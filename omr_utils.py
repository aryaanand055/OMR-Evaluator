import csv
import os
from datetime import datetime
import random

SUBJECTS = ["Python", "EDA", "SQL", "POWER BI", "Satistics"]
REPORT_FILE = "uploads/evaluations.csv"

def evaluate_results(key, marked):
    results = {}
    total_score = 0
    total_questions = 0
    for i in range(len(key)):
        for j in range(len(key[i])):
            if(key[i][j] == marked[i][j]):
                results[SUBJECTS[i]] = results.get(SUBJECTS[i], 0) + 1
                total_score += 1
            total_questions += 1
   
    result_data = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": results,
        "total_score": total_score,
        "total_questions": total_questions
    }
    return result_data


def save_evaluation(result, student_id, version, flagged, omr_file, key_file):
    file_exists = os.path.isfile(REPORT_FILE)
    with open(REPORT_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        
        # Update header to include new fields
        if not file_exists:
            header = ["Date", "OMR Sheet", "Answer KEY"] + SUBJECTS + ["Total Score", "Total Questions", "Student ID", "Version", "Flagged"]
            writer.writerow(header)
        
        # Flatten row and add new fields at the end
        row = [result["date"], omr_file, key_file]
        row += [result["result"].get(subj, 0) for subj in SUBJECTS]
        row += [result["total_score"], result["total_questions"]]
        row += [student_id, version, flagged]
        
        writer.writerow(row)
