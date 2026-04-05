import json
import uuid
from pathlib import Path

class Team:
    def __init__(self, team_id, name, member_ids, score=0, solved=None, active=None):
        self.team_id = str(team_id) # The unique filename/identifier
        self.name = name           # The display name (can have spaces/emojis)
        self.member_ids = member_ids
        self.score = score
        self.solved_challenges = set(solved) if solved else set()
        self.active_challenges = set(active) if active else set()

    @classmethod
    def load_from_file(cls, file_path):
        """Creates a Team instance from [team_id].json."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # We take the team_id from the filename itself (stem)
        return cls(
            team_id=file_path.stem,
            name=data['name'],
            member_ids=data['member_ids'],
            score=data['score'],
            solved=data['solved_challenges'],
            active=data['active_challenges']
        )

    def save(self, directory):
        """Saves state to [team_id].json."""
        file_path = Path(directory) / f"{self.team_id}.json"
        data = {
            "name": self.name,
            "member_ids": self.member_ids,
            "score": self.score,
            "solved_challenges": list(self.solved_challenges),
            "active_challenges": list(self.active_challenges)
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def solve(self, challenge):
        """
        Updates the team state after a successful solve.
        Returns: (bool, list) -> (Success Status, List of newly unlocked IDs)
        """
        # 1. Prevent double-scoring
        if challenge.id in self.solved_challenges:
            return False, []

        # 2. Move from Active to Solved and add points
        self.solved_challenges.add(challenge.id)
        self.score += challenge.points
        self.active_challenges.discard(challenge.id)

        # 3. Calculate new unlocks
        new_unlocks = []
        for next_id in challenge.unlocks:
            # Only add to active if they haven't already solved it
            if next_id not in self.solved_challenges and next_id not in self.active_challenges:
                self.active_challenges.add(next_id)
                new_unlocks.append(next_id)
                
        return True, new_unlocks