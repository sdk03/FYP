# --- Imports: Flask for API, pickle/json for data loading, CORS for frontend access ---
from flask import Flask, jsonify
import pickle
import json
from flask_cors import CORS

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)

# --- File paths for LLM response and original clustered messages ---
FILE_PATH_LLM = '../llm-response.pkl'
FILE_PATH_OG = '../cleaned_data.pkl'

# --- Load and format data into JSON for API response ---
def load_data():
    """Loads data from pickle files and formats it for JSON."""
    with open(FILE_PATH_LLM, 'rb') as file:
        data = pickle.load(file)

    with open(FILE_PATH_OG, 'rb') as fileOG:
        raw_data = pickle.load(fileOG)

    nodes = []
    links = []

    for index, i in enumerate(data):
        response = json.loads(i['response'])  # Convert the string to a dictionary
        window_start = i['window_start']
        window_end = i['window_end']
        
        original_data = raw_data[index]
        formatted_og_data = "\n".join([
            f"{msg['Date/Time']}|{msg['Message Type']}|{msg['Text']}|{msg['From Phone Number']}"
            for msg in original_data["messages"]
        ])

        nodes.append({
            "id": index,
            "summary": response['window_summary'],
            "window_start": window_start,
            "window_end": window_end,
            "original_messages": formatted_og_data
        })

        if index > 0:
            links.append({"source": index - 1, "target": index - 1})

    return {"nodes": nodes, "links": links}

# --- API endpoint to retrieve summary and message graph data ---
@app.route('/get_data')
def get_data():
    """API endpoint to serve data dynamically."""
    return jsonify(load_data())

# --- Start the Flask server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)