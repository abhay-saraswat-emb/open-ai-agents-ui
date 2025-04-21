"""
Customer Service Web Application

This script runs the Customer Service Bot as a web application using FastAPI.
It provides a web interface for users to interact with the airline customer service agents.

Usage:
    python -m examples.customer_service.web_app
"""

import os
import sys
import uvicorn

from examples.customer_service.api import app

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
        print("OPENAI_API_KEY=your_api_key_here python -m examples.customer_service.web_app")
        sys.exit(1)
    
    print("Starting Customer Service Web Application...")
    print("Open your browser and navigate to http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
