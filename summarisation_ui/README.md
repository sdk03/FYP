# Summarization UI: LLM-Powered Chat Interpretation

This folder contains a web-based UI for summarizing and inspecting forensic chat logs. Chat data extracted from Android phone images is processed via an LLM and displayed in a searchable, interactive format.

## Features
- Displays summaries grouped by conversation ID
- Allows investigators to inspect original messages alongside AI summaries
- Built-in feedback loop to refine low-scoring summaries (G-Eval < 90%)

## Technologies
- Flask (backend)
- HTML, CSS, JS (frontend)
- Ollama for local model inference

## How to Run
1. Extract chat logs using ALEAPP and save as `.csv`.
2. Start the Flask app using `flask run`.
3. Visit `http://localhost:5000` in a browser to access the UI.
