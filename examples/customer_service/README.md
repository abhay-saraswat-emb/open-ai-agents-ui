# Customer Service Bot with Web UI

This example demonstrates a multi-agent customer service system for an airline with a web-based user interface. It showcases how to use handoffs between different specialized agents to provide a comprehensive customer service experience.

## Agents

The system consists of three specialized agents:

1. **Triage Agent**: The main agent that delegates questions to other specialized agents based on the customer's needs.
2. **FAQ Agent**: Answers frequently asked questions about the airline (baggage policy, seating, wifi, etc.).
3. **Seat Booking Agent**: Helps customers update their seat on a flight.

## Features

- Agent handoffs based on customer needs
- Context tracking (passenger name, confirmation number, seat number, flight number)
- Tool usage for FAQ lookup and seat updates
- Web interface with real-time updates
- Visual indication of agent changes
- Responsive design for desktop and mobile

## Running the Web Application

To run the customer service bot with the web UI:

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

### Name Detection

- "My name is John Smith" (this will automatically update the passenger name in the context panel)

## Architecture

The web application is built using:

- **Backend**: FastAPI server with endpoints for conversation management and Server-Sent Events for real-time updates
- **Frontend**: Responsive UI with vanilla JavaScript, HTML, and CSS
- **Real-time Communication**: EventSource API for receiving updates from the server
- **Multi-agent System**: Agents SDK for creating specialized agents with handoffs

## Troubleshooting

If you encounter any issues:

1. Check the browser console (F12 or right-click > Inspect > Console) for detailed logs
2. Ensure your OpenAI API key is set correctly
3. Make sure no other application is running on port 8000
