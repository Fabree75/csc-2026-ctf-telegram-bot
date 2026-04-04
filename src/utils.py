#Telegram Bot API Token (!!!KEEP IN SECRET!!!)
TOKEN = ""

# Dictionary of flags (eggs) mapped to their challenge name and points
CHALLENGES : dict[str, dict[str, str | int]] = {
    "egg{example_flag1}": {"name": "Sanity Check", "points": 10},
    "egg{example_flag2}": {"name": "Crypto Basics", "points": 50},
}

# Maps team_name -> {"score": int, "solved_challenges": list}
teams : dict[str, dict[str, int | list[str]]] = {
    "name1" : {"score" : 0, "solved_challenges": []},
    "name2" : {"score" : 0, "solved_challenges": []}
}
# Maps user_id -> team_name
user_to_team = {}