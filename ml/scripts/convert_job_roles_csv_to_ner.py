import argparse
import csv
import json
import re
from pathlib import Path

TOKEN_RE = re.compile(r"[A-Za-z0-9+#.&/-]+")


def tokenize(text: str):
    return TOKEN_RE.findall(text or "")


def normalize(token: str):
    return token.lower().strip()


def label_tokens(tokens, skill_phrases):
    labels = [0] * len(tokens)
    norm_tokens = [normalize(t) for t in tokens]

    # Longest-first matching reduces partial overlaps.
    phrases = sorted(skill_phrases, key=lambda p: len(p), reverse=True)

    for phrase in phrases:
        phrase_tokens = [normalize(t) for t in tokenize(phrase)]
        if not phrase_tokens:
            continue

        n = len(phrase_tokens)
        for i in range(0, len(norm_tokens) - n + 1):
            if norm_tokens[i : i + n] == phrase_tokens:
                # Do not overwrite a tag that was already assigned.
                if any(labels[j] != 0 for j in range(i, i + n)):
                    continue
                labels[i] = 1
                for j in range(i + 1, i + n):
                    labels[j] = 2

    return labels


def convert(csv_path: Path, output_path: Path):
    rows_written = 0

    encodings_to_try = ["utf-8-sig", "cp1252", "latin-1"]
    last_error = None

    for encoding in encodings_to_try:
        try:
            with csv_path.open("r", encoding=encoding, newline="") as infile, output_path.open(
                "w", encoding="utf-8"
            ) as outfile:
                reader = csv.DictReader(infile)
                for row in reader:
                    description = (row.get("Job Description") or "").strip()
                    skills_raw = (row.get("Skills") or "").strip()
                    if not description or not skills_raw:
                        continue

                    skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
                    tokens = tokenize(description)
                    if not tokens:
                        continue

                    ner_tags = label_tokens(tokens, skills)
                    example = {"tokens": tokens, "ner_tags": ner_tags}
                    outfile.write(json.dumps(example, ensure_ascii=True) + "\n")
                    rows_written += 1
            return rows_written
        except UnicodeDecodeError as exc:
            last_error = exc
            rows_written = 0
            continue

    if last_error:
        raise last_error

    return rows_written


def main():
    parser = argparse.ArgumentParser(
        description="Convert IT job role CSV to token-level NER training data"
    )
    parser.add_argument("--csv_path", required=True, help="Path to source CSV")
    parser.add_argument("--output_path", required=True, help="Path to output JSONL")
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = convert(csv_path, output_path)
    print(f"Wrote {rows} training rows to {output_path}")


if __name__ == "__main__":
    main()
