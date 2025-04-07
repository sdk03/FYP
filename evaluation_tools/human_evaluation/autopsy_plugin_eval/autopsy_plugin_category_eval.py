# --- Imports: data handling, GUI for file dialog, and tabular display ---
import pandas as pd
from tabulate import tabulate
import tkinter as tk
from tkinter import filedialog
import os

# --- File selection using Tkinter dialog ---
root = tk.Tk()
root.withdraw()  

# Open file dialog to select CSV
file_path = filedialog.askopenfilename(
    title="Select CSV file",
    filetypes=[("CSV files", "*.csv")]
)

if not file_path:
    print("No file selected. Exiting.")
    exit()

# --- Read selected CSV file into DataFrame ---
df = pd.read_csv(file_path)

# --- Identify category columns (bounded by 'Person' and 'Cardinal') ---
columns = df.columns.tolist()
start_idx = columns.index('Person')
end_idx = columns.index('Cardinal')
categories = columns[start_idx:end_idx+1]

# --- Initialize accumulators for overall evaluation ---
total_tp = 0
total_tn = 0
total_fp = 0
total_fn = 0

results = []

# --- Evaluate each category column for classification performance ---
for category in categories:
    counts = df[category].value_counts().to_dict()
    tp = counts.get('TP', 0)
    tn = counts.get('TN', 0)
    fp = counts.get('FP', 0)
    fn = counts.get('FN', 0)
    
    total_tp += tp
    total_tn += tn
    total_fp += fp
    total_fn += fn
    
    total = tp + tn + fp + fn
    
    sensitivity = tp / (tp + fn) if (tp + fn) != 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) != 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) != 0 else 0.0
    accuracy = (tp + tn) / total if total != 0 else 0.0
    
    fpr = fp / (fp + tn) if (fp + tn) != 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) != 0 else 0.0
    
    if precision + sensitivity == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * sensitivity) / (precision + sensitivity)
    
    denominator = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if denominator == 0:
        mcc = 0.0
    else:
        mcc = (tp * tn - fp * fn) / (denominator ** 0.5)
    
    results.append([
        category,
        tp, fp, tn, fn,
        f"{sensitivity*100:.2f}%",
        f"{specificity*100:.2f}%",
        f"{fpr*100:.2f}%",
        f"{fnr*100:.2f}%",
        f"{precision*100:.2f}%",
        f"{accuracy*100:.2f}%",
        f"{f1*100:.2f}%",
        round(mcc, 4)
    ])

# --- Calculate and append overall performance metrics ---
total = total_tp + total_tn + total_fp + total_fn

overall_sensitivity = total_tp / (total_tp + total_fn) if (total_tp + total_fn) != 0 else 0.0
overall_specificity = total_tn / (total_tn + total_fp) if (total_tn + total_fp) != 0 else 0.0
overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) != 0 else 0.0
overall_accuracy = (total_tp + total_tn) / total if total != 0 else 0.0

overall_fpr = total_fp / (total_fp + total_tn) if (total_fp + total_tn) != 0 else 0.0
overall_fnr = total_fn / (total_fn + total_tp) if (total_fn + total_tp) != 0 else 0.0

if overall_precision + overall_sensitivity == 0:
    overall_f1 = 0.0
else:
    overall_f1 = 2 * (overall_precision * overall_sensitivity) / (overall_precision + overall_sensitivity)

denominator = (total_tp + total_fp) * (total_tp + total_fn) * (total_tn + total_fp) * (total_tn + total_fn)
if denominator == 0:
    overall_mcc = 0.0
else:
    overall_mcc = (total_tp * total_tn - total_fp * total_fn) / (denominator ** 0.5)

results.append([
    'OVERALL',
    total_tp, total_fp, total_tn, total_fn,
    f"{overall_sensitivity*100:.2f}%",
    f"{overall_specificity*100:.2f}%",
    f"{overall_fpr*100:.2f}%",
    f"{overall_fnr*100:.2f}%",
    f"{overall_precision*100:.2f}%",
    f"{overall_accuracy*100:.2f}%",
    f"{overall_f1*100:.2f}%",
    round(overall_mcc, 4)
])

# --- Prepare results DataFrame and save to a new file ---
headers = [
    'Category', 'TP', 'FP', 'TN', 'FN',
    'Sensitivity', 'Specificity', 'FPR', 'FNR',
    'Precision', 'Accuracy', 'F1 Score', 'MCC'
]

df_results = pd.DataFrame(results, columns=headers)

output_dir = os.path.dirname(file_path)
base_name = os.path.basename(file_path)
name_part, ext_part = os.path.splitext(base_name)
output_filename = f"{name_part}_16_categories_eval{ext_part}"
output_path = os.path.join(output_dir, output_filename)
df_results.to_csv(output_path, index=False)

# --- Display result path and summary table in console ---
print(f"\nResults saved to: {output_path}")
print("\nConsole Output:")
print(tabulate(results, headers=headers, tablefmt='pretty', disable_numparse=True))