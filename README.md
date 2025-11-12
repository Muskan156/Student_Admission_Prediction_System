# 🎓 Student Admission Prediction System (Flask + Machine Learning)

![Python](https://img.shields.io/badge/Built%20With-Python-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Framework-Flask-000000?logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/Database-MySQL-4479A1?logo=mysql&logoColor=white)
![Status](https://img.shields.io/badge/Status-Deployed-brightgreen)

A machine learning–powered web application that predicts students' chances of admission into various colleges based on their academic performance, percentile, and category.  
The system also checks eligibility, provides a list of predicted colleges, and allows students to save and download their preferred choices.

---

## 🔗 Live Demo

▶️ [Try the App on Render](https://student-admission-prediction-system-1.onrender.com/)

---

## 📌 Features

- **User Module**
  - Register, login, and manage student profiles  
  - Check eligibility and predict admission chances  
  - Save and download preferred college lists (PDF format)

- **Admin Module**
  - Manage admission timelines and view student statistics  
  - Edit or delete existing data entries  
  - Monitor student preferences and trends  

- **Machine Learning Integration**
  - Predicts admission probability using trained ML model  
  - Uses Random Forest Regressor trained with `scikit-learn`  
  - Custom prediction logic via `predict_model.py`

- **Responsive Web Interface**
  - Fully mobile-friendly layout  
  - Dynamic navigation bar with hamburger menu  
  - Clean modern UI built with HTML, CSS, and JavaScript  

---

## 🌐 Tech Stack
* Python
* Flask
* HTML,CSS,JS
* Pandas, Numpy, scikit-learn
* MySQL

---

## 🧠 Model Highlights

- Algorithm: **Random Forest Regressor**  
- Evaluation Matrix:
  - Accuracy:68.06%
  - Recall:67.22% 
  - Precision:67.89%
  - F1-Score:67.55%

---

## 📊 Dataset

The dataset used for this project was **manually created** by extracting **CAP Round-wise cutoff data for three academic years — 2023, 2024, and 2025** for **engineering colleges within Sangli district**, Maharashtra.This data was collected from the **official CET CELL (CAP Round) reports** and preprocessed into a clean CSV format used to train the prediction model.
Each record contains details such as:
- **Institute Code**
- **Institute Name**
- **Department / Branch**
- **Category (OPEN, OBC, SC, ST, EWS, etc.)**
- **Academic Year**
- **CAP Round 1 / 2 / 3**

---

## 🚀 How to Run Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/Muskan156/Student_Admission_Prediction_System.git
   cd Student_Admission_Prediction_System
2. **Create Virtual Environment**
    ```bash
   python -m venv venv
    venv\Scripts\activate        # Windows
    source venv/bin/activate
3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
4. **Set up your .env file**
   ```bash
   SECRET_KEY=mysecretkey
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DB=admission_db
   MYSQL_CURSORCLASS=DictCursor
5. **Run the Flask app**
   ```bash
   python app.py
Visit 👉 http://127.0.0.1:5000

---

## 🗂️ File Structure
 ```bash
.
├── app.py                     # Main Flask application
├── requirements.txt            # Dependencies
├── runtime.txt                 # Python version for Render
├── .env                        # Environment variables (local)
│
├── ml_models/
│   ├── train_model.py          # Train logistic regression model
│   └── predict_model.py        # Predict admission outcomes
│
├── templates/
│   ├── index.html              # Homepage
│   ├── predictor.html          # Eligibility & prediction form
│   ├── predicted_colleges.html # Predicted results
│   ├── my_list.html            # Student saved list
│   ├── admission_info.html     # Admission guidelines
│   ├── login.html / register.html
│
├── static/
│   ├── css/style.css           # Styling & responsive layout
│   └── assets/background1.jpg  # Banner image
│
└── README.md
