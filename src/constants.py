import os
from pathlib import Path

#Telegram Bot API Token (!!!KEEP IN SECRET!!!)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BASE_DIR = Path(__file__).parent.parent

VPS_IP = os.getenv("VPS_IP", "localhost") # For file download instructions