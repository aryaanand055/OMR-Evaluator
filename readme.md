# OMR Evaluator Platform

## Overview
OMR Evaluator is a full-featured web application for scanning, evaluating, and reporting results from OMR (Optical Mark Recognition) sheets. Built with Flask, Bootstrap, pandas, and Chart.js, it provides a dashboard, bulk evaluation, reporting, authentication, and audit storage for educational institutions and exam centers.

---

## Features
- **Dashboard**: View key stats, top students, and average scores per subject.
- **Answer Key Upload**: Upload and manage answer keys for different exam versions.
- **OMR Sheet Upload**: Upload individual or bulk OMR sheets for evaluation.
- **Bulk Evaluation**: Select multiple OMR sheets for simultaneous evaluation.
- **Student ID Optional**: Student ID can be left blank during evaluation.
- **Evaluation Results**: View detailed subject-wise scores and overall results.
- **Reports**: Filter, search, and export results (CSV/Excel).
- **Charts & Analytics**: Interactive graphs for score distributions, recent evaluations, and averages.
- **Audit Storage**: Rectified images and JSON results saved for each evaluation.
- **Authentication**: Simple login/logout for evaluator access.
- **Responsive UI**: Modern Bootstrap design for desktop and mobile.

---

## Project Structure
```
Hackathon 24/
├── app.py                # Main Flask application
├── omr_utils.py          # OMR processing and evaluation logic
├── script.py             # Image processing and bubble detection (OpenCV)
├── templates/            # Jinja2 HTML templates
│   ├── base.html         # Navbar, layout, flash messages
│   ├── home.html         # Dashboard
│   ├── evaluate.html     # Evaluation form and results
│   ├── reports.html      # Reports table and charts
│   ├── login.html        # Login form
│   ├── upload_answer.html# (Optional) Answer key upload page
│   ├── upload_omr.html   # (Optional) OMR upload page
├── uploads/
│   ├── answers/          # Uploaded answer keys
│   ├── omr/              # Uploaded OMR sheets
│   ├── rectified/        # Rectified images (audit)
│   ├── json_results/     # JSON results (audit)
│   └── evaluations.csv   # Main report file
├── static/
│   └── style.css         # Custom styles (optional)
└── README.md             # Project documentation
```

---

## Installation & Setup
1. **Clone the repository**
   ```sh
   git clone https://github.com/aryaanand055/OMR-Evaluator.git
   cd OMR-Evaluator
   ```
2. **Install dependencies**
   ```sh
   pip install flask pandas opencv-python
   ```
3. **Run the application**
   ```sh
   python app.py
   ```
4. **Access the app**
   - Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Usage
- **Login**: Use the default credentials (`admin:1234` or `evaluator:password123`).
- **Dashboard**: View stats and quick links.
- **Upload Answer Key**: Go to Evaluation > Upload New Answer Key.
- **Upload OMR Sheets**: Upload single or multiple sheets for evaluation.
- **Bulk Evaluation**: Select multiple OMR sheets in the evaluation form.
- **View Results**: After evaluation, results are shown and saved to `uploads/evaluations.csv`.
- **Reports**: Filter, search, and export results. View interactive charts.
- **Audit**: Rectified images and JSON results are saved for each evaluation.

---

## Code Highlights
- **app.py**: Flask routes for dashboard, evaluation, reports, authentication, file handling, and CSV/Excel export.
- **omr_utils.py**: Core OMR evaluation logic, random score generation (placeholder), CSV writing.
- **script.py**: OpenCV-based bubble detection and image processing (for advanced OMR extraction).
- **templates/**: Jinja2 templates for all pages, Bootstrap UI, Chart.js graphs.

---

## Customization
- **Subjects**: Edit `SUBJECTS` in `omr_utils.py` to match your exam.
- **Authentication**: Update `USERS` in `app.py` for more users.
- **Styling**: Add custom CSS in `static/style.css`.
- **Image Processing**: Extend `script.py` for advanced OMR logic.

---

## Example Workflow
1. Login as evaluator.
2. Upload answer key for the exam.
3. Upload OMR sheets (single or bulk).
4. Select answer key and OMR sheets, enter student ID (optional), and evaluate.
5. View results and audit files.
6. Go to Reports for analytics, filtering, and export.

---

## Screenshots
> Add screenshots of dashboard, evaluation, and reports pages here.

---

## License
This project is for educational and hackathon use. See [LICENSE](LICENSE) for details.

---

## Contributors
- Arya Anand (@aryaanand055)
- Hackathon 2024 Team

---

## Issues & Support
For bugs or feature requests, open an issue on GitHub.

---

## Acknowledgements
- Flask
- Bootstrap
- pandas
- Chart.js
- OpenCV
