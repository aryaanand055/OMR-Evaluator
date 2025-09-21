import os
import json
from io import BytesIO
from datetime import datetime
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session
from omr_utils import  evaluate_results, SUBJECTS, REPORT_FILE,save_evaluation
from files import *


app = Flask(__name__)
app.secret_key = "secret123"

# --- Simple Auth ---
USERS = {"admin": "1234"}  # username: password

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please login to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if USERS.get(username) == password:
            session["logged_in"] = True
            session["username"] = username
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))

# --- Folders ---
UPLOAD_FOLDER = 'uploads'
ANSWER_FOLDER = os.path.join(UPLOAD_FOLDER, 'answers')
OMR_FOLDER = os.path.join(UPLOAD_FOLDER, 'omr')
RECTIFIED_FOLDER = os.path.join(UPLOAD_FOLDER, 'rectified')
JSON_FOLDER = os.path.join(UPLOAD_FOLDER, 'json_results')

for folder in [UPLOAD_FOLDER, ANSWER_FOLDER, OMR_FOLDER, RECTIFIED_FOLDER, JSON_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# --- Home Dashboard ---
@app.route('/')
@login_required
def home():
    total_answer_keys = len(os.listdir(ANSWER_FOLDER))
    total_omr_sheets = len(os.listdir(OMR_FOLDER))
    flagged_count = 0
    sheets_evaluated = 0
    last_score = None
    top_students = []
    avg_scores = {}

    if os.path.isfile(REPORT_FILE):
        df = pd.read_csv(REPORT_FILE)
        sheets_evaluated = len(df)
        flagged_count = df["Flagged"].sum() if "Flagged" in df.columns else 0

        if not df.empty:
            # Last evaluated sheet score
            last_score = f"{df.iloc[-1]['Total Score']}/{df.iloc[-1]['Total Questions']}"

            # Top 3 students
            if "Student ID" in df.columns and "Total Score" in df.columns:
                top_students = df.sort_values("Total Score", ascending=False).head(3)[["Student ID","Total Score"]].to_dict('records')

            # Average scores per subject
            for s in SUBJECTS:
                if s in df.columns:
                    avg_scores[s] = round(df[s].mean(), 2)
                else:
                    avg_scores[s] = None

    return render_template("home.html",
        total_answer_keys=total_answer_keys,
        total_omr_sheets=total_omr_sheets,
        sheets_evaluated=sheets_evaluated,
        flagged_count=flagged_count,
        last_score=last_score,
        top_students=top_students,
        avg_scores=avg_scores
    )

# --- Reports Route ---
@app.route('/reports')
@login_required
def reports():
    df = pd.read_csv(REPORT_FILE) if os.path.isfile(REPORT_FILE) else pd.DataFrame()

    # Filters
    filters = {
        "student_id": request.args.get("student_id", ""),
        "date": request.args.get("date", ""),
        "version": request.args.get("version", ""),
        "flagged": request.args.get("flagged", ""),
        "omr_file": request.args.get("omr_file", ""),
        "key_file": request.args.get("key_file", "")
    }

    filtered_df = df.copy()
    if filters["student_id"]:
        filtered_df = filtered_df[
            filtered_df["Student ID"].astype(str).str.contains(filters["student_id"], case=False, na=False)
        ]
    if filters["date"]:
        filtered_df = filtered_df[
            filtered_df["Date"].astype(str).str.contains(filters["date"], case=False, na=False)
        ]
    if filters["version"]:
        filtered_df = filtered_df[filtered_df["Version"].astype(str) == filters["version"]]
    if filters["flagged"]:
        flagged_val = True if filters["flagged"] == "1" else False
        filtered_df = filtered_df[filtered_df["Flagged"] == flagged_val]
    if filters["omr_file"]:
        filtered_df = filtered_df[
            filtered_df["OMR Sheet"].astype(str).str.contains(filters["omr_file"], case=False, na=False)
        ]
    if filters["key_file"]:
        filtered_df = filtered_df[
            filtered_df["Answer Key"].astype(str).str.contains(filters["key_file"], case=False, na=False)
        ]
    # Export options
    export_type = request.args.get("export")
    if export_type == "csv":
        return filtered_df.to_csv(index=False), 200, {"Content-Type": "text/csv"}
    if export_type == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            filtered_df.to_excel(writer, index=False)
        output.seek(0)
        return output.read(), 200, {"Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}

    # Prepare data for charts and template
    reports = filtered_df.to_dict("records")
    labels = filtered_df["Date"].tolist() if "Date" in filtered_df.columns else []
    subject_scores = {s: filtered_df[s].tolist() if s in filtered_df.columns else [] for s in SUBJECTS}
    overall_scores = filtered_df["Total Score"].tolist() if "Total Score" in filtered_df.columns else []
    versions = filtered_df["Version"].unique().tolist() if "Version" in filtered_df.columns else []

    return render_template("reports.html",
        reports=reports,
        subjects=SUBJECTS,
        labels=json.dumps(labels),
        subject_scores=json.dumps(subject_scores),
        overall_scores=json.dumps(overall_scores),
        filters=filters,
        versions=versions
    )

# --- Evaluate Route ---
@app.route('/evaluate', methods=['GET', 'POST'])
@login_required

def evaluate():
    existing_keys = os.listdir(ANSWER_FOLDER)
    existing_omr = os.listdir(OMR_FOLDER)
    versions = ["v1"]
    result = None

    if request.method == "POST":
        # Upload answer key
        if "answer_file" in request.files and request.files["answer_file"].filename:
            file = request.files["answer_file"]
            split_save_xlsx(file.filename)
            flash("New answer key uploaded!", "success")
            return redirect(url_for("evaluate"))

        # Upload OMR sheets
        if "bulk_omr" in request.files and request.files.getlist("bulk_omr")[0].filename:
            files = request.files.getlist("bulk_omr")
            total, success = len(files), 0
            for file in files:
                if file.filename:
                    file.save(os.path.join(OMR_FOLDER, file.filename))
                    process_omr_sheet(os.path.join(OMR_FOLDER, file.filename))
                    success += 1
            flash(f"Bulk upload complete: {success}/{total} sheets uploaded.", "success")
            return redirect(url_for("evaluate"))

        # Upload single OMR sheet
        if "omr_file" in request.files and request.files["omr_file"].filename:
            file = request.files["omr_file"]
            filename = file.filename
            filepath = os.path.join(OMR_FOLDER, filename)
            file.save(filepath)
            process_omr_sheet(filepath)
            flash(f"New OMR sheet '{filename}' uploaded!", "success")
            return redirect(url_for("evaluate"))


        # Evaluation
        if "evaluate" in request.form:
            student_id = request.form.get("student_id")
            selected_key = request.form.get("selected_key")
            selected_omr_list = request.form.getlist("selected_omr")
            version = request.form.get("version")
            flagged = True if request.form.get("flagged") == "on" else False

            if not selected_key or not selected_omr_list:
                flash("Please select both Answer Key and OMR Sheet.", "danger")
                return redirect(url_for("evaluate"))

            for omr_file in selected_omr_list:
                marked_answers = process_omr_sheet(os.path.join(OMR_FOLDER, omr_file))
                key_answers = process_answer_key(os.path.join(ANSWER_FOLDER, selected_key))
                
                result = evaluate_results(key_answers, marked_answers)
                save_evaluation(result, student_id, version, flagged, omr_file, selected_key)

    return render_template("evaluate.html",
        existing_keys=existing_keys,
        existing_omr=existing_omr,
        versions=versions,
        result=result,
        subjects=SUBJECTS
    )

if __name__ == "__main__":
    app.run(debug=True)
