import os
import json
import pandas as pd
import re

# We will use weak-supervision by searching for known skills in the resume text.
# In a full production system, this list comes from O*NET or a skills graph.
KNOWN_SKILLS = [
    "Python", "Java", "C++", "C#", "JavaScript", "React", "Node.js", "Docker", "Kubernetes",
    "Machine Learning", "Data Analysis", "SQL", "NoSQL", "MongoDB", "PostgreSQL",
    "AWS", "Azure", "GCP", "HTML", "CSS", "Git", "Agile", "Scrum",
    "Microsoft Office", "Excel", "Word", "PowerPoint", "Project Management",
    "Customer Service", "Human Resources", "Recruiting", "Payroll", "Benefits Administration"
]
# Lowercase for case-insensitive matching
KNOWN_SKILLS_LOWER = [skill.lower() for skill in KNOWN_SKILLS]

def preprocess_resume_csv(input_csv, output_json, max_samples=50):
    """
    Reads Resume.csv, tokenizes the text, finds known skills, and assigns B-SKILL/I-SKILL/O tags.
    Saves the output as a JSON dataset suitable for training.
    """
    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # Take a sample to keep training times low for this initial test
    df_sample = df.sample(n=min(max_samples, len(df)), random_state=42)
    
    dataset = []
    
    for _, row in df_sample.iterrows():
        text = str(row.get('Resume_str', ''))
        # Basic tokenization (split by whitespace/punctuation, keeping punctuation separate optionally)
        # For simplicity, we just split by whitespace and strip basic punctuation.
        raw_tokens = text.split()
        
        tokens = []
        ner_tags = []
        
        i = 0
        while i < len(raw_tokens):
            # Clean token
            word = re.sub(r'[^a-zA-Z0-9#+.-]', '', raw_tokens[i])
            if not word:
                i += 1
                continue
                
            matched = False
            # Check for multi-word skills first (greedy match)
            for skill in KNOWN_SKILLS_LOWER:
                skill_words = skill.split()
                if len(skill_words) > 1:
                    # Check if the next N words match this skill
                    if i + len(skill_words) <= len(raw_tokens):
                        candidate = " ".join([re.sub(r'[^a-zA-Z0-9#+.-]', '', w).lower() for w in raw_tokens[i:i+len(skill_words)]])
                        if candidate == skill:
                            tokens.append(word)
                            ner_tags.append(1) # B-SKILL
                            # Add the rest of the words as I-SKILL
                            for j in range(1, len(skill_words)):
                                rest_word = re.sub(r'[^a-zA-Z0-9#+.-]', '', raw_tokens[i+j])
                                tokens.append(rest_word)
                                ner_tags.append(2) # I-SKILL
                            i += len(skill_words)
                            matched = True
                            break
            
            if not matched:
                # Check single word skills
                if word.lower() in KNOWN_SKILLS_LOWER:
                    tokens.append(word)
                    ner_tags.append(1) # B-SKILL
                else:
                    tokens.append(word)
                    ner_tags.append(0) # O
                i += 1

        if len(tokens) > 0:
            dataset.append({
                "tokens": tokens,
                "ner_tags": ner_tags
            })
            
    # Save the processed dataset
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        for ex in dataset:
            f.write(json.dumps(ex) + "\n")
            
    print(f"Successfully processed {len(dataset)} resumes and saved to {output_json}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Path to Kaggle Resume.csv")
    parser.add_argument("--output", type=str, default="../data/new_batches/kaggle_batch_1.json")
    parser.add_argument("--samples", type=int, default=100, help="Number of samples to process from the CSV")
    args = parser.parse_args()
    
    preprocess_resume_csv(args.input, args.output, max_samples=args.samples)
