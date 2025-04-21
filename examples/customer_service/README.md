# Customer Service Bot Example

This example demonstrates a multi-agent customer service system for an airline. It showcases how to use handoffs between different specialized agents to provide a comprehensive customer service experience.

## Agents

The system consists of three specialized agents:

1. **Triage Agent**: The main agent that delegates questions to other specialized agents based on the customer's needs.
2. **FAQ Agent**: Answers frequently asked questions about the airline (baggage policy, seating, wifi, etc.).
3. **Seat Booking Agent**: Helps customers update their seat on a flight.

## Features

- Agent handoffs based on customer needs
- Context tracking (passenger name, confirmation number, seat number, flight number)
- Tool usage for FAQ lookup and seat updates
- Web interface for easy interaction

## Running the Example

You can run the example in two modes:

### Command Line Interface

To run the bot in the command line:

1. Set your OpenAI API key as an environment variable:

```bash
# On Linux/Mac
export OPENAI_API_KEY=your_api_key_here

# On Windows
set OPENAI_API_KEY=your_api_key_here
```

2. Run the command line interface:

```bash
python -m examples.customer_service.main
```

You can also run the application in a single command:

```bash
OPENAI_API_KEY=your_api_key_here python -m examples.customer_service.main
```

### Web Application

To run the bot as a web application with a user-friendly interface:

1. Set your OpenAI API key as an environment variable:

```bash
# On Linux/Mac
export OPENAI_API_KEY=your_api_key_here

# On Windows
set OPENAI_API_KEY=your_api_key_here
```

2. Run the web application:

```bash
python -m examples.customer_service.web_app
```

3. Open your browser and navigate to http://localhost:8000

You can also run the application in a single command:

```bash
OPENAI_API_KEY=your_api_key_here python -m examples.customer_service.web_app
```

## Example Interactions

Here are some example interactions you can try:

### FAQ Questions

- "What is your baggage policy?"
- "How many seats are on the plane?"
- "Do you have wifi on the flight?"

### Seat Booking

- "I want to change my seat"
- When asked for confirmation number, provide any alphanumeric string (e.g., "ABC123")
- When asked for desired seat, provide any seat number (e.g., "12A")

## Architecture

The system uses the Agents SDK to create a multi-agent system with handoffs. The web application is built using FastAPI for the backend and vanilla JavaScript for the frontend, with Server-Sent Events (SSE) for real-time updates.

### Backend

- FastAPI server with endpoints for conversation management
- Server-Sent Events for real-time updates
- Context tracking for customer information

### Frontend

- Responsive UI with chat interface
- Real-time updates using EventSource API
- Context panel showing customer information
- Agent tracking to show which agent is currently active
