# Evaluation Tools: Forensic Metric Assessment

This folder provides automated scripts for evaluating LLM outputs against human-grounded truth using both statistical and model-based metrics.

## Features
- Precision, Recall, F1, Accuracy, Specificity, MCC (for Categorization)
- BERTScore + G-Eval (for Summarization)
- Weighted scoring and hallucination tracking

## Tools Required
- `scikit-learn`
- `transformers` (for BERTScore)
- Custom G-Eval LLM-based module (included)

## Usage
1. Place LLM outputs and ground truth files in `/data/`.
2. Run `evaluate.py` for statistical results.
3. Use `geval_interface.py` for summarization scoring.
