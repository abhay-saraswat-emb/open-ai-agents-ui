import asyncio
import os
import sys

from examples.research_bot.manager import ResearchManager


async def main() -> None:
    # Check if OPENAI_API_KEY is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Please set it before running the application:")
        print("\nOn Linux/Mac:")
        print("export OPENAI_API_KEY=your_api_key_here")
        print("\nOn Windows:")
        print("set OPENAI_API_KEY=your_api_key_here")
        print("\nOr run with:")
        print("OPENAI_API_KEY=your_api_key_here python -m examples.research_bot.main")
        sys.exit(1)
        
    query = input("What would you like to research? ")
    await ResearchManager().run(query)


if __name__ == "__main__":
    asyncio.run(main())
