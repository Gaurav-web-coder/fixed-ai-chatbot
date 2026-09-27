import os
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import streamlit as st
from gemini_client import GEMINI_MODEL, GeminiError, generate_response

st.set_page_config(page_title="Generative Music Chatbot", page_icon="🎹")


def get_api_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except (FileNotFoundError, KeyError):
        key = ""
    if not key:
        path = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
        if path.exists():
            with path.open("rb") as file:
                key = tomllib.load(file).get("GEMINI_API_KEY", "")
    return str(key).strip()


st.title("🎹 Generative Music Assistant")
st.caption("Powered by Gemini. Ask about music, Punjabi culture, production, or anything else.")
try:
    api_key = get_api_key()
except Exception:
    st.error('Cannot read API settings. Use GEMINI_API_KEY = "your-key" in .streamlit/secrets.toml.')
    st.stop()

if "gemini_messages" not in st.session_state:
    st.session_state.gemini_messages = []

with st.sidebar:
    st.subheader("Status")
    if api_key:
        st.info("API key configured. Sending a message tests the connection.")
    else:
        st.error("Gemini API key missing")
        st.code('GEMINI_API_KEY = "your-key"', language="toml")
        st.caption("Add this to .streamlit/secrets.toml in your project folder.")
    model = st.text_input("Gemini model", value=GEMINI_MODEL).strip() or GEMINI_MODEL
    if st.button("New chat"):
        st.session_state.gemini_messages = []
        st.rerun()

if not st.session_state.gemini_messages:
    with st.chat_message("assistant"):
        st.markdown("What's up! Let's talk music. What are you working on today?")

for item in st.session_state.gemini_messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

if prompt := st.chat_input("Ask about music, Punjabi vibes, or production ideas...", disabled=not api_key):
    if not prompt.strip():
        st.stop()
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                answer = generate_response(
                    prompt,
                    api_key=api_key,
                    conversation_history=st.session_state.gemini_messages,
                    model=model,
                )
        except GeminiError as exc:
            st.error("Gemini could not answer. See the error details below.")
            st.code(str(exc), language=None)
            st.caption("Your previous conversation is preserved. Send your question again after resolving the error.")
        else:
            st.markdown(answer)
            st.session_state.gemini_messages.extend([
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer},
            ])
