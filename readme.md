Here’s a **revised, detailed README** for your OMR Evaluator platform, incorporating your hackathon problem statement and removing the audit storage section:

---

# Automated OMR Evaluation & Scoring System

## Overview

This project is a **Hackathon 2024 submission** built for **Innomatics Research Labs**. It automates the evaluation of OMR sheets used in placement readiness assessments across roles like Data Analytics and AI/ML for Data Science students.

The **Automated OMR Evaluation & Scoring System** replaces the traditional manual process of counting correct answers per subject and generating student reports. With potentially thousands of sheets per exam day (\~3000 sheets), the manual process is time-consuming, error-prone, and resource-intensive.

This system allows evaluators to **upload OMR sheets via a web interface**, automatically compute per-subject scores and total scores, and export results, drastically reducing turnaround time from days to minutes.

---

## Problem Statement

**Current Challenge:**

* Each exam uses standardized OMR sheets with 100 questions (20 questions per subject across 5 subjects).
* Evaluators manually check each sheet, count correct answers per subject, and prepare reports.
* Manual evaluation is **time-consuming**, **error-prone**, and **requires multiple evaluators**, delaying feedback loops crucial for student learning and placement readiness.

**Objective:**
Design a scalable, automated OMR evaluation system that:

* Accurately evaluates OMR sheets captured via mobile phone cameras.
* Provides per-subject scores (0–20 each) and total scores (0–100).
* Supports multiple sheet versions (2–4 sets per exam).
* Functions as a web application interface for evaluators.
* Maintains an error tolerance of <0.5%.
* Reduces evaluation time from days to minutes.

---

## Proposed Solution

The solution consists of a **web application and a backend OMR evaluation pipeline** with the following capabilities:

1. **Capture & Upload**

   * Students fill OMR sheets during exams.
   * Sheets are captured via mobile phone camera.
   * Evaluators upload OMR sheets through the web interface (single or bulk uploads).

2. **Image Preprocessing**

   * Grayscale conversion, noise reduction, and adaptive thresholding.
   * Detect sheet edges and correct for rotation, skew, and perspective distortion.

3. **Bubble Detection & Evaluation**

   * Identify filled bubbles using classical Computer Vision techniques (OpenCV).
   * Handle ambiguous markings optionally using ML-based classifiers.

4. **Answer Key Matching**

   * Compare detected answers with pre-defined answer keys per sheet version.

5. **Result Generation**

   * Calculate **subject-wise scores** (0–20 per subject) and **total score** (0–100).
   * Save results in **CSV or Excel format** for reporting.

6. **Web Application Interface**

   * Dashboard for **key stats, top students, and average scores per subject**.
   * Upload and evaluation form for single or bulk OMR sheets.
   * Evaluation results displayed immediately after processing.
   * Reports page with filtering, searching, and exporting.
   * Subject-wise score graphs with a dropdown for dynamic selection.

---

## Step-by-Step OMR Image Processing

1. **Load the Image**

   * Read uploaded OMR sheet via OpenCV (`cv2.imread`).
   * ![WhatsApp Image 2025-09-21 at 23 08 11 (6)](https://github.com/user-attachments/assets/57ba261f-fe2e-4579-84af-6e285868656e)


2. **Grayscale Conversion**

   * Simplifies image for processing:

     ```python
     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
     ```
     ![WhatsApp Image 2025-09-21 at 23 08 11 (1)](https://github.com/user-attachments/assets/7a47b8d2-1e67-42af-a066-46f7977bf522)


3. **Noise Reduction**

   * Apply Gaussian blur to remove noise:

     ```python
     blur = cv2.GaussianBlur(gray, (5,5), 0)
     ```

4. **Thresholding**

   * Convert the image to binary (black & white) for easier bubble detection:

     ```python
     thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 11, 2)
     ```

5. **Contour Detection**

   * Detect sheet boundaries and crop the sheet.
   * ![WhatsApp Image 2025-09-21 at 23 08 11 (4)](https://github.com/user-attachments/assets/6b9b29c6-6a3e-477a-9e4c-353547177079)
   * ![WhatsApp Image 2025-09-21 at 23 08 11 (3)](https://github.com/user-attachments/assets/4aa2d20c-ba95-4ee3-8bfb-b7710727426b)



6. **Perspective Correction**

   * Align the sheet to a top-down view.
   * ![WhatsApp Image 2025-09-21 at 23 08 11 (2)](https://github.com/user-attachments/assets/622f410a-86c1-4a11-b6cc-3a98d4d0a7b1)


7. **Bubble Detection and draw Templates**

   * Divide sheet into questions and subjects.
   * Draw templates and find out the question positions
   * Identify marked bubbles using pixel intensity thresholds.
   * ![WhatsApp Image 2025-09-21 at 23 08 11 (5)](https://github.com/user-attachments/assets/4678f22f-431b-4922-8230-095c1ec3ba87)
   * ![WhatsApp Image 2025-09-21 at 23 08 11](https://github.com/user-attachments/assets/c46e73d2-507f-4aad-8336-c8824e34eb68)


8. **Score Calculation**

   * Compare detected answers with the answer key.
   * The answer key is provides as a excel document that can be used
   * Compute per-subject scores and total scores.

---

## Tech Stack

**OMR Evaluation & Image Processing:**

* Python, OpenCV, NumPy, SciPy
* Optional ML models (Scikit-learn / TensorFlow Lite) for ambiguous marks

**Web Application:**

* Flask – Backend routes and evaluation processing
* Bootstrap – Responsive and modern UI
* pandas – Data handling for CSV/Excel export
* Chart.js – Dynamic graphs for analytics

**Database & Storage:**

* Excel / CSV for storing results
* JSON/Excel export for sharing and analysis

---

## Project Structure

```
Hackathon 24/
├── app.py                # Flask routes and evaluation logic
├── omr_utils.py          # OMR evaluation and scoring
├── script.py             # Image preprocessing & bubble detection
├── templates/
│   ├── base.html         # Navbar & layout
│   ├── home.html         # Dashboard
│   ├── evaluate.html     # Evaluation form & results
│   ├── reports.html      # Reports and charts
│   ├── login.html        # Login form
├── uploads/
│   ├── answers/          # Uploaded answer keys
│   ├── omr/              # Uploaded OMR sheets
│   └── evaluations.csv   # Master evaluation results
├── static/
│   └── style.css         # Optional custom styles
└── README.md
```

---

## Example Workflow

1. Login as evaluator.
2. Upload a new answer key for the exam version.
3. Upload OMR sheets (single or bulk).
4. Select sheets and answer key, optionally enter Student ID.
5. Evaluate sheets.
6. View subject-wise results and total scores.
7. Access **Reports** for filtering, exporting, and dynamic graphs.

---

## Customization

* **Subjects:** Update `SUBJECTS` in `omr_utils.py`.
* **Sheet Versions:** Upload multiple answer key versions.
* **Styling:** Modify `static/style.css` or templates.
* **Advanced OMR Logic:** Extend `script.py` for skewed sheets or multiple formats.

---

## Contributors

* Arya Anand (@aryaanand055)
* Abishek N
* Akshaya NE
* Hackathon 2024 Team

---

## License

For hackathon and educational use. See [LICENSE](LICENSE).
