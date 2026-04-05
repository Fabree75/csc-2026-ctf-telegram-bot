import json
import os
from pathlib import Path

from constants import VPS_IP

class Challenge:
    '''
    Class that initalises a challenge from a given folder path. 
    The folder should contain a challenge.json file and 
    optionally a "files" subfolder with any assets.
    '''

    def __init__(self, json_path: Path):
        self.id = json_path.stem
        # id is the same as challenge name, 
        # but in lowercase and with underscores instead of spaces

        #load challenge data from json
        with open(json_path, 'r') as f:
            data = json.load(f)

        # this is *only* for display  
        self.title = data.get("title", "Untitled") 
        self.description = data.get("description", "No description provided.")
        self.points = data.get("points", 0)
        self.flags = data.get("flags", [])
        self.unlocks = data.get("unlocks", []) # List of IDs
        self.has_files = data.get("has_files", False)

    def format_message(self):
        """Formats the challenge text for Telegram."""
        msg = f"<b>{self.title}</b> ({self.points} pts)\n\n"
        msg += f"<i>{self.description}</i>\n\n"
        if self.has_files:
            # Pointing to the .tar.gz we generate with your shell script
            msg += "📦 <b>Challenge Files:</b>\n"
            
            url = f"http://{VPS_IP}/dist/{self.id}.tar.gz"
            cmd = (
                f"mkdir -p {self.id} && "
                f"curl -L {url} | tar -xz -C {self.id}"
            )
            
            msg += f"<code>{cmd}</code>"
        return msg