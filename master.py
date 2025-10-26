from bot_scripts.realtime import start_conver_and_get_transcript
from scoring_scripts import get_conver_skills, get_conver_scores

def main():
    # Step 1: Get transcript
    transcript = start_conver_and_get_transcript()
    print("Transcript:", transcript)

    # Step 2: Analyze skills
    skills = get_conver_skills.get_conver_skills(transcript)
    print("Skills:", skills)

    # Step 3: Compute scores
    scores = get_conver_scores.get_conver_scores(transcript)
    print("Scores:", scores)

if __name__ == "__main__":
    main()