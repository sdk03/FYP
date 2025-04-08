# Autopsy Plugin: SMS Categorization Using LLMs

This folder contains the source code and documentation for the Autopsy plugin developed as part of the MSc project. The plugin enables automated categorization of SMS messages using Large Language Models (LLMs), integrated with the Autopsy forensic tool via a local Flask-LLM setup.

## Features
- Extracts SMS from `mmssms.db` (Android)
- Sends extracted messages to a local LLM via Flask API
- Receives categorization results and integrates them as blackboard artifacts in Autopsy

## Technologies
- Java (Autopsy plugin)
- Python (Flask server + Ollama)
- Jython (for cross-language execution)

## How to Run
1. Install Autopsy.
2. Place the plugin files in the Autopsy `PythonPlugins` folder.
3. Start the Flask server using `flask run`.
4. Load a case with `mmssms.db` and run the plugin.

## Notes
- Works with Ollama models (e.g., Gemma, LLaMA).
