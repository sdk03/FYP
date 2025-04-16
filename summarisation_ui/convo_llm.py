import pandas as pd
import json
import requests
from tabulate import tabulate
import logging
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

# -------------------------
# 1. Configure Logging
# -------------------------
log_file = "program_log_with_a12.txt"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Log the start of the program
logging.info("Program started.")

# -------------------------
# 2. Load and Prepare Data
# -------------------------
input_csv_path = "../data_group/output_conversations_a12.csv"
try:
    df = pd.read_csv(input_csv_path)
    df['Date/Time'] = pd.to_datetime(df['Date/Time'], utc=True)
    logging.info(f"Successfully loaded {len(df)} rows from {input_csv_path}")
except Exception as e:
    logging.error(f"Error loading input CSV: {e}")
    raise

# --------------------------------------------
# 3. Function to Build the Prompt for LLM
# --------------------------------------------
def build_prompt(convo_id, messages_df):
    """
    Constructs a prompt for the LLM to generate a conversation summary.
    
    For each message, the format is:
      "[Date/Time] - [Source Name] ([Message Type]): [Text]"
    """
    prompt_lines = []
    prompt_lines.append("Please generate a concise summary of the conversation below.")
    prompt_lines.append(f"Conversation ID: {convo_id}")
    prompt_lines.append("Messages:")
    
    for _, row in messages_df.iterrows():
        dt_str = row['Date/Time'].strftime('%Y-%m-%d %H:%M:%S')
        source_name = row['Source Name']
        line = f"{dt_str} - ({row['Message Type']}): {row['Text']}"
        prompt_lines.append(line)
    
    return "\n".join(prompt_lines)

# --------------------------------------------
# 4. Define Ollama API Details and Payload Schema
# --------------------------------------------
ollama_url = "http://192.168.88.234:11434/api/generate"

# The payload now only expects the "summary" field in the response.
payload_schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"}
    },
    "required": ["summary"]
}

# --------------------------------------------
# 5. Define G-Eval Metric for Evaluation
# --------------------------------------------
def create_geval_metric():
    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine whether the summary accurately reflects the conversation messages.",
        evaluation_steps=[
            "Check if the summary captures the key points of the conversation.",
            "Ensure no important details are omitted from the summary.",
            "Verify that the summary does not introduce any incorrect information."
        ],
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT
        ],
        verbose_mode=True
    )
    return correctness_metric

# --------------------------------------------
# 6. Process Each Conversation, Send Request, & Collect Responses
# --------------------------------------------
output_csv_path = 'ollama_responses_with_evaluation_a12.csv'

# Initialize an empty DataFrame to store responses
try:
    # Try to load existing CSV file if it exists
    responses_df = pd.read_csv(output_csv_path)
    logging.info(f"Loaded existing responses from {output_csv_path}.")
except FileNotFoundError:
    # If the file doesn't exist, create an empty DataFrame
    responses_df = pd.DataFrame(columns=["Conversation_ID", "summary", "evaluation_score", "evaluation_reason"])
    logging.info(f"No existing responses found. Starting fresh.")

geval_metric = create_geval_metric()

for convo_id, group in df.groupby("Conversation_ID"):
    # Skip conversations already processed
    if convo_id in responses_df["Conversation_ID"].values:
        logging.info(f"Skipping already processed Conversation ID {convo_id}.")
        continue

    messages = "\n".join(group.apply(
        lambda row: f"{row['Date/Time'].strftime('%Y-%m-%d %H:%M:%S')} - {row['Source Name']} ({row['Message Type']}): {row['Text']}",
        axis=1
    ))
    
    attempt = 1
    while True:
        logging.info(f"Processing Conversation ID {convo_id}, Attempt {attempt}")
        
        # Build the prompt
        prompt = build_prompt(convo_id, group)
        
        # Send request to Ollama API
        payload = {
            "model": "gemma2:9b",
            "prompt": prompt,
            "stream": False,
            "format": payload_schema,
            "options": {
                "num_ctx": 4096
            }
        }
        
        try:
            response = requests.post(ollama_url, json=payload, timeout=30)
            response.raise_for_status()
            
            # Parse the response JSON
            try:
                response_json = response.json()
            except Exception as json_err:
                logging.error(f"Error parsing JSON for Conversation ID {convo_id}: {json_err}")
                response_json = None
            
            # Retrieve the "response" field from the API reply
            if response_json and isinstance(response_json, dict):
                raw_resp = response_json.get("response", {})
                if isinstance(raw_resp, str):
                    try:
                        response_data = json.loads(raw_resp)
                    except json.JSONDecodeError:
                        response_data = raw_resp
                else:
                    response_data = raw_resp
            else:
                response_data = response_json if response_json is not None else response.text
            
            # Extract the summary
            if isinstance(response_data, dict):
                summary = response_data.get("summary", "")
            else:
                summary = ""
            
            # Evaluate the summary using G-Eval
            test_case = LLMTestCase(
                input=messages,
                actual_output=summary
            )
            geval_metric.measure(test_case)
            score = geval_metric.score * 100  # Convert to percentage
            reason = geval_metric.reason
            verbose = geval_metric.verbose_logs
            
            logging.info(f"Evaluation for Conversation ID {convo_id}: Score={score:.2f}%, Reason={reason}")
            logging.info(f"\n\n\nEvaluation for Conversation ID {convo_id}: STEPS USED={verbose}\n\n\n")

            
            # Check if the score meets the threshold
            if score >= 80:
                logging.info(f"Summary for Conversation ID {convo_id} passed evaluation with score {score:.2f}%.")
                
                # Append the result to the DataFrame
                new_record = pd.DataFrame([{
                    "Conversation_ID": convo_id,
                    "summary": summary,
                    "evaluation_score": score,
                    "evaluation_reason": reason
                }])
                responses_df = pd.concat([responses_df, new_record], ignore_index=True)
                
                # Save the updated DataFrame to the CSV file
                responses_df.to_csv(output_csv_path, index=False, encoding='utf-8')
                logging.info(f"Saved Conversation ID {convo_id} to {output_csv_path}.")
                break
            else:
                logging.warning(f"Summary for Conversation ID {convo_id} failed evaluation with score {score:.2f}%. Retrying with additional context...")
                
                # Add feedback to the prompt for refinement
                prompt += (
                    "\n\nThe previous summary was evaluated and scored below 90%. "
                    "Please refine the summary to better capture the key points of the conversation."
                )
                attempt += 1
        
        except Exception as e:
            error_message = f"Error processing Conversation ID {convo_id}: {e}"
            logging.error(error_message)
            
            # Append the error to the DataFrame
            new_record = pd.DataFrame([{
                "Conversation_ID": convo_id,
                "summary": "",
                "evaluation_score": 0,
                "evaluation_reason": error_message
            }])
            responses_df = pd.concat([responses_df, new_record], ignore_index=True)
            
            # Save the updated DataFrame to the CSV file
            responses_df.to_csv(output_csv_path, index=False, encoding='utf-8')
            logging.info(f"Saved error for Conversation ID {convo_id} to {output_csv_path}.")
            break

# Log the end of the program
logging.info("Program completed.")