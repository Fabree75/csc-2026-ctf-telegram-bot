import yaml
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.yml"

def load_config():
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {}

def get_live_ips():
    conf = load_config()
    return {
        "VPS_IP": conf.get("VPS_IP", "127.0.0.1"),
        "SERVICE_IP": conf.get("SERVICE_IP", "127.0.0.1")
    }