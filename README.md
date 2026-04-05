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
   First set the configs in `config.yml`.
   Then, in the same shell, start the bot by running the following command from the root of the project:
   ```bash
   python src/bot.py
   ```

## Bot Commands

* **/start**
    Displays the welcome message and this command list.

* **/teams**
    View all available teams. This shows the **Team Name**, current **Member Count**, and the unique **Team ID** required to join.

* **/join `<team_id>`**
    Join a team using its unique identifier.
    *Example:* `/join team_1_a7b2c9`
    > **Note:** Teams are limited to 3 members. You cannot join a team if you are already registered in one.

* **/challenges**
    List all currently **unlocked** challenges for your team. This includes:
    * Challenge descriptions and point values.
    * `curl` commands to download files directly into organized folders.

* **/myteam**
    View your team's private summary, including total score and a list of solved challenges.

* **/submit `<flag>`**
    Submit a flag for points. The bot automatically checks your input against all of your team's active challenges.
    *Example:* `/submit egg{flag_text}` or `/submit flag_text`

* **/score**
    View the global live scoreboard to see current rankings.
