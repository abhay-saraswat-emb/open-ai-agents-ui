import asyncio
import os
import sys

from examples.financial_research_agent.manager import FinancialResearchManager


# Entrypoint for the financial bot example.
# Run this as `python -m examples.financial_research_agent.main` and enter a
# financial research query, for example:
# "Write up an analysis of Apple Inc.'s most recent quarter."
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
        print("OPENAI_API_KEY=your_api_key_here python -m examples.financial_research_agent.main")
        sys.exit(1)
        
    query = input("Enter a financial research query: ")
    mgr = FinancialResearchManager()
    await mgr.run(query)


if __name__ == "__main__":
    asyncio.run(main())
