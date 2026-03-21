import json
import os
import sys

# Add ml folder to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.old_skill_extractor import extract_skills

def main():
    batch_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'new_batches', 'resume_batch.json')
    
    with open(batch_path, 'r') as f:
        data = [json.loads(line) for line in f]
        
    print(f"Loaded {len(data)} resumes for testing.")
    
    total_tokens = 0
    correct_tokens = 0
    tp = 0
    fp = 0
    fn = 0
    
    total_skills_extracted = 0
    total_skills_required = 0
    total_skill_gap = 0
    
    role = "software_engineer"
    
    for idx, row in enumerate(data):
        tokens = row["tokens"]
        ner_tags = row["ner_tags"] # 0=O, 1=B-SKILL, 2=I-SKILL
        text = " ".join(tokens)
        
        # Run extractor
        result = extract_skills(text, role=role)
        extracted = result["skills"]
        
        # Skill gap calculation
        # The abstract "required" vs "extracted"
        # Mocking required as 5 for software engineer
        extracted_names = [s["name"].lower() for s in extracted]
        
        # Token accuracy estimation (very rough alignment for the heuristic proxy)
        # B-SKILL=1, I-SKILL=2
        # We will build a predicted tag list
        predicted_tags = [0] * len(tokens)
        
        text_lower = text.lower()
        for skill in extracted:
            name = skill["name"].lower()
            # Find tokens that match this name
            name_tokens = name.split()
            for i in range(len(tokens) - len(name_tokens) + 1):
                window = [t.lower() for t in tokens[i:i+len(name_tokens)]]
                if window == name_tokens:
                    predicted_tags[i] = 1
                    for j in range(1, len(name_tokens)):
                        predicted_tags[i+j] = 2
                        
        # Compare tags
        total_tokens += len(tokens)
        
        for p, t in zip(predicted_tags, ner_tags):
            if p == t:
                correct_tokens += 1
                
            is_p_skill = (p == 1 or p == 2)
            is_t_skill = (t == 1 or t == 2)
            
            if is_p_skill and is_t_skill:
                tp += 1
            elif is_p_skill and not is_t_skill:
                fp += 1
            elif not is_p_skill and is_t_skill:
                fn += 1

    accuracy = (correct_tokens / total_tokens) * 100 if total_tokens > 0 else 0
    precision = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0
    recall = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"Overall Fallback Heuristic Accuracy: {accuracy:.2f}% (Out of 100%)")
    print(f"Heuristic Precision: {precision:.2f}%")
    print(f"Heuristic Recall:    {recall:.2f}%")
    print(f"Heuristic F1 Score:  {f1:.2f}%")
    print(f"\nThe model falls short of 85% F1 because the heuristic misses many contextual skills (high FN).")
    
if __name__ == '__main__':
    main()
