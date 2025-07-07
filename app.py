import os
import json
import re
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
from tavily import TavilyClient

# Load environment variables
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
tavily_api_key = os.getenv("TAVILY_API_KEY")

# Prompts for the research workflow
QUERY_PROMPT = '''Your goal is to generate a targeted web search query.
Current date: {date}
Topic: {topic}
Format your response as JSON with keys `query` and `rationale`.
Example: {"query": "machine learning transformer architecture", "rationale": "Understand transformer basics"}'''

SUMMARIZE_PROMPT = '''Generate a concise summary of the context below:
Context:
{context}
Topic: {topic}
If `existing_summary` is provided, integrate new information; otherwise create a new summary.'''

REFLECT_PROMPT = '''You are an expert research assistant analyzing a summary about {topic}.
1. Identify what information is missing (knowledge_gap).
2. Propose a follow-up web search query (follow_up_query).
Respond as JSON with `knowledge_gap` and `follow_up_query`.'''

# Utility functions
def generate_query(topic: str, date: str):
    # Separate system and user messages
    messages = [
        {"role": "system", "content":
            "You are a research assistant. "
            "Given a date and a topic, output ONLY a JSON object "
            "with keys `query` and `rationale`. No extra text or markdown."},
        {"role": "user", "content": f"Current date: {date}\nTopic: {topic}"}
    ]

    # Use temperature=0 for deterministic and stable output
    resp = client.chat.completions.create(
        model="gpt-4.1-mini-2025-04-14",
        messages=messages,
        temperature=0
    )
    raw = resp.choices[0].message.content.strip()

    # Extract and parse only the JSON portion
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        st.error(f"❗️Could not find JSON in the response:\n{raw}")
        return "", ""

    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        st.error(f"❗️Failed to parse JSON ({e}):\n{raw}")
        return "", ""

    # Check for required key
    if 'query' not in data:
        st.error(f"❗️Missing `query` key: {data}")
        return "", data.get('rationale', '')

    return data['query'], data.get('rationale', '')


def summarize(existing_summary: str, context: str, topic: str):
    prompt = SUMMARIZE_PROMPT.format(context=context, topic=topic)
    messages = []
    if existing_summary:
        messages.append({"role": "system", "content": prompt + f"\nExisting summary:\n{existing_summary}"})
    else:
        messages.append({"role": "system", "content": prompt})
    response = client.chat.completions.create(
        model="gpt-4.1-mini-2025-04-14",
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def reflect(summary: str, topic: str):
    response = client.chat.completions.create(
        model="gpt-4.1-mini-2025-04-14",
        messages=[
            {"role": "system", "content": REFLECT_PROMPT.format(topic=topic)},
            {"role": "user", "content": summary}
        ]
    )
    data = json.loads(response.choices[0].message.content)
    return data.get('follow_up_query', ''), data.get('knowledge_gap', '')


def deep_research(topic: str, cycles: int = 3):
    client = TavilyClient(api_key=tavily_api_key)
    summary = ""
    all_sources = []
    all_images = []
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")

    query, _ = generate_query(topic, current_date)
    for i in range(cycles):
        # Web search
        results = client.search(query, max_results=1)
        sources = [r['url'] for r in results.get('results', [])]
        images = results.get('images', [])
        all_sources.extend(sources)
        all_images.extend(images)

        # Build context
        context = results['results'][0].get('content', '') if sources else ''

        # Summarize
        summary = summarize(summary, context, topic)

        # Reflect for next query
        query, _ = reflect(summary, topic)
        if not query:
            break

    return summary, all_sources, all_images

# Streamlit app
st.title("Deep Research with Tavily & OpenAI")
topic = st.text_input("Enter research topic:")
cycles = st.slider("Number of research cycles:", 1, 5, 3)

if st.button("Start Research"):
    if not topic:
        st.warning("Please enter a research topic.")
    else:
        with st.spinner("Conducting deep research..."):
            summary, sources, images = deep_research(topic, cycles)
        st.subheader("Summary")
        st.write(summary)
        st.subheader("Sources")
        for url in sources:
            st.write(f"- {url}")
        if images:
            st.subheader("Images")
            st.image(images)
