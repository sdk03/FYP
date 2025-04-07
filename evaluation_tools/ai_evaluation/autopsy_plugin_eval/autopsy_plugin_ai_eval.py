# --- Imports: data handling, logging, and DeepEval evaluation framework ---
import pandas as pd
import logging
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

# --- Configuration for file paths and entity categories ---
CSV_INPUT = 'ENTER_YOUR_INPUT_CSV_FILE'  # Your input CSV with "-" for missing categories
CSV_OUTPUT = 'ENTER_DESIRED_OUTPUT_CSV_FILE_NAME'
LOG_FILE = 'ENTER_DESIRED_OUTPUT_LOG_FILE_NAME'
CATEGORIES = [
    'Person', 'Organization', 'Geo-Political Entity', 
    'Nationalities/Religious/Political Groups', 'Date', 'Time', 
    'Money', 'Percent', 'Facility', 'Product', 'Work of Art', 
    'Language', 'Event', 'Law', 'Ordinal', 'Cardinal'
]

# --- Setup logging to file ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Initialize GEval metric for accuracy evaluation of entity extraction ---
category_check_metric = GEval(
    name="Entity Extraction Accuracy",
    criteria=f"""
    Verify if entities were correctly extracted:
    1. For categories with "-" values: check if the SMS truly contains no entities of that type
    2. For categories with non-"-" values: check if the extracted entity is valid and correctly categorized
    Categories: {', '.join(CATEGORIES)}
    """,
    evaluation_steps=[
        "Check each category's value in actual_output",
        "For '-' entries: verify absence in SMS",
        "For non-'-' entries: validate entity existence and proper categorization",
        "Calculate accuracy considering both false positives and false negatives"
    ],
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT
    ],
    model='gpt-4o',
    threshold=0.8
)

# --- Prepare output file if it doesn't exist ---
try:
    with open(CSV_OUTPUT, 'x', newline='') as f:
        pd.DataFrame(columns=[
            'sms_text', 
            *CATEGORIES, 
            'accuracy_score', 
            'evaluation_reason'
        ]).to_csv(f, index=False)
except FileExistsError:
    pass

# --- Load input CSV and evaluate each row ---
df = pd.read_csv(CSV_INPUT)

for index, row in df.iterrows():
    try:
        sms_text = row['SMS Text']
        logging.info(f"Processing row {index + 1}/{len(df)}: {sms_text[:50]}...")
        
        actual_tags = {cat: row[cat] for cat in CATEGORIES}
        
        test_case = LLMTestCase(
            input=sms_text,
            actual_output=actual_tags
        )
        category_check_metric.measure(test_case)
        
        result_row = {
            'sms_text': sms_text,
            **{cat: row[cat] for cat in CATEGORIES},
            'accuracy_score': category_check_metric.score,
            'evaluation_reason': category_check_metric.reason
        }
        
        pd.DataFrame([result_row]).to_csv(
            CSV_OUTPUT, 
            mode='a', 
            header=False, 
            index=False
        )
        
        logging.info(f"Row {index + 1} processed successfully. Score: {result_row['accuracy_score']}")
        
    except Exception as e:
        error_msg = f"Error processing row {index + 1}: {str(e)}"
        logging.error(error_msg)
        
        error_row = {
            'sms_text': sms_text if 'sms_text' in locals() else 'N/A',
            **{cat: 'ERROR' for cat in CATEGORIES},
            'accuracy_score': 'ERROR',
            'evaluation_reason': error_msg
        }
        pd.DataFrame([error_row]).to_csv(
            CSV_OUTPUT, 
            mode='a', 
            header=False, 
            index=False
        )

# --- Final log entry once processing is complete ---
logging.info("Evaluation completed. Results saved to evaluation_results.csv")