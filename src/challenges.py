import json
import os
from pathlib import Path
from config_loader import get_live_ips

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
        self.has_service = data.get("has_service", False)
        self.service_port = data.get("service_port", None)

    def format_message(self):
        """Formats the challenge text for Telegram."""
        current_ips = get_live_ips()
        vps_ip = current_ips.get("VPS_IP")
        service_ip = current_ips.get("SERVICE_IP")

        msg = f"<b>{self.title}</b> ({self.points} pts)\n\n"
        msg += f"<i>{self.description}</i>\n\n"
        
        # 1. Use SERVICE_IP for netcat connections
        if self.has_service:
            msg += "🌐 <b>Connect:</b>\n"
            msg += f"paste <code>http://{service_ip}:{self.service_port}</code> into your browser\n"
            msg += f"or <code>nc {service_ip} {self.service_port}</code>\n\n"
            

        # 2. Use VPS_IP for file downloads (Nginx)
        if self.has_files:
            file_url = f"http://{vps_ip}/dist/{self.id}.tar.gz"
            msg += "📦 <b>Files:</b>\n"
            # Using the improved folder-naming command
            cmd = f"mkdir -p {self.id} && curl -L {file_url} | tar -xz -C {self.id}"
            msg += f"<code>{cmd}</code>\n"

        return msg