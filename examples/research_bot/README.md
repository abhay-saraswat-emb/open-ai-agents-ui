# Research Bot

This is a multi-agent research bot that can research any topic and generate a comprehensive report. It can be run in two modes:

## Command Line Interface

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
python -m examples.research_bot.main
```

You can also run the application in a single command:

```bash
OPENAI_API_KEY=your_api_key_here python -m examples.research_bot.main
```

## Web Application

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
python -m examples.research_bot.web_app
```

3. Open your browser and navigate to http://localhost:8000

You can also run the application in a single command:

```bash
OPENAI_API_KEY=your_api_key_here python -m examples.research_bot.web_app
```

## Architecture

The flow is:

1. User enters their research topic
2. `planner_agent` comes up with a plan to search the web for information. The plan is a list of search queries, with a search term and a reason for each query.
3. For each search item, we run a `search_agent`, which uses the Web Search tool to search for that term and summarize the results. These all run in parallel.
4. Finally, the `writer_agent` receives the search summaries, and creates a written report.

## Suggested improvements

If you're building your own research bot, some ideas to add to this are:

1. Retrieval: Add support for fetching relevant information from a vector store. You could use the File Search tool for this.
2. Image and file upload: Allow users to attach PDFs or other files, as baseline context for the research.
3. More planning and thinking: Models often produce better results given more time to think. Improve the planning process to come up with a better plan, and add an evaluation step so that the model can choose to improve its results, search for more stuff, etc.
4. Code execution: Allow running code, which is useful for data analysis.
5. Save reports: Add functionality to save generated reports to files or a database.
6. User accounts: Add user authentication to save research history and preferences.
