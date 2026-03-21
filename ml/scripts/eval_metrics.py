"""
eval_metrics.py

Evaluates the fine-tuned BERT NER skill extractor model against the dataset (resume_batch.json),
calculating precision, recall, f1, and accuracy via the seqeval metric.

This script expects the extracted model to be locally present at `app/models/checkpoints/skill_extractor`.
"""

import os
import argparse
import numpy as np
import logging
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    pipeline
)
import evaluate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

label_list = ["O", "B-SKILL", "I-SKILL"]

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate a trained BERT model for Skill Extraction (NER)")
    parser.add_argument("--model_path", type=str, default="../app/models/checkpoints/skill_extractor",
                        help="Path to the fine-tuned model directory")
    parser.add_argument("--dataset_path", type=str, default="../data/new_batches/resume_batch.json",
                        help="Path to the validation dataset (JSON).")
    return parser.parse_args()


def tokenize_and_align_labels(examples, tokenizer):
    tokenized_inputs = tokenizer(
        examples["tokens"], 
        padding="max_length", 
        truncation=True, 
        max_length=512,
        is_split_into_words=True
    )

    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(label[word_idx])
            else:
                label_ids.append(-100)
            previous_word_idx = word_idx
        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    return tokenized_inputs


def main():
    args = parse_args()

    # Get absolute paths
    model_path = os.path.abspath(args.model_path)
    dataset_path = os.path.abspath(args.dataset_path)

    logger.info(f"Loading tokenizer and model from: {model_path}")
    if not os.path.exists(model_path):
        logger.error(f"Model path does not exist: {model_path}")
        return

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForTokenClassification.from_pretrained(model_path)

    logger.info(f"Loading dataset from: {dataset_path}")
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset path does not exist: {dataset_path}")
        return

    dataset = load_dataset('json', data_files={'test': dataset_path})
    
    logger.info("Tokenizing and aligning labels...")
    tokenized_datasets = dataset.map(
        lambda x: tokenize_and_align_labels(x, tokenizer),
        batched=True,
        remove_columns=dataset["test"].column_names
    )

    tokenized_test = tokenized_datasets["test"]

    # We use Trainer for evaluation metric parsing since evaluate provides straightforward handling with the HF pipeline APIs,
    # or we can iterate manually. We'll run iteration manually for transparency.
    seqeval_metric = evaluate.load("seqeval")
    
    true_predictions = []
    true_labels = []

    logger.info("Running evaluation over dataset...")
    # Using PyTorch model forward pass or pipeline? We'll just run manual forward pass
    import torch
    
    # move model to correct device if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    # Predict loop
    for i in range(len(tokenized_test)):
        inputs = {
            "input_ids": torch.tensor([tokenized_test[i]["input_ids"]]).to(device),
            "attention_mask": torch.tensor([tokenized_test[i]["attention_mask"]]).to(device)
        }
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        predictions = torch.argmax(outputs.logits, dim=2).cpu().numpy()[0]
        labels = tokenized_test[i]["labels"]

        # Filter out ignored indices (-100)
        true_pred = [label_list[p] for p, l in zip(predictions, labels) if l != -100]
        true_lab = [label_list[l] for p, l in zip(predictions, labels) if l != -100]
        
        true_predictions.append(true_pred)
        true_labels.append(true_lab)

    results = seqeval_metric.compute(predictions=true_predictions, references=true_labels)
    
    logger.info("Evaluation Complete. Results:")
    logger.info(f"Overall Precision : {results['overall_precision']:.4f}")
    logger.info(f"Overall Recall    : {results['overall_recall']:.4f}")
    logger.info(f"Overall F1        : {results['overall_f1']:.4f}")
    logger.info(f"Overall Accuracy  : {results['overall_accuracy']:.4f}")
    
    if results['overall_f1'] > 0.85:
        logger.info("SUCCESS: F1 Accuracy has increased past 85%!")
    else:
        logger.warning("F1 Accuracy is below the 85% target threshold. Further fine-tuning may be required.")


if __name__ == "__main__":
    main()
