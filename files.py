import pandas as pd
import re
from s2 import process_with_fallback as process_omr

def process_answer_key(filepath):
    df = pd.read_excel(filepath)
    all_subjects = []

    for col in df.columns:
        subject_answers = []
        for entry in df[col].dropna():
            # Split at any of: hyphen, en dash, period
            parts = re.split(r'\s*[-–.]\s*', str(entry), maxsplit=1)
            if len(parts) >= 2:
                ans_str = parts[1].strip()
                # Split multiple answers separated by comma, dot, or semicolon
                answers = [a.strip().upper() for a in re.split(r'[,.;]', ans_str) if a.strip()]
                if len(answers) == 1:
                    subject_answers.append(answers[0])
                else:
                    subject_answers.append(answers)
        all_subjects.append(subject_answers)
    return all_subjects


def process_omr_sheet(filepath):
    return process_omr(filepath)


if __name__ == "__main__":
    print("Testing OMR and Key Processing...")
    marked = process_omr_sheet("Img1.jpeg")
    print("Marked Answers:", marked)

    key = process_answer_key("Key.xlsx")
    print("Answer Key:", key)
