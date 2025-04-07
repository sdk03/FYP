# --- Imports: loading data, HTTP requests, and timestamping ---
import pickle
import requests as rq
import datetime

# --- API and model configuration ---
API_URL = "http://192.168.88.234:11434/api/generate"
API_KEY = ""

# --- Load pre-processed clustered message data ---
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type":"application/json"
}

# --- Prompt template for LLM input ---
MODEL = "gemma2:9b"
RESPONSE_FILE = "../llm-response.txt"

all_responses = []
llm_response_file = '../llm-response.pkl'

# ---------------------------------------

cleaned_file = '../cleaned_data.pkl'


with open(cleaned_file, 'rb') as c_file:
    clustered_data = pickle.load(c_file)

print("[DEBUG]: LOADED CLEANED DATA\n")
print("[DEBUG]: \n", clustered_data[1:2])

# ----------------------------------------
PROMPT_TEMPLATE = """
Analyse the following messages grouped into a time window from {start} to {end}. 
Tasks:
1. **Summarise Key Events**: What is the main theme or activity in this window?
Messages:
{messages}

Respond in JSON fromat.
"""
# --- Begin generation and logging loop ---
with open(RESPONSE_FILE, 'a', encoding='utf-8') as file:

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file.write(f"\n\n+----------------------------------------+\n")
    file.write(f"[INFO]: Run Timestamp: {timestamp}\n")

    for i, cluster in enumerate(clustered_data):
      
        context_messages = cluster["messages"]
        context_str = "\n".join([f"{msg['Date/Time']}: {msg['From Phone Number']}: {msg['Text']}"
                             for msg in context_messages])

        prompt = PROMPT_TEMPLATE.format(
            start=cluster["window_start"],
            end=cluster["window_end"],
            messages = context_str
        )

        print(f"[DEBUG]: PROMPT {i} \n")
        print("[DEBUG]: \n", prompt)

        file.write(f"[DEBUG]: PROMPT {i} \n")
        file.write(f"[DEBUG]: \n {prompt}")

        DATA = {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": {
                "type": "object",
                "properties": {
                "window_summary": {
                    "type": "string"
                },
                },
                "required": [
                "window_summary"
                ]
            }
        }

        # --- Send prompt to LLM API and handle the response ---
        response = rq.post(API_URL, json=DATA, headers=HEADERS)

        if response.status_code == 200:
            response_data = response.json()
            print(f"[DEBUG]: RESPONSE {i} \n")
            print(f"[DEBUG]: \n{response_data['response']}\n")

            all_responses.append({
                "window_start": cluster["window_start"],
                "window_end": cluster["window_end"],
                "response": response_data['response']
            })

            with open(llm_response_file, 'wb') as pkl_file:
                pickle.dump(all_responses, pkl_file)

            file.write(f"[DEBUG]: RESPONSE {i} \n")
            file.write(f"[DEBUG]: \n{response_data['response']}\n")
            file.flush()

        else:
            print(f"[ERROR]: RESPONSE {i} \n")
            print(f"[DEBUG]: \n{response.text}\n")

            file.write(f"[ERROR]: RESPONSE {i} \n")
            file.write(f"[DEBUG]: \n{response.text}\n")
            file.flush()

    



