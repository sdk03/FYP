# --- Imports: GUI, CSV handling, text evaluation metrics ---
import tkinter as tk
from tkinter import filedialog
import pandas as pd
from rouge import Rouge
from bert_score import score as bert_score
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.tokenize import word_tokenize
import logging

# --- Suppress verbose logging from transformers ---
logging.getLogger("transformers").setLevel(logging.ERROR)

# --- Initialize GUI window ---
root = tk.Tk()
root.title("Summary Evaluation Metrics")

# --- Variables to store file paths for input CSVs ---
human_summary_path = tk.StringVar()
ai_summary_path = tk.StringVar()

# --- File selection for human summaries ---
def select_human_summary():
    """Open a file dialog to select the human summary CSV and update the label."""
    path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if path:
        human_summary_path.set(path)
        label_human_path.config(text=path)

# --- File selection for AI summaries ---
def select_ai_summary():
    """Open a file dialog to select the AI summary CSV and update the label."""
    path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if path:
        ai_summary_path.set(path)
        label_ai_path.config(text=path)

# --- Main logic for computing ROUGE, BLEU, and BERTScore ---
def compute_metrics():
    """Compute evaluation metrics and display results."""
    human_file = human_summary_path.get()
    ai_file = ai_summary_path.get()
    
    # Check if both files are selected
    if not human_file or not ai_file:
        result_label.config(text="Please select both CSV files.")
        return

    # Read the CSV files
    try:
        human_df = pd.read_csv(human_file)
        ai_df = pd.read_csv(ai_file)
    except Exception as e:
        result_label.config(text=f"Error reading CSV files: {e}")
        return

    # Verify required columns
    if "Convo_ID" not in human_df.columns or "Human_Summary" not in human_df.columns:
        result_label.config(text="Human summary CSV must have 'Convo_ID' and 'Human_Summary' columns.")
        return
    if "Convo_ID" not in ai_df.columns or "AI_Summary" not in ai_df.columns:
        result_label.config(text="AI summary CSV must have 'Convo_ID' and 'AI_Summary' columns.")
        return

    # Clean the data: remove rows with missing summaries and convert to strings
    human_df = human_df.dropna(subset=["Human_Summary"])
    ai_df = ai_df.dropna(subset=["AI_Summary"])
    human_df["Human_Summary"] = human_df["Human_Summary"].astype(str)
    ai_df["AI_Summary"] = ai_df["AI_Summary"].astype(str)

    # Merge DataFrames on Convo_ID
    merged_df = pd.merge(human_df, ai_df, on="Convo_ID")
    if merged_df.empty:
        result_label.config(text="No matching Convo_IDs found between the two files.")
        return

    # Extract summaries as lists
    human_summaries = merged_df["Human_Summary"].tolist()
    ai_summaries = merged_df["AI_Summary"].tolist()

    # Compute ROUGE scores
    rouge_scorer = Rouge()
    rouge_scores = rouge_scorer.get_scores(ai_summaries, human_summaries, avg=False)
    rouge1_f1 = [score["rouge-1"]["f"] for score in rouge_scores]
    rouge2_f1 = [score["rouge-2"]["f"] for score in rouge_scores]
    rougel_f1 = [score["rouge-l"]["f"] for score in rouge_scores]

    # Compute BLEU scores with smoothing
    smoother = SmoothingFunction()
    bleu_scores = []
    for ref, hyp in zip(human_summaries, ai_summaries):
        ref_tokens = word_tokenize(ref)
        hyp_tokens = word_tokenize(hyp)
        if len(hyp_tokens) == 0 or len(ref_tokens) == 0:
            bleu = 0.0
        else:
            bleu = sentence_bleu([ref_tokens], hyp_tokens, weights=(0.25, 0.25, 0.25, 0.25), 
                               smoothing_function=smoother.method1)
        bleu_scores.append(bleu)

    # Compute BERTScore
    P, R, F1 = bert_score(ai_summaries, human_summaries, lang="en", verbose=False)
    bertscore_f1 = F1.tolist()

    # Calculate average scores
    avg_rouge1 = sum(rouge1_f1) / len(rouge1_f1)
    avg_rouge2 = sum(rouge2_f1) / len(rouge2_f1)
    avg_rougel = sum(rougel_f1) / len(rougel_f1)
    avg_bleu = sum(bleu_scores) / len(bleu_scores)
    avg_bertscore_f1 = sum(bertscore_f1) / len(bertscore_f1)

    # Format the results
    result_text = f"Number of conversations evaluated: {len(merged_df)}\n"
    result_text += f"Average ROUGE-1 F1: {avg_rouge1:.4f}\n"
    result_text += f"Average ROUGE-2 F1: {avg_rouge2:.4f}\n"
    result_text += f"Average ROUGE-L F1: {avg_rougel:.4f}\n"
    result_text += f"Average BLEU: {avg_bleu:.4f}\n"
    result_text += f"Average BERTScore F1: {avg_bertscore_f1:.4f}"
    
    # Display the results
    result_label.config(text=result_text)

# --- GUI layout and buttons ---
tk.Label(root, text="Human Summary CSV:").grid(row=0, column=0, padx=5, pady=5)
button_human = tk.Button(root, text="Select", command=select_human_summary)
button_human.grid(row=0, column=1, padx=5, pady=5)
label_human_path = tk.Label(root, text="", wraplength=300)
label_human_path.grid(row=0, column=2, padx=5, pady=5)

tk.Label(root, text="AI Summary CSV:").grid(row=1, column=0, padx=5, pady=5)
button_ai = tk.Button(root, text="Select", command=select_ai_summary)
button_ai.grid(row=1, column=1, padx=5, pady=5)
label_ai_path = tk.Label(root, text="", wraplength=300)
label_ai_path.grid(row=1, column=2, padx=5, pady=5)

button_compute = tk.Button(root, text="Compute Metrics", command=compute_metrics)
button_compute.grid(row=2, column=0, columnspan=3, pady=10)

result_label = tk.Label(root, text="", justify="left", wraplength=400)
result_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

# --- Start the GUI event loop ---
root.mainloop()