# Deep Research Streamlit Sample

This sample demonstrates how to perform an automated deep research process using the Tavily API for web search and OpenAI's Chat API for reasoning and summarization, all wrapped in a Streamlit interface.

## Prerequisites

* **Tavily API key** (set as `TAVILY_API_KEY`)
* **OpenAI API key** (set as `OPENAI_API_KEY`)

## .env Configuration

Create a file named `.env` in the project root with the following contents:

```dotenv
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

## Conda Virtual Environment Setup

```bash
# Create and activate a new environment
conda create -n deepresearch python=3.10 -y
conda activate deepresearch

# Install required packages
pip install streamlit openai python-dotenv tavily-python
```

## Running the App

```bash
streamlit run app.py
```
