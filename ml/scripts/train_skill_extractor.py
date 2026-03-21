import os
import argparse
import numpy as np
from datasets import load_dataset, Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    TrainingArguments,
    Trainer
)
import evaluate

# Setup logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The NER tags to extract. E.g. O = Outside, B-SKILL = Beginning of Skill, I-SKILL = Inside Skill
# We expect the dataset to provide labels as integers corresponding to these indices.
label_list = ["O", "B-SKILL", "I-SKILL"]
id2label = {i: label for i, label in enumerate(label_list)}
label2id = {label: i for i, label in enumerate(label_list)}

def parse_args():
    parser = argparse.ArgumentParser(description="Train a BERT model for Skill Extraction (NER)")
    parser.add_argument("--model_name_or_path", type=str, default="bert-base-uncased",
                        help="Base model to fine-tune (e.g. bert-base-uncased or dslim/bert-base-NER)")
    parser.add_argument("--dataset_path", type=str, required=True,
                        help="Path to the training dataset (JSON or CSV). Expected format: lists of tokens and lists of NER tags")
    parser.add_argument("--output_dir", type=str, default="../app/models/checkpoints/skill_extractor",
                        help="Directory to save the trained model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size for training")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    return parser.parse_args()


def tokenize_and_align_labels(examples, tokenizer):
    """
    Since BERT tokenizes words into subwords (WordPiece), we need to align 
    our original word-level NER tags with the newly generated subwords.
    """
    tokenized_inputs = tokenizer(
        examples["tokens"], 
        padding="max_length", 
        truncation=True, 
        max_length=512,
        is_split_into_words=True
    )

    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        # map tokens to their respective word in the original pre-tokenized sequence
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                # Special tokens (-100 is ignored by PyTorch CrossEntropyLoss)
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                # First subword of a word gets the original label
                label_ids.append(label[word_idx])
            else:
                # Subsequent subwords get -100 (or we could propagate I-SKILL)
                label_ids.append(-100)
            previous_word_idx = word_idx
        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    return tokenized_inputs


def compute_metrics(p):
    """Computes precision, recall, f1, and accuracy for NER tasks."""
    metric = evaluate.load("seqeval")
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    # Remove ignored index (special tokens)
    true_predictions = [
        [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = metric.compute(predictions=true_predictions, references=true_labels)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }


def main():
    args = parse_args()
    logger.info(f"Loading tokenizer and model: {args.model_name_or_path}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    model = AutoModelForTokenClassification.from_pretrained(
        args.model_name_or_path,
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True # Required if base model had different number of labels
    )

    # Load dataset
    logger.info(f"Loading dataset from: {args.dataset_path}")
    if args.dataset_path.endswith('.json'):
        dataset = load_dataset('json', data_files=args.dataset_path)
    elif args.dataset_path.endswith('.csv'):
        dataset = load_dataset('csv', data_files=args.dataset_path)
    else:
        raise ValueError("Unsupported dataset format. Please use JSON or CSV.")

    # Split dataset if no validation provided (assuming raw data is just a 'train' split)
    if 'test' not in dataset.keys():
        dataset = dataset['train'].train_test_split(test_size=0.1)

    # Note: Dataset should look like:
    # {"tokens": ["Proficient", "in", "Python", "and", "React"], "ner_tags": [0, 0, 1, 0, 1]}
    # (Where 1 is B-SKILL)

    logger.info("Tokenizing and aligning labels...")
    tokenized_datasets = dataset.map(
        lambda x: tokenize_and_align_labels(x, tokenizer),
        batched=True,
        remove_columns=dataset["train"].column_names
    )

    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        eval_strategy="epoch",
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        save_strategy="epoch",
        logging_steps=10,
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    logger.info("Starting training...")
    trainer.train()

    logger.info("Training complete. Saving best model...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    logger.info(f"Model saved to {args.output_dir}")


if __name__ == "__main__":
    main()
