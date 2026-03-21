# BERT NER Skill Extractor Fine-Tuning Guide (Google Colab)

This guide provides step-by-step instructions to fine-tune the `bert-base-uncased` model for Named Entity Recognition (NER) on skill extraction using Google Colab's free GPU instances (T4) or A100 instances.

## Prerequisites

1.  A Google account.
2.  The `resume_batch.json` dataset file (provided in `ml/data/new_batches/resume_batch.json` in this repository).
3.  The `train_skill_extractor.py` file from the `ml/scripts/` directory.

## Step 1: Open Google Colab and Setup GPU Environment

1.  Go to [Google Colab](https://colab.research.google.com/) and create a **New Notebook**.
2.  In the top menu, go to **Runtime > Change runtime type**.
3.  Select **T4 GPU** (or A100 GPU if available/preferred) under Hardware accelerator and click **Save**.

## Step 2: Install Required Libraries

In the first cell of your Colab notebook, copy and paste the following snippet, then run it to install the required Python libraries.

```bash
!pip install -q transformers datasets evaluate seqeval
!pip install -q accelerate -U
```

## Step 3: Upload Files

In the second cell, we will set up our local file structure to mimic your repository and upload the python script and the training data.

1.  Run the following code block to create the required folders:

```bash
!mkdir -p ml/data/new_batches
!mkdir -p ml/scripts
!mkdir -p app/models/checkpoints/skill_extractor
```

2.  On the left sidebar, click the **Folder icon** to open the Colab file explorer.
3.  Upload `resume_batch.json` into the `ml/data/new_batches/` folder.
4.  Upload `train_skill_extractor.py` into the `ml/scripts/` folder.

## Step 4: Run Fine-tuning Script

In the third cell, execute the training script by running the python file. The script handles token alignment, dataset splitting, training, and metric evaluation automatically.

```bash
!python ml/scripts/train_skill_extractor.py \
    --model_name_or_path bert-base-uncased \
    --dataset_path ml/data/new_batches/resume_batch.json \
    --output_dir app/models/checkpoints/skill_extractor \
    --epochs 3 \
    --batch_size 8 \
    --learning_rate 2e-5
```

*Note: Depending on your dataset size, training may take a few minutes. You should observe the validation logs inside Colab displaying Precision, Recall, and Accuracy during training.*

## Step 5: Download Checkpoint Artifacts

Once training completes, the fine-tuned model checkpoint will be saved to the `app/models/checkpoints/skill_extractor` folder. You can zip them and download them to your local repository.

Run this cell to zip the model folder:

```bash
!zip -r skill_extractor_model.zip app/models/checkpoints/skill_extractor
```

Then run this cell to trigger the file download from Colab to your machine:

```python
from google.colab import files
files.download('skill_extractor_model.zip')
```

## Next Steps

After downloading `skill_extractor_model.zip`:
1.  Extract the zip file.
2.  Move the contents inside `app/models/checkpoints/skill_extractor` to the `ml/app/models/checkpoints/skill_extractor` directory in your local `pathforge-hackcodeio` repository.
3.  Run the system as normal—the refactored `skill_extractor.py` code will now pick up the dynamically loaded HuggingFace Pipeline automatically!
