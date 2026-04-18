<div align="center">

<img src="https://img.shields.io/badge/Score%20Impact%20Analyzer-v2.0-6C63FF?style=for-the-badge&logoColor=white" alt="Score Impact Analyzer"/>

# 🎯 Score Impact Analyzer

### *Pinpoint the exact questions that move the needle — before the next test.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.x-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Hardened-red?style=flat-square&logo=shield)](SECURITY.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP8-blue?style=flat-square)](https://peps.python.org/pep-0008/)

<br/>

> **Stop studying everything. Start studying what matters.**
> 
> Score Impact Analyzer uses the official Digital SAT adaptive scoring model to simulate every "what if I had answered this correctly?" scenario — and ranks the results. In seconds, you know exactly which questions were worth the most points.

<br/>

---

</div>

## 📋 Table of Contents

- [Why This Tool](#-why-this-tool)
- [How It Works](#-how-it-works)
- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Output Example](#-output-example)
- [Security & Privacy](#-security--privacy)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 💡 Why This Tool

The Digital SAT is **adaptive**: Module 1 performance determines whether a student gets the *easy* or *hard* Module 2 — and that single routing decision can swing the final score by **60+ points**. Standard practice tools ignore this cascade effect entirely.

Score Impact Analyzer doesn't. It models the full adaptive pipeline so tutors and students can identify not just which questions a student missed, but which misses had **systemic, score-multiplying consequences**.

---

## ⚙️ How It Works

```
Student Attempt Data  ──►  Module 1 Analysis  ──►  Cascade Simulation
        │                                                  │
        │              ┌────────────────────────────────── │
        │              │  For each incorrect answer:       │
        ▼              │  1. Flip to correct               │
  Scoring Model        │  2. Recalculate M2 routing        │
  (DSAT v2 JSON)       │  3. Recompute scaled score        │
        │              │  4. Record Δscore                 │
        └──────────────┴──► Ranked Impact List ──► Output
```

---

## ✨ Features

### Core Analysis
| Feature | Description |
|---|---|
| 📊 **Score Simulation** | Simulates score changes for every missed question |
| 🔀 **Cascade Detection** | Identifies Module 1 misses that would change Module 2 routing |
| 🏆 **Impact Ranking** | Ranks questions by score-point upside |
| 📚 **Dual-Subject Analysis** | Separate pipelines for Math and Reading & Writing |
| 🎯 **Topic Clustering** | Groups high-impact questions by skill/topic |

### Enhanced (v2.0)
| Feature | Description |
|---|---|
| 📄 **Report Export** | Save results as CSV or JSON for further analysis |
| 🔒 **Secure Config** | Environment-variable based secrets (no hardcoded credentials) |
| 🔁 **Retry Logic** | Exponential backoff for MongoDB connection failures |
| 🧪 **Input Validation** | Schema-validated JSON loading with descriptive errors |
| 🛡️ **Privacy-Safe Logging** | Student IDs are never logged in plaintext |
| 📈 **Batch Processing** | Analyze multiple students in a single run |
| ⚙️ **Configurable Thresholds** | Adjust adaptive routing thresholds without touching code |
| 📝 **Structured Logging** | JSON-formatted logs with severity levels |

---

## 🏗️ Architecture

```
score-impact-analyzer/
│
├── main.py                  # Entry point — orchestrates analysis pipeline
├── config.py                # Centralised config (env vars + defaults)
├── analyzer/
│   ├── __init__.py
│   ├── adaptive.py          # Adaptive/cascade scoring logic
│   ├── scorer.py            # Raw → scaled score lookup
│   └── reporter.py          # CSV / JSON export
├── db/
│   ├── __init__.py
│   └── mongo_client.py      # Connection pooling + retry logic
├── utils/
│   ├── __init__.py
│   ├── logger.py            # Structured logging setup
│   └── validators.py        # JSON schema validation
│
├── data/                    # (gitignored) — student attempt files go here
├── scoring_DSAT_v2.json     # Official DSAT scoring model
│
├── requirements.txt         # Pinned dependencies
├── .env.example             # Environment variable template
├── .gitignore               # Protects secrets and data files
├── SECURITY.md              # Vulnerability reporting & security practices
└── README.md                # You are here
```

---

## 🚀 Installation

### Prerequisites

- Python **3.8+**
- MongoDB **6.0+** (local or Atlas)
- `pip` or `pipenv`

### Step-by-step

```bash
# 1. Clone
git clone https://github.com/your-username/score-impact-analyzer.git
cd score-impact-analyzer

# 2. Create a virtual environment (strongly recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
#    → Edit .env with your MongoDB URI and any custom settings
```

---

## 🔧 Configuration

All settings are loaded from environment variables. Copy `.env.example` to `.env` and fill in your values:

```env
# .env.example — copy to .env, never commit .env to git

MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=sat_analysis

# Adaptive routing threshold (0.0 – 1.0, default 0.5)
ADAPTIVE_THRESHOLD=0.5

# Path to student attempt data directory
DATA_DIR=./data

# Log level: DEBUG | INFO | WARNING | ERROR
LOG_LEVEL=INFO

# Export format: csv | json | both | none
EXPORT_FORMAT=csv
EXPORT_DIR=./reports
```

> ⚠️ **Never commit your `.env` file.** It is already in `.gitignore`.

---

## 📖 Usage

### Basic run

```bash
python main.py
```

### Analyze a specific student

```bash
python main.py --student-id <your_student_id>
```

### Batch mode (all students in data/)

```bash
python main.py --batch
```

### Export results

```bash
python main.py --batch --export csv --output ./reports
```

### Adjust adaptive threshold

```bash
python main.py --threshold 0.6
```

### All options

```
usage: main.py [-h] [--student-id ID] [--batch] [--threshold FLOAT]
               [--export {csv,json,both,none}] [--output DIR] [--log-level LEVEL]

optional arguments:
  --student-id ID       Analyze a single student by ID
  --batch               Analyze all student files in DATA_DIR
  --threshold FLOAT     Module 2 routing threshold (default: 0.5)
  --export FORMAT       Export results (csv | json | both | none)
  --output DIR          Directory for exported reports
  --log-level LEVEL     Logging verbosity (DEBUG | INFO | WARNING | ERROR)
```

---

## 🖥️ Output Example

```
╔══════════════════════════════════════════════════════╗
║          Score Impact Analyzer — v2.0                ║
╚══════════════════════════════════════════════════════╝

[Student: s***1]  Subject: Reading & Writing
──────────────────────────────────────────────────────
Current Score : 650  │  Module 2 assigned : HARD

  Top 5 High-Impact Module 1 Questions
  ┌─────┬──────────────────────────────────┬──────────┬──────────────────────┐
  │  #  │ Topic                            │ +Points  │ Notes                │
  ├─────┼──────────────────────────────────┼──────────┼──────────────────────┤
  │  1  │ Text structure and purpose       │  +20     │                      │
  │  2  │ Text structure and purpose       │  +20     │                      │
  │  3  │ Command of evidence (textual)    │  +10     │                      │
  │  4  │ Words in context                 │  +10     │                      │
  │  5  │ Inferences                       │  +10     │                      │
  └─────┴──────────────────────────────────┴──────────┴──────────────────────┘

[Student: s***1]  Subject: Math
──────────────────────────────────────────────────────
Current Score : 520  │  Module 2 assigned : EASY

  Top 5 High-Impact Module 1 Questions
  ┌─────┬──────────────────────────────────┬──────────┬──────────────────────┐
  │  #  │ Topic                            │ +Points  │ Notes                │
  ├─────┼──────────────────────────────────┼──────────┼──────────────────────┤
  │  1  │ Advanced Math                    │  +60     │ ⚡ M2→HARD (cascade) │
  │  2  │ Nonlinear functions              │  +20     │                      │
  │  3  │ Linear equations (one var.)      │  +10     │                      │
  │  4  │ Systems of equations             │  +10     │                      │
  │  5  │ Ratios, rates & proportions      │  +10     │                      │
  └─────┴──────────────────────────────────┴──────────┴──────────────────────┘
```

---

## 🔒 Security & Privacy

This project handles **sensitive educational data**. The following safeguards are built in:

- **No hardcoded credentials** — all secrets via environment variables
- **Data directory is gitignored** — student attempt files never reach version control
- **Student IDs are masked** in all log output (`s***1`, not the raw ID)
- **Input validation** — all JSON files are schema-validated before being inserted into MongoDB
- **MongoDB connection** uses a connection pool with configurable timeouts, not a raw persistent socket
- **No telemetry** — this tool makes zero outbound network calls except to your own MongoDB instance

For vulnerability reporting, see [SECURITY.md](SECURITY.md).

---

## 🗺️ Roadmap

- [ ] **Web dashboard** — Flask/FastAPI UI for non-technical tutors
- [ ] **Module 2 analysis** — extend impact ranking to Module 2 questions
- [ ] **Topic heatmaps** — visual breakdown of skill gaps
- [ ] **Multi-test trend** — track score trajectory across multiple practice tests
- [ ] **PDF report generation** — shareable one-page student summaries
- [ ] **MongoDB Atlas support** — plug-and-play cloud deployment

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

```bash
# Fork → clone → branch → change → test → PR
git checkout -b feature/your-feature-name
```

Please make sure your code passes `flake8` and includes appropriate tests.

---

## 📄 License

[MIT](LICENSE) © 2025 — Score Impact Analyzer contributors

---

<div align="center">

**Built for students. Powered by data. Designed for impact.**

⭐ Star this repo if it helps your students!

</div>
