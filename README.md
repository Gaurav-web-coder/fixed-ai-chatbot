# Gemini-only Music Chatbot

## Run on Windows
1. Stop the previous Streamlit process with Ctrl+C.
2. Extract this ZIP into a NEW folder and open the extracted `ai chatbot` folder in VS Code.
3. In the VS Code terminal, run:

   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -U -r requirements.txt
   .\.venv\Scripts\python.exe -m streamlit run app.py

4. Open the Local URL printed in the terminal and send `Hello`.

The original .streamlit/secrets.toml is preserved. If needed, set:

    GEMINI_API_KEY = "your-key"

An environment variable named GEMINI_API_KEY takes precedence over that file.
Keep your API key private.

## Changes
- app.py calls gemini_client.py for every question.
- Removed chat.py, train.py, intents.json and chatbot_model.h5 from this distribution.
- No TensorFlow, NLTK, local model, intent classifier or local fallback.
- Keeps the original music production system instruction.
- Keeps the documented model ID gemini-3.8-flash; the sidebar lets you change it.
- Shows API error codes and details, with the API key redacted.
- Says API key configured rather than claiming the connection has been tested.
- Stores only successful conversation turns; sends each new question once.
- Adds a New chat button.
- The package excludes the old virtual environment, Git metadata and Python caches.

## If Gemini still rejects the request
The previous screenshot hides the real cause. Removing local files cannot fix a
Gemini account, network, or quota problem. The new error panel exposes the cause:
- 400/401: inspect the error and check the key/request settings.
- 403: check API key restrictions and project permissions.
- 404: check the model ID and access for your project.
- 429: check quota/rate limits in Google AI Studio.
- 500/503: temporary service issue; retry later.
- Connection/timeout error: check internet, firewall or proxy settings.

Copy the new error text for further diagnosis; do not share the API key.

## Verification
Python syntax checks and 5 unittest tests passed with simulated Gemini responses.
A live Gemini request and the Streamlit UI were not run in the editing environment.
Run tests with: python -m unittest test_chatbot_flow.py -v

References:
https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
https://googleapis.github.io/python-genai/
https://ai.google.dev/gemini-api/docs/troubleshooting
