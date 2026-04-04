# CTF 2026 Telegram Bot

## Setup Instructions

1. **Install dependencies**:

   **Option A: Using uv (Recommended)**
   If you have `uv` installed, you can simply sync the project using the provided `pyproject.toml`:
   ```bash
   uv sync
   ```

   **Option B: Using standard pip**
   Ensure you have Python installed (version specified in `.python-version` or pyproject.toml). Install the required packages:
   ```bash
   pip install python-telegram-bot
   ```

2. **Configure the Bot Token**:
   - Talk to [@BotFather](https://t.me/BotFather) on Telegram to create a new bot and obtain an API token.
   - Open `src/utils.py` and replace the `TOKEN` variable with your actual bot token.
   - You can also configure the CTF challenges, points, and available teams directly in `src/utils.py`.

3. **Run the Bot**:
   Start the bot by running the following command from the root of the project:
   ```bash
   python src/bot.py
   ```

## Bot Commands
- `/start` - Welcome message and command list
- `/teams` - View available teams to join
- `/register <team_name>` - Join an existing team (max 3 members)
- `/myteam` - View your team's detailed summary and solved challenges
- `/submit <flag>` - Submit a flag for points (format: `egg{flag_text}` or just `flag_text`)
- `/score` - View the current CTF scoreboard
