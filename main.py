import json
from pymongo import MongoClient

# --- Database Setup ---
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['sat_analysis']
    student_attempts_collection = db['student_attempts']
    scoring_models_collection = db['scoring_models']
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

# --- Data Loading ---
def load_data():
    """Loads data from JSON files into MongoDB if the collections are empty."""
    try:
        if student_attempts_collection.count_documents({}) == 0:
            print("Loading student attempts data...")
            with open('67f2aae2c084263d16dbe462user_attempt_v2.json', 'r') as f:
                student_attempts_v2 = json.load(f)
                student_attempts_collection.insert_many(student_attempts_v2)
            with open('66fece285a916f0bb5aea9c5user_attempt_v3.json', 'r') as f:
                student_attempts_v3 = json.load(f)
                student_attempts_collection.insert_many(student_attempts_v3)
            print("Student attempts data loaded successfully.")
        else:
            print("Student attempts data already loaded.")

        if scoring_models_collection.count_documents({}) == 0:
            print("Loading scoring model data...")
            with open('scoring_DSAT_v2.json', 'r') as f:
                scoring_model = json.load(f)
                scoring_models_collection.insert_many(scoring_model)
            print("Scoring model data loaded successfully.")
        else:
            print("Scoring model data already loaded.")
    except Exception as e:
        print(f"Error loading data: {e}")

def calculate_score(attempts, scoring_model):
    """Calculates the student's score based on their attempts."""
    raw_score = sum(1 for attempt in attempts if attempt['correct'])
    
    # Determine if the easy or hard scoring map should be used
    # This is a simplified logic. A real-world scenario might be more complex.
    difficulty_level = "hard" # Assuming 'hard' by default
    
    for score_map in scoring_model:
        if score_map['key'].lower() in attempts[0]['subject']['name'].lower():
            for score in score_map['map']:
                if score['raw'] == raw_score:
                    return score[difficulty_level]
    return 0


def analyze_student_performance(student_id):
    """Analyzes a student's performance to find high-impact questions."""
    try:
        student_attempts = list(student_attempts_collection.find({'student_id': student_id}))
        if not student_attempts:
            print(f"No attempts found for student {student_id}")
            return

        scoring_model_cursor = scoring_models_collection.find()
        scoring_model = list(scoring_model_cursor)
        if not scoring_model:
            print("Scoring model not found.")
            return

        subjects = {attempt['subject']['name'] for attempt in student_attempts}

        for subject in subjects:
            print(f"--- Analyzing {subject} ---")
            
            subject_attempts = [attempt for attempt in student_attempts if attempt['subject']['name'] == subject]
            
            # Calculate current score
            current_score = calculate_score(subject_attempts, scoring_model)
            print(f"Current Score for {subject}: {current_score}")

            incorrect_questions = [q for q in subject_attempts if not q['correct']]
            
            impactful_questions = []

            for question in incorrect_questions:
                # Simulate flipping the answer to correct
                simulated_attempts = subject_attempts.copy()
                for i, attempt in enumerate(simulated_attempts):
                    if attempt['question_id'] == question['question_id']:
                        simulated_attempts[i]['correct'] = 1
                
                new_score = calculate_score(simulated_attempts, scoring_model)
                score_increase = new_score - current_score

                if score_increase > 0:
                    impactful_questions.append({
                        'question_id': question['question_id'],
                        'topic': question.get('topic', {}).get('name', 'N/A'),
                        'score_increase': score_increase
                    })
            
            # Sort questions by impact
            impactful_questions.sort(key=lambda x: x['score_increase'], reverse=True)
            
            print("Top 5 impactful questions:")
            for i, item in enumerate(impactful_questions[:5]):
                print(f"{i+1}. Question ID: {item['question_id']}, Topic: {item['topic']}, Potential Score Increase: {item['score_increase']}")


    except Exception as e:
        print(f"An error occurred during analysis: {e}")

def determine_module2_difficulty(module1_correct, module1_total, threshold=0.5):
    """Determine if Module 2 should be 'hard' or 'easy' based on Module 1 performance."""
    performance = module1_correct / module1_total if module1_total > 0 else 0
    return 'hard' if performance >= threshold else 'easy'


def calculate_adaptive_score(module1_attempts, module2_attempts, scoring_model, module2_difficulty):
    """Calculate the total score based on module attempts and module2 difficulty."""
    # Raw score is sum of correct answers in both modules
    raw_score = sum(1 for a in module1_attempts + module2_attempts if a['correct'])
    subject = module1_attempts[0]['subject']['name'] if module1_attempts else module2_attempts[0]['subject']['name']
    for score_map in scoring_model:
        if score_map['key'].lower() in subject.lower():
            for score in score_map['map']:
                if score['raw'] == raw_score:
                    return score[module2_difficulty]
    return 0


def analyze_student_performance_adaptive(student_id, threshold=0.5):
    """Advanced analysis: considers adaptive/cascade effects for Module 1 questions."""
    try:
        student_attempts = list(student_attempts_collection.find({'student_id': student_id}))
        if not student_attempts:
            print(f"No attempts found for student {student_id}")
            return

        scoring_model_cursor = scoring_models_collection.find()
        scoring_model = list(scoring_model_cursor)
        if not scoring_model:
            print("Scoring model not found.")
            return

        subjects = {attempt['subject']['name'] for attempt in student_attempts}

        for subject in subjects:
            print(f"\n--- Adaptive Analysis for {subject} ---")
            subject_attempts = [a for a in student_attempts if a['subject']['name'] == subject]
            module1 = [a for a in subject_attempts if a.get('section', '').lower() == 'static']
            module2 = [a for a in subject_attempts if a.get('section', '').lower() in ['hard', 'easy']]
            if not module1 or not module2:
                print(f"Insufficient data for {subject} (need both modules)")
                continue

            module1_total = len(module1)
            module1_correct = sum(1 for a in module1 if a['correct'])
            module2_difficulty = determine_module2_difficulty(module1_correct, module1_total, threshold)
            current_score = calculate_adaptive_score(module1, module2, scoring_model, module2_difficulty)
            print(f"Current Score: {current_score} (Module 2: {module2_difficulty})")

            impactful_questions = []
            for i, q in enumerate(module1):
                if q['correct']:
                    continue
                # Simulate flipping this Module 1 question to correct
                simulated_module1 = module1.copy()
                simulated_module1[i] = dict(simulated_module1[i])
                simulated_module1[i]['correct'] = 1
                new_module1_correct = module1_correct + 1
                new_module2_difficulty = determine_module2_difficulty(new_module1_correct, module1_total, threshold)
                # If module2 difficulty changes, need to use the other set of module2 attempts
                simulated_score = calculate_adaptive_score(simulated_module1, module2, scoring_model, new_module2_difficulty)
                score_increase = simulated_score - current_score
                impactful_questions.append({
                    'question_id': q['question_id'],
                    'topic': q.get('topic', {}).get('name', 'N/A'),
                    'score_increase': score_increase,
                    'module2_difficulty_change': module2_difficulty != new_module2_difficulty,
                    'new_module2_difficulty': new_module2_difficulty
                })
            impactful_questions.sort(key=lambda x: x['score_increase'], reverse=True)
            print("Top 5 impactful Module 1 questions (cascade-aware):")
            for i, item in enumerate(impactful_questions[:5]):
                change_str = f" (Module 2 changes to {item['new_module2_difficulty']})" if item['module2_difficulty_change'] else ""
                print(f"{i+1}. QID: {item['question_id']}, Topic: {item['topic']}, Score +{item['score_increase']}{change_str}")
    except Exception as e:
        print(f"An error occurred during adaptive analysis: {e}")

if __name__ == '__main__':
    load_data()
    
    # Example Usage: Use anonymized student IDs
    student_id_1 = "sample_student_1"  # From anonymized user_attempt_v2_anonymized.json
    student_id_2 = "sample_student_2"  # From anonymized user_attempt_v3_anonymized.json
    
    analyze_student_performance(student_id_1)
    analyze_student_performance(student_id_2)
    analyze_student_performance_adaptive(student_id_1)
    analyze_student_performance_adaptive(student_id_2)
