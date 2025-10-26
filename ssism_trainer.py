# ssism_trainer.py
"""
SS'ISM Mahārbote Baydin Trainer (SS'ISM-MB-Trainer)
Purpose: Trainer and Paññā Truth Validator for SS'ISM V14 core logic.
"""
import random
from datetime import datetime, timedelta
from ssism_v14_baydin import create_immutable_lock, MAHARBOTE_MAP, WEDNESDAY_AM_SIGN, WEDNESDAY_PM_SIGN

def generate_random_challenge() -> Tuple[int, int, int, int, int]:
    """Generates a random date and time for testing."""
    start_date = datetime(1950, 1, 1)
    end_date = datetime(2050, 12, 31)
    
    time_between_dates = end_date - start_date
    random_number_of_days = random.randrange(time_between_dates.days)
    random_date = start_date + timedelta(days=random_number_of_days)
    
    # Random hour/minute for boundary testing
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    
    return random_date.year, random_date.month, random_date.day, hour, minute

def get_sign_list():
    """Returns a combined list of all possible Mahārbote signs for user choice."""
    signs = list(MAHARBOTE_MAP.values())
    signs.extend([WEDNESDAY_AM_SIGN, WEDNESDAY_PM_SIGN])
    return [s.split('(')[0].strip() for s in signs] # Clean up for simpler user input


def run_training_session():
    """Executes a single training session."""
    print("\n--- SS'ISM-MB-Trainer: Sīla-Samādhi Challenge ---")
    
    # 1. Generate Challenge
    y, m, d, h, mi = generate_random_challenge()
    challenge_date_time = datetime(y, m, d, h, mi).strftime("%Y-%m-%d %H:%M")
    
    print(f"\nYour Challenge Date (Gregorian Input): {challenge_date_time}")
    print("Task: Predict the final Baydin Day and Mahārbote Sign based on the 06:00 boundary rule.")

    # 2. User Input (Simulated Rule-Based Guess)
    try:
        user_day = input("Your Predicted Baydin Day (e.g., Tuesday): ").strip()
        user_sign = input("Your Predicted Mahārbote Sign (e.g., Lion): ").strip()
    except EOFError:
        print("\nTraining session ended.")
        return

    # 3. Paññā Truth Validation (The Core Engine)
    try:
        truth_lock = create_immutable_lock(y, m, d, h, mi)
        
        # Clean the truth for comparison (e.g., remove the '(Sīha)' for simpler comparison)
        truth_sign_clean = truth_lock['maharbote_sign'].split('(')[0].strip()
        truth_day = truth_lock['baydin_day']
        
        # Comparison (The Samādhi Score)
        day_match = (user_day.lower() == truth_day.lower())
        sign_match = (user_sign.lower() == truth_sign_clean.lower())

        print("\n--- Trainer Feedback ---")
        if day_match and sign_match:
            print("✅ **PERFECT MATCH!** Sīla-Samādhi Certified. Your prediction is 100% precise.")
        else:
            print("❌ **MISMATCH DETECTED.** Review the Mahārbote boundary rules.")
            print(f"Your Guess: Day={user_day}, Sign={user_sign}")
            print(f"SS'ISM V14 Truth (Locked): Day={truth_day}, Sign={truth_lock['maharbote_sign']}")

            # Provide detailed explanation for educational value (The A' Directive)
            if not day_match and not sign_match:
                print(f"Reasoning Tip: The Baydin day for {challenge_date_time} starts at 06:00. The V14 core determined the Baydin day based on the hour ({h}).")
            elif not day_match:
                print("Reasoning Tip: Check the 06:00 boundary. Your Day is incorrect, which affects the sign.")
            elif not sign_match:
                if truth_day == "Wednesday" and truth_sign_clean != user_sign.lower():
                    print("Reasoning Tip: Check the Wednesday AM (Tusked Elephant) vs PM (Elephant) rule. The split is at 12:00 local time.")
                else:
                    print("Reasoning Tip: Check your basic day-to-sign Mahārbote mapping.")
                    
        # Verification of the internal lock integrity
        is_valid, msg = verify_immutable_lock(truth_lock)
        print(f"\nSS'ISM Internal Lock Integrity: {'✅ PASS' if is_valid else '❌ FAIL'} - {msg}")

    except Exception as e:
        print(f"An internal error occurred during validation: {e}")
        
if __name__ == "__main__":
    while True:
        run_training_session()
        cont = input("\nRun another session? (y/n): ").strip().lower()
        if cont != 'y':
            break

