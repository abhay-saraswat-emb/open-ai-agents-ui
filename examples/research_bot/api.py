from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents import Runner, custom_span, gen_trace_id, trace

from examples.research_bot.agents.planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from examples.research_bot.agents.search_agent import search_agent
from examples.research_bot.agents.writer_agent import ReportData, writer_agent

app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"]   # Allow all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="examples/research_bot/static"), name="static")

# Queue to store research updates
research_updates = {}


class ResearchRequest(BaseModel):
    query: str


class ResearchUpdate(BaseModel):
    id: str
    type: str
    content: str
    is_done: bool = False


class ResearchManager:
    def __init__(self, research_id: str):
        self.research_id = research_id
        self.updates_queue = []

    def add_update(self, update_type: str, content: str, is_done: bool = False):
        update = ResearchUpdate(
            id=str(uuid.uuid4()),
            type=update_type,
            content=content,
            is_done=is_done
        )
        self.updates_queue.append(update)
        research_updates[self.research_id].append(update.dict())

    async def run(self, query: str) -> None:
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            self.add_update(
                "trace_id",
                f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}",
                is_done=True,
            )

            self.add_update(
                "starting",
                "Starting research...",
                is_done=True,
            )
            search_plan = await self._plan_searches(query)
            search_results = await self._perform_searches(search_plan)
            report = await self._write_report(query, search_results)

            final_report = f"Report summary\n\n{report.short_summary}"
            self.add_update("final_report", final_report, is_done=True)

            # Add the full report
            self.add_update("full_report", report.markdown_report, is_done=True)
            
            # Add follow-up questions
            follow_up_questions = "\n".join(report.follow_up_questions)
            self.add_update("follow_up_questions", follow_up_questions, is_done=True)

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        self.add_update("planning", "Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        self.add_update(
            "planning",
            f"Will perform {len(result.final_output.searches)} searches",
            is_done=True,
        )
        return result.final_output_as(WebSearchPlan)

    async def _perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        with custom_span("Search the web"):
            self.add_update("searching", "Searching...")
            num_completed = 0
            tasks = [asyncio.create_task(self._search(item)) for item in search_plan.searches]
            results = []
            for task in asyncio.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
                self.add_update(
                    "searching", f"Searching... {num_completed}/{len(tasks)} completed"
                )
            self.add_update("searching", "Search completed", is_done=True)
            return results

    async def _search(self, item: WebSearchItem) -> str | None:
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
        self.add_update("writing", "Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = Runner.run_streamed(
            writer_agent,
            input,
        )
        update_messages = [
            "Thinking about report...",
            "Planning report structure...",
            "Writing outline...",
            "Creating sections...",
            "Cleaning up formatting...",
            "Finalizing report...",
            "Finishing report...",
        ]

        last_update = time.time()
        next_message = 0
        async for _ in result.stream_events():
            if time.time() - last_update > 5 and next_message < len(update_messages):
                self.add_update("writing", update_messages[next_message])
                next_message += 1
                last_update = time.time()

        self.add_update("writing", "Report completed", is_done=True)
        return result.final_output_as(ReportData)


@app.post("/research")
async def start_research(request: ResearchRequest):
    research_id = str(uuid.uuid4())
    research_updates[research_id] = []
    
    # Start research in background task
    manager = ResearchManager(research_id)
    asyncio.create_task(manager.run(request.query))
    
    return {"research_id": research_id}


@app.get("/research/{research_id}/updates")
async def get_research_updates(research_id: str, request: Request):
    async def event_generator():
        if research_id not in research_updates:
            yield f"data: {json.dumps({'error': 'Research ID not found'})}\n\n"
            return

        # Send all existing updates
        for update in research_updates[research_id]:
            yield f"data: {json.dumps(update)}\n\n"
        
        # Keep connection open for new updates
        last_idx = len(research_updates[research_id])
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Check for new updates
            if len(research_updates[research_id]) > last_idx:
                for update in research_updates[research_id][last_idx:]:
                    yield f"data: {json.dumps(update)}\n\n"
                last_idx = len(research_updates[research_id])
            
            # Wait a bit before checking again
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse("examples/research_bot/static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
