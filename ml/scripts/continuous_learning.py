import os
import glob
import logging
import argparse
from train_skill_extractor import main as train_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Continuous Learning Loop for Skill Extractor")
    parser.add_argument("--data_dir", type=str, default="../data/new_batches/",
                        help="Directory containing new dataset batches (JSON/CSV)")
    parser.add_argument("--model_dir", type=str, default="../app/models/checkpoints/skill_extractor",
                        help="Directory of the currently deployed model")
    parser.add_argument("--epochs_per_loop", type=int, default=1, help="Epochs to train per new batch")
    return parser.parse_args()

def run_continuous_learning():
    """
    Looks for new dataset files in the data_dir.
    If found, loads the CURRENT model from model_dir, fine-tunes it on the new data,
    and overwrites the model_dir with the improved model.
    """
    args = parse_args()
    
    if not os.path.exists(args.data_dir):
        os.makedirs(args.data_dir, exist_ok=True)
        logger.info(f"Created {args.data_dir}. Drop your new data files here to keep training.")
        return

    # Find all new datasets
    new_datasets = glob.glob(os.path.join(args.data_dir, "*.json")) + glob.glob(os.path.join(args.data_dir, "*.csv"))
    
    if not new_datasets:
        logger.info("No new data batches found to train on. The model is waiting for more data.")
        return

    # If the model doesn't exist yet, we start from the base bert model
    current_model = args.model_dir if os.path.exists(args.model_dir) else "bert-base-uncased"
    logger.info(f"Current Model State: {current_model}")

    for dataset_file in new_datasets:
        logger.info(f"=== Starting Continuous Improvement loop on: {dataset_file} ===")
        
        # Override sys.argv to call the original train script programmatically
        import sys
        sys.argv = [
            "train_skill_extractor.py",
            "--model_name_or_path", current_model,
            "--dataset_path", dataset_file,
            "--output_dir", args.model_dir,
            "--epochs", str(args.epochs_per_loop),
            "--batch_size", "8"
        ]
        
        try:
            train_model()
            logger.info(f"Successfully improved model using {dataset_file}")
            
            # After training, the model in args.model_dir is updated.
            current_model = args.model_dir 
            
            # Archive the processed dataset so we don't train on it again
            archive_dir = os.path.join(args.data_dir, "processed")
            os.makedirs(archive_dir, exist_ok=True)
            os.rename(dataset_file, os.path.join(archive_dir, os.path.basename(dataset_file)))
            
        except Exception as e:
            logger.error(f"Failed to train on {dataset_file}: {e}")
            break

    logger.info("Continuous learning cycle complete. Model is now smarter!")

if __name__ == "__main__":
    run_continuous_learning()
