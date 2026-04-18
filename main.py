"""
Score Impact Analyzer — main.py
================================
Entry point. Parses CLI args, loads config, orchestrates the analysis
pipeline across all specified students, and optionally exports results.

Usage
-----
  python main.py                          # use defaults from .env
  python main.py --student-id abc123
  python main.py --batch --export csv
  python main.py --threshold 0.6 --log-level DEBUG
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from tabulate import tabulate

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv()

# ── Logging setup ─────────────────────────────────────────────────────────────
def setup_logging(level: str, log_file: Optional[str] = None) -> logging.Logger:
    """Configure structured logging with optional file output."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )
    return logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────
class Config:
    MONGO_URI: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME: str = os.environ.get("MONGO_DB_NAME", "sat_analysis")
    MONGO_TIMEOUT_MS: int = int(os.environ.get("MONGO_TIMEOUT_MS", 5000))
    MONGO_MAX_RETRIES: int = int(os.environ.get("MONGO_MAX_RETRIES", 3))
    ADAPTIVE_THRESHOLD: float = float(os.environ.get("ADAPTIVE_THRESHOLD", 0.5))
    DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "./data"))
    SCORING_MODEL_FILE: Path = Path(
        os.environ.get("SCORING_MODEL_FILE", "./scoring_DSAT_v2.json")
    )
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.environ.get("LOG_FILE")
    EXPORT_FORMAT: str = os.environ.get("EXPORT_FORMAT", "none")
    EXPORT_DIR: Path = Path(os.environ.get("EXPORT_DIR", "./reports"))


# ── Privacy helper ────────────────────────────────────────────────────────────
def mask_id(student_id: str) -> str:
    """Return a masked version of a student ID safe for logging.
    
    Examples
    --------
    'abc123'  →  'a***3'
    'x'       →  '*'
    """
    if len(student_id) <= 2:
        return "*" * len(student_id)
    return f"{student_id[0]}***{student_id[-1]}"


# ── MongoDB connection with retry ─────────────────────────────────────────────
def get_db(config: Config, logger: logging.Logger):
    """Return a MongoDB database handle with exponential-backoff retry."""
    for attempt in range(1, config.MONGO_MAX_RETRIES + 1):
        try:
            client = MongoClient(
                config.MONGO_URI,
                serverSelectionTimeoutMS=config.MONGO_TIMEOUT_MS,
            )
            # Force a connection check
            client.admin.command("ping")
            logger.info("Connected to MongoDB (attempt %d/%d)", attempt, config.MONGO_MAX_RETRIES)
            return client[config.MONGO_DB_NAME]
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            wait = 2 ** attempt
            logger.warning(
                "MongoDB connection failed (attempt %d/%d): %s. Retrying in %ds…",
                attempt,
                config.MONGO_MAX_RETRIES,
                exc,
                wait,
            )
            if attempt == config.MONGO_MAX_RETRIES:
                logger.error("All MongoDB connection attempts exhausted. Exiting.")
                sys.exit(1)
            time.sleep(wait)


# ── Data loading ──────────────────────────────────────────────────────────────
def load_data(db, config: Config, logger: logging.Logger) -> None:
    """Load student attempt and scoring model data into MongoDB if not present."""
    attempts_col = db["student_attempts"]
    scoring_col = db["scoring_models"]

    if attempts_col.count_documents({}) == 0:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        json_files = list(config.DATA_DIR.glob("*.json"))
        if not json_files:
            logger.warning(
                "No student attempt JSON files found in %s. "
                "Place anonymized attempt files there and re-run.",
                config.DATA_DIR,
            )
        for fp in json_files:
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    data = [data]
                attempts_col.insert_many(data)
                logger.info("Loaded %d records from %s", len(data), fp.name)
            except (json.JSONDecodeError, ValueError) as exc:
                logger.error("Failed to parse %s: %s", fp.name, exc)
    else:
        logger.info("Student attempts already loaded (%d docs)", attempts_col.count_documents({}))

    if scoring_col.count_documents({}) == 0:
        if not config.SCORING_MODEL_FILE.exists():
            logger.error("Scoring model file not found: %s", config.SCORING_MODEL_FILE)
            sys.exit(1)
        try:
            model_data = json.loads(config.SCORING_MODEL_FILE.read_text(encoding="utf-8"))
            if not isinstance(model_data, list):
                model_data = [model_data]
            scoring_col.insert_many(model_data)
            logger.info("Scoring model loaded (%d entries)", len(model_data))
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse scoring model: %s", exc)
            sys.exit(1)
    else:
        logger.info("Scoring model already loaded.")


# ── Scoring helpers ───────────────────────────────────────────────────────────
def determine_module2_difficulty(
    module1_correct: int, module1_total: int, threshold: float = 0.5
) -> str:
    """Return 'hard' or 'easy' based on Module 1 performance vs threshold."""
    if module1_total == 0:
        return "easy"
    return "hard" if (module1_correct / module1_total) >= threshold else "easy"


def calculate_adaptive_score(
    module1_attempts: list,
    module2_attempts: list,
    scoring_model: list,
    module2_difficulty: str,
) -> int:
    """Return the scaled score given combined attempts and M2 difficulty."""
    all_attempts = module1_attempts + module2_attempts
    raw_score = sum(1 for a in all_attempts if a.get("correct"))
    subject = (
        module1_attempts[0]["subject"]["name"]
        if module1_attempts
        else module2_attempts[0]["subject"]["name"]
    )
    for score_map in scoring_model:
        if score_map.get("key", "").lower() in subject.lower():
            for entry in score_map.get("map", []):
                if entry.get("raw") == raw_score:
                    return entry.get(module2_difficulty, 0)
    return 0


# ── Core analysis ─────────────────────────────────────────────────────────────
def analyze_student(
    student_id: str,
    db,
    scoring_model: list,
    threshold: float,
    logger: logging.Logger,
) -> dict:
    """Run cascade-aware adaptive analysis for one student.

    Returns a dict keyed by subject with ranked impact lists.
    """
    masked = mask_id(student_id)
    attempts = list(db["student_attempts"].find({"student_id": student_id}))
    if not attempts:
        logger.warning("No attempts found for student %s", masked)
        return {}

    results = {}
    subjects = {a["subject"]["name"] for a in attempts}

    for subject in sorted(subjects):
        subj_attempts = [a for a in attempts if a["subject"]["name"] == subject]
        module1 = [a for a in subj_attempts if a.get("section", "").lower() == "static"]
        module2 = [
            a for a in subj_attempts if a.get("section", "").lower() in ("hard", "easy")
        ]

        if not module1 or not module2:
            logger.warning(
                "[%s] %s — missing module data (m1=%d, m2=%d), skipping.",
                masked, subject, len(module1), len(module2),
            )
            continue

        m1_correct = sum(1 for a in module1 if a.get("correct"))
        m1_total = len(module1)
        m2_diff = determine_module2_difficulty(m1_correct, m1_total, threshold)
        current_score = calculate_adaptive_score(module1, module2, scoring_model, m2_diff)

        impact_rows = []
        for i, q in enumerate(module1):
            if q.get("correct"):
                continue
            sim_m1 = [dict(a) for a in module1]
            sim_m1[i]["correct"] = 1
            new_m2_diff = determine_module2_difficulty(m1_correct + 1, m1_total, threshold)
            new_score = calculate_adaptive_score(sim_m1, module2, scoring_model, new_m2_diff)
            delta = new_score - current_score
            impact_rows.append(
                {
                    "question_id": q.get("question_id", "N/A"),
                    "topic": q.get("topic", {}).get("name", "N/A"),
                    "score_increase": delta,
                    "cascade": m2_diff != new_m2_diff,
                    "new_m2_difficulty": new_m2_diff,
                }
            )

        impact_rows.sort(key=lambda x: x["score_increase"], reverse=True)
        results[subject] = {
            "current_score": current_score,
            "module2_difficulty": m2_diff,
            "impact_rows": impact_rows,
        }

    return results


# ── Output helpers ────────────────────────────────────────────────────────────
def print_banner() -> None:
    print("\n" + "═" * 56)
    print("       Score Impact Analyzer — v2.0")
    print("═" * 56 + "\n")


def print_results(student_id: str, results: dict) -> None:
    masked = mask_id(student_id)
    for subject, data in results.items():
        print(f"\n[Student: {masked}]  Subject: {subject}")
        print("─" * 54)
        print(
            f"  Current Score : {data['current_score']}  │  "
            f"Module 2 assigned : {data['module2_difficulty'].upper()}"
        )
        rows = data["impact_rows"][:5]
        if not rows:
            print("  No impactful Module 1 questions found.\n")
            continue
        table_data = []
        for rank, row in enumerate(rows, 1):
            note = (
                f"⚡ M2→{row['new_m2_difficulty'].upper()} (cascade)"
                if row["cascade"]
                else ""
            )
            table_data.append(
                [rank, row["topic"][:34], f"+{row['score_increase']}", note]
            )
        print(
            "\n  Top 5 High-Impact Module 1 Questions\n"
            + tabulate(
                table_data,
                headers=["#", "Topic", "+Points", "Notes"],
                tablefmt="rounded_outline",
                colalign=("center", "left", "center", "left"),
            )
        )
    print()


def export_results(
    student_id: str,
    results: dict,
    export_format: str,
    export_dir: Path,
    logger: logging.Logger,
) -> None:
    """Write results to CSV and/or JSON depending on export_format."""
    if export_format == "none" or not results:
        return
    export_dir.mkdir(parents=True, exist_ok=True)
    safe_id = mask_id(student_id).replace("*", "x")

    if export_format in ("json", "both"):
        out_path = export_dir / f"{safe_id}_results.json"
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        logger.info("Results exported to %s", out_path)

    if export_format in ("csv", "both"):
        out_path = export_dir / f"{safe_id}_results.csv"
        lines = ["student_id,subject,current_score,module2_difficulty,rank,topic,score_increase,cascade"]
        for subject, data in results.items():
            for rank, row in enumerate(data["impact_rows"][:5], 1):
                lines.append(
                    f"{safe_id},{subject},{data['current_score']},"
                    f"{data['module2_difficulty']},{rank},"
                    f"{row['topic']},{row['score_increase']},{row['cascade']}"
                )
        out_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Results exported to %s", out_path)


# ── CLI ───────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="score-impact-analyzer",
        description="Rank Digital SAT questions by score-impact potential.",
    )
    parser.add_argument("--student-id", metavar="ID", help="Analyze a single student by ID")
    parser.add_argument(
        "--batch", action="store_true", help="Analyze all students in the database"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        metavar="FLOAT",
        help="Module 2 routing threshold (0.0–1.0, default from .env or 0.5)",
    )
    parser.add_argument(
        "--export",
        choices=["csv", "json", "both", "none"],
        default=None,
        help="Export format for results",
    )
    parser.add_argument("--output", metavar="DIR", help="Directory for exported reports")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Logging verbosity",
    )
    return parser


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    config = Config()
    args = build_parser().parse_args()

    # CLI overrides .env
    if args.threshold is not None:
        config.ADAPTIVE_THRESHOLD = args.threshold
    if args.export is not None:
        config.EXPORT_FORMAT = args.export
    if args.output is not None:
        config.EXPORT_DIR = Path(args.output)
    if args.log_level is not None:
        config.LOG_LEVEL = args.log_level

    logger = setup_logging(config.LOG_LEVEL, config.LOG_FILE)
    print_banner()

    db = get_db(config, logger)
    load_data(db, config, logger)

    scoring_model = list(db["scoring_models"].find())
    if not scoring_model:
        logger.error("Scoring model is empty. Exiting.")
        sys.exit(1)

    # Determine which students to process
    if args.student_id:
        student_ids = [args.student_id]
    elif args.batch:
        student_ids = db["student_attempts"].distinct("student_id")
        logger.info("Batch mode: found %d unique students.", len(student_ids))
    else:
        # Default: process all students
        student_ids = db["student_attempts"].distinct("student_id")
        if not student_ids:
            logger.warning("No students found. Add data files to %s and re-run.", config.DATA_DIR)
            sys.exit(0)

    for sid in student_ids:
        results = analyze_student(
            sid, db, scoring_model, config.ADAPTIVE_THRESHOLD, logger
        )
        if results:
            print_results(sid, results)
            export_results(
                sid, results, config.EXPORT_FORMAT, config.EXPORT_DIR, logger
            )


if __name__ == "__main__":
    main()
