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

## convo_llm.py
Since the server uses a stored CSV response file, the LLM processing is done via another python file called convo_llm.py

This script automates the summarization of chat or SMS conversation threads using a locally hosted Large Language Model (LLM) via Ollama and evaluates the generated summaries using the G-Eval metric from the `deepeval` library.

---

## 🔧 Features

- **Data Loading & Preprocessing**  
  Loads conversation data from a CSV file and converts timestamps into standardized format.

- **Prompt Construction**  
  Dynamically builds prompts per conversation in a human-readable format to guide LLM summarization.

- **LLM Integration (Ollama)**  
  Sends prompts to a locally deployed LLM (e.g., `gemma2:9b`) through the Ollama HTTP API.

- **Structured JSON Handling**  
  Parses and extracts the `summary` field from the API’s structured JSON response.

- **Evaluation with G-Eval**  
  Evaluates the summary’s correctness by checking:
  1. Key points are captured.
  2. No important info is missing.
  3. No incorrect details are introduced.

- **Error Handling & Reattempts**  
  Automatically retries with prompt refinement if the evaluation score is below threshold.

- **Logging & Persistence**  
  Logs each step and outcome to `program_log_with_a12.txt`, and appends results to `ollama_responses_with_evaluation_a12.csv`.

---

## 📁 File Structure

| File | Description |
|------|-------------|
| `output_conversations_a12.csv` | Input CSV containing grouped messages with metadata. |
| `ollama_responses_with_evaluation_a12.csv` | Output CSV with summaries, evaluation scores, and reasons. |
| `program_log_with_a12.txt` | Detailed execution log and error trace. |

---

