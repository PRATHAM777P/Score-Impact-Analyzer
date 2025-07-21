# 🚀 Score Impact Analyzer

---

> **Empower students to focus on the questions that matter most!**

---

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![MongoDB](https://img.shields.io/badge/MongoDB-%20Required-brightgreen?logo=mongodb)

---

## 🎯 Overview

**Score Impact Analyzer** is a smart tool for analyzing SAT/DSAT diagnostic test results. It identifies which questions in both English and Math would have contributed most to a student's score improvement, using official scoring models and adaptive test logic. Perfect for targeted study and actionable feedback!

---

## ✨ Features

- 📊 **Data-Driven Insights:** Simulates score changes based on real student attempt data and official scoring models.
- 🏆 **Impact Ranking:** Ranks questions by their potential to improve the student's overall score.
- 📚 **Subject-Specific Analysis:** Separate analysis for Math and Reading & Writing.
- 🧠 **Adaptive/Cascade What-If Analysis:** Models the DSAT's adaptive module structure, showing how flipping Module 1 answers can change Module 2 assignment (easy/hard) and cause large score jumps.
- ⚙️ **Configurable Threshold:** Easily adjust the threshold for switching from "easy" to "hard" Module 2 (default: 50% correct in Module 1).
- 🗄️ **MongoDB Integration:** Uses MongoDB to store and manage student results and scoring data.

---

## ⚡ Quick Start

1. **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd score-impact-analyzer
    ```
2. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
3. **Start MongoDB**
    - Make sure your MongoDB server is running on its default port (`27017`).
4. **Run the Analyzer**
    ```bash
    python main.py
    ```

---

## 📁 Data Files

- `scoring_DSAT_v2.json` — SAT scoring model
- `67f2aae2c084263d16dbe462user_attempt_v2.json` — Student 1 (anonymized)
- `66fece285a916f0bb5aea9c5user_attempt_v3.json` — Student 2 (anonymized)

---

## 🛠️ Usage

- The script will:
  - Connect to MongoDB and load the data
  - For each student, output:
    - The current score for each subject and the current Module 2 assignment (easy/hard)
    - A ranked list of the top five Module 1 questions that would have provided the most significant score increase if answered correctly, including whether flipping the answer would change the Module 2 assignment (cascade effect)

---

## 🎬 Demo Output

```shell
--- Adaptive Analysis for Reading and Writing ---
Current Score: 650 (Module 2: hard)
Top 5 impactful Module 1 questions (cascade-aware):
1. QID: 659041da1d3470ce13e94642, Topic: Text structure and purpose, Score +20
2. QID: 659040581d3470ce13e94610, Topic: Text structure and purpose, Score +20
...

--- Adaptive Analysis for Math ---
Current Score: 520 (Module 2: easy)
Top 5 impactful Module 1 questions (cascade-aware):
1. QID: 659043271d3470ce13e94679, Topic: Advanced Math, Score +60 (Module 2 changes to hard)
2. QID: 659e991004e80b72d57ac8c2, Topic: Nonlinear functions, Score +20
...
```

---

## ⚙️ Advanced Configuration

- Adjust the adaptive threshold in the code (`main.py`, default is 0.5, or 50% correct in Module 1).
- Ready to analyze both a high-performing and a regular student.

---

## 💡 Extensions

- Analyze Module 2 questions
- Cluster by topic for targeted recommendations
- Run multiple what-if scenarios

---
