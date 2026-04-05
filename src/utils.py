import os
from pathlib import Path
import uuid

from config_loader import BASE_DIR
from challenges import Challenge
from teams import Team

TEAMS_DIR = BASE_DIR / "teams"
TEAMS_DIR.mkdir(exist_ok=True)

TEAMS = {}      # { "TeamId": TeamObject }
USER_TO_TEAM = {}  # { 12345678: "TeamId" }
CHALLENGES = {} # { "challenge_id": ChallengeObject }

def load_all_challenges():
    # We don't even strictly need 'global' if we use .update() 
    # but it's good practice for clarity.
    global CHALLENGES 
    
    path_to_challenges = BASE_DIR / "challenges"
    
    if not path_to_challenges.exists():
        print(f"Directory not found: {path_to_challenges}")
        return

    # 1. Create a fresh temporary dictionary
    loaded_temp = {}
    for file_path in path_to_challenges.glob("*.json"):
        try:
            new_chall = Challenge(file_path)
            loaded_temp[new_chall.id] = new_chall
        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")

    # 2. CRITICAL STEP: Update the original reference
    CHALLENGES.clear()         # Empty the original global dict
    CHALLENGES.update(loaded_temp) # Fill it with the new data
    
    print(f"Done! {len(CHALLENGES)} challenges are now live.")

def load_all_teams():
    for team_file in TEAMS_DIR.glob("*.json"):
        try:
            team = Team.load_from_file(team_file)
            TEAMS[team.team_id] = team
            
            for uid in team.member_ids:
                USER_TO_TEAM[uid] = team.team_id
                
            print(f"Loaded: {team.name} [ID: {team.team_id}]")
        except Exception as e:
            print(f"Failed to load {team_file.name}: {e}")

def signup_team(team_name, creator_id):
    """
    Creates a new team with a unique ID.
    Returns: (Team object, success_message)
    """
    # 1. Generate a short, unique ID (e.g., 't_a1b2c3d4')
    # We use uuid4 and take the first 8 characters for a clean filename
    unique_id = f"t_{uuid.uuid4().hex[:8]}"
    
    # 2. Initialize the Team object
    # We pass the name, the creator's ID, and any starting challenges
    new_team = Team(
        team_id=unique_id, 
        name=team_name, 
        member_ids=[creator_id],
        score=0
    )
    
    # 3. Unlock initial 'Welcome' challenges if they exist
    # Replace 'welcome_01' with your actual starting challenge ID
    new_team.active_challenges.add("warmup")
    
    # 4. Save to teams/[unique_id].json
    new_team.save(TEAMS_DIR)
    
    return new_team