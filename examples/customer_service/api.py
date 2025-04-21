from __future__ import annotations

import asyncio
import json
import random
import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents import (
    Agent,
    HandoffOutputItem,
    ItemHelpers,
    MessageOutputItem,
    RunContextWrapper,
    Runner,
    ToolCallItem,
    ToolCallOutputItem,
    TResponseInputItem,
    function_tool,
    handoff,
    trace,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="examples/customer_service/static"), name="static")

# Store active conversations
active_conversations: Dict[str, Dict] = {}


### CONTEXT


class AirlineAgentContext(BaseModel):
    passenger_name: str | None = None
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None


### TOOLS


@function_tool(
    name_override="faq_lookup_tool", description_override="Lookup frequently asked questions."
)
async def faq_lookup_tool(question: str) -> str:
    if "bag" in question or "baggage" in question:
        return (
            "You are allowed to bring one bag on the plane. "
            "It must be under 50 pounds and 22 inches x 14 inches x 9 inches."
        )
    elif "seats" in question or "plane" in question:
        return (
            "There are 120 seats on the plane. "
            "There are 22 business class seats and 98 economy seats. "
            "Exit rows are rows 4 and 16. "
            "Rows 5-8 are Economy Plus, with extra legroom. "
        )
    elif "wifi" in question:
        return "We have free wifi on the plane, join Airline-Wifi"
    return "I'm sorry, I don't know the answer to that question."


@function_tool
async def update_seat(
    context: RunContextWrapper[AirlineAgentContext], confirmation_number: str, new_seat: str
) -> str:
    """
    Update the seat for a given confirmation number.

    Args:
        confirmation_number: The confirmation number for the flight.
        new_seat: The new seat to update to.
    """
    # Update the context based on the customer's input
    context.context.confirmation_number = confirmation_number
    context.context.seat_number = new_seat
    # Ensure that the flight number has been set by the incoming handoff
    assert context.context.flight_number is not None, "Flight number is required"
    return f"Updated seat to {new_seat} for confirmation number {confirmation_number}"


### HOOKS


async def on_seat_booking_handoff(context: RunContextWrapper[AirlineAgentContext]) -> None:
    flight_number = f"FLT-{random.randint(100, 999)}"
    context.context.flight_number = flight_number


### AGENTS

faq_agent = Agent[AirlineAgentContext](
    name="FAQ Agent",
    handoff_description="A helpful agent that can answer questions about the airline.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are an FAQ agent. If you are speaking to a customer, you probably were transferred to from the triage agent.
    Use the following routine to support the customer.
    # Routine
    1. Identify the last question asked by the customer.
    2. Use the faq lookup tool to answer the question. Do not rely on your own knowledge.
    3. If you cannot answer the question, transfer back to the triage agent.""",
    tools=[faq_lookup_tool],
)

seat_booking_agent = Agent[AirlineAgentContext](
    name="Seat Booking Agent",
    handoff_description="A helpful agent that can update a seat on a flight.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a seat booking agent. If you are speaking to a customer, you probably were transferred to from the triage agent.
    Use the following routine to support the customer.
    # Routine
    1. Ask for their confirmation number.
    2. Ask the customer what their desired seat number is.
    3. Use the update seat tool to update the seat on the flight.
    If the customer asks a question that is not related to the routine, transfer back to the triage agent. """,
    tools=[update_seat],
)

triage_agent = Agent[AirlineAgentContext](
    name="Triage Agent",
    handoff_description="A triage agent that can delegate a customer's request to the appropriate agent.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful triaging agent. You can use your tools to delegate questions to other appropriate agents."
    ),
    handoffs=[
        faq_agent,
        handoff(agent=seat_booking_agent, on_handoff=on_seat_booking_handoff),
    ],
)

faq_agent.handoffs.append(triage_agent)
seat_booking_agent.handoffs.append(triage_agent)


### API MODELS

class Message(BaseModel):
    id: str = ""  # Add an ID field with a default empty string
    role: str
    content: str
    agent_name: Optional[str] = None
    type: Optional[str] = None


class ConversationRequest(BaseModel):
    message: str


class ConversationResponse(BaseModel):
    conversation_id: str
    messages: List[Message]


### API ROUTES

@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse("examples/customer_service/static/index.html")


@app.post("/conversation")
async def start_conversation():
    conversation_id = uuid.uuid4().hex[:16]
    active_conversations[conversation_id] = {
        "current_agent": triage_agent,
        "input_items": [],
        "context": AirlineAgentContext(),
        "messages": []
    }
    return {"conversation_id": conversation_id}


@app.post("/conversation/{conversation_id}/message")
async def send_message(conversation_id: str, request: ConversationRequest):
    if conversation_id not in active_conversations:
        return {"error": "Conversation not found"}
    
    conversation = active_conversations[conversation_id]
    current_agent = conversation["current_agent"]
    input_items = conversation["input_items"]
    context = conversation["context"]
    
    # Add user message to conversation
    user_message = Message(id=str(uuid.uuid4()), role="user", content=request.message)
    conversation["messages"].append(user_message)
    
    # Try to extract passenger name from the message
    if context.passenger_name is None:
        # Simple name extraction - look for common name patterns
        name_patterns = [
            r"my name is ([A-Z][a-z]+ [A-Z][a-z]+)",
            r"name is ([A-Z][a-z]+ [A-Z][a-z]+)",
            r"I am ([A-Z][a-z]+ [A-Z][a-z]+)",
            r"I'm ([A-Z][a-z]+ [A-Z][a-z]+)",
            r"this is ([A-Z][a-z]+ [A-Z][a-z]+)"
        ]
        
        for pattern in name_patterns:
            import re
            match = re.search(pattern, request.message)
            if match:
                context.passenger_name = match.group(1)
                break
    
    # Process message with agent
    with trace("Customer service", group_id=conversation_id):
        input_items.append({"content": request.message, "role": "user"})
        result = await Runner.run(current_agent, input_items, context=context)
        
        for new_item in result.new_items:
            agent_name = new_item.agent.name
            if isinstance(new_item, MessageOutputItem):
                message_content = ItemHelpers.text_message_output(new_item)
                conversation["messages"].append(
                    Message(
                        id=str(uuid.uuid4()),
                        role="assistant", 
                        content=message_content, 
                        agent_name=agent_name, 
                        type="message"
                    )
                )
            elif isinstance(new_item, HandoffOutputItem):
                handoff_message = f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}"
                conversation["messages"].append(
                    Message(
                        id=str(uuid.uuid4()),
                        role="system", 
                        content=handoff_message, 
                        type="handoff"
                    )
                )
            elif isinstance(new_item, ToolCallItem):
                # Access the function name from the tool call
                function_name = new_item.function.name if hasattr(new_item, 'function') else "unknown tool"
                tool_call_message = f"Calling tool: {function_name}"
                conversation["messages"].append(
                    Message(
                        id=str(uuid.uuid4()),
                        role="system", 
                        content=tool_call_message, 
                        agent_name=agent_name, 
                        type="tool_call"
                    )
                )
            elif isinstance(new_item, ToolCallOutputItem):
                tool_output_message = f"Tool result: {new_item.output}"
                conversation["messages"].append(
                    Message(
                        id=str(uuid.uuid4()),
                        role="system", 
                        content=tool_output_message, 
                        agent_name=agent_name, 
                        type="tool_output"
                    )
                )
        
        # Update conversation state
        conversation["input_items"] = result.to_input_list()
        conversation["current_agent"] = result.last_agent
    
    return {"conversation_id": conversation_id, "messages": conversation["messages"]}


@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in active_conversations:
        return {"error": "Conversation not found"}
    
    return {
        "conversation_id": conversation_id,
        "messages": active_conversations[conversation_id]["messages"],
        "context": active_conversations[conversation_id]["context"]
    }


@app.get("/conversation/{conversation_id}/stream")
async def stream_conversation(conversation_id: str, request: Request):
    async def event_generator():
        if conversation_id not in active_conversations:
            yield f"data: {json.dumps({'error': 'Conversation not found'})}\n\n"
            return
        
        # Send all existing messages
        for message in active_conversations[conversation_id]["messages"]:
            message_dict = message.dict()
            print(f"Sending message via SSE: {message_dict}")
            yield f"data: {json.dumps(message_dict)}\n\n"
        
        # Keep track of the last message index
        last_idx = len(active_conversations[conversation_id]["messages"])
        
        # Keep connection open for new messages
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                print(f"Client disconnected from SSE for conversation {conversation_id}")
                break
            
            # Check for new messages
            if conversation_id in active_conversations:
                current_messages = active_conversations[conversation_id]["messages"]
                if len(current_messages) > last_idx:
                    print(f"New messages available: {len(current_messages) - last_idx}")
                    for message in current_messages[last_idx:]:
                        message_dict = message.dict()
                        print(f"Sending new message via SSE: {message_dict}")
                        yield f"data: {json.dumps(message_dict)}\n\n"
                    last_idx = len(current_messages)
            
            # Wait a bit before checking again
            await asyncio.sleep(0.5)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
