"""
Financial Research Bot Web Application

This script runs the Financial Research Bot as a web application using FastAPI.
It provides a web interface for users to input financial research queries and
view the results in real-time.

Usage:
    python -m examples.financial_research_agent.web_app
"""

import os
import sys
import uvicorn

from examples.financial_research_agent.api import app

if __name__ == "__main__":
    # Check if OPENAI_API_KEY is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Please set it before running the application:")
        print("\nOn Linux/Mac:")
        print("export OPENAI_API_KEY=your_api_key_here")
        print("\nOn Windows:")
        print("set OPENAI_API_KEY=your_api_key_here")
        print("\nOr run with:")
        print("OPENAI_API_KEY=your_api_key_here python -m examples.financial_research_agent.web_app")
        sys.exit(1)
    
    print("Starting Financial Research Bot Web Application...")
    print("Open your browser and navigate to http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
