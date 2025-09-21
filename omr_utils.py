import csv
import os
from datetime import datetime
import random

SUBJECTS = ["Math", "English", "Science", "Social Studies", "Tamil"]
REPORT_FILE = "uploads/evaluations.csv"

def process_answer_key(file_path):
    return "Answer key processed successfully!"

def process_omr_sheet(file_path):
    return "OMR sheet processed successfully!"

def evaluate_results(answer_key, omr_file):
    results = {}
    total_score = 0
    total_questions = 0

    for subject in SUBJECTS:
        score = random.randint(10, 20)  # placeholder
        results[subject] = score
        total_score += score
        total_questions += 20

    overall = total_score
    result_data = {
        "omr": omr_file,
        "answer_key": answer_key,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "subjects": results,
        "overall": overall,
        "total": total_questions
    }

    # --- Save to CSV ---
    save_evaluation(result_data)

    return result_data

def save_evaluation(result):
    file_exists = os.path.isfile(REPORT_FILE)
    with open(REPORT_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            header = ["omr_file", "answer_key", "date"] + SUBJECTS + ["Overall", "Total"]
            writer.writerow(header)

        row = [
            result["omr"], 
            result["answer_key"], 
            result["date"]
        ] + [result["subjects"][s] for s in SUBJECTS] + [result["overall"], result["total"]]
        writer.writerow(row)
