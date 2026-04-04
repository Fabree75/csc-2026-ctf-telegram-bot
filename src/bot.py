import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from utils import *

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO,
    handlers=[
        logging.FileHandler("ctf_bot_chat.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Commands ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    welcome_text = (
        "🏆 Welcome to the 2026 CTF Bot! 🏆\n\n"
        "Here are the commands you can use:\n"
        "/teams - View available teams\n"
        "/register <team_name> - Specify what team are you in\n"
        "/myteam - View your team's detailed summary\n"
        "/submit <flag> - Submit a flag for points. You can submit the full \"egg{flag_text}\" or just \"flag_text\"\n"
        "/score - View the current scoreboard"
    )
    await update.message.reply_text(welcome_text)

async def teams_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the list of available teams."""
    if not teams:
        await update.message.reply_text("No teams are currently available.")
        return
        
    teams_list = "\n".join([f"· {team}" for team in teams.keys()])
    await update.message.reply_text(f"🏆 Available Teams 🏆\n\n{teams_list}")

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Register a user to a team."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("Usage: /register <team_name>")
        return
        
    team_name = " ".join(context.args).lower()
    
    # Check if user is already on a team
    if user_id in user_to_team:
        await update.message.reply_text(f"You are already registered to the team: {user_to_team[user_id]}.")
        return

    # Check if team is valid
    if team_name not in teams:
        await update.message.reply_text(f"❌ Team '{team_name}' does not exist. Use /teams to see available teams.")
        return
        
    # Check if team is full
    current_members = list(user_to_team.values()).count(team_name)
    if current_members >= 3:
        await update.message.reply_text(f"❌ Team '{team_name}' is already full (maximum 3 participants).")
        return
        
    await update.message.reply_text(f"Joined existing team: '{team_name}'.")
        
    user_to_team[user_id] = team_name

async def myteam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a detailed summary of the user's team."""
    user_id = update.effective_user.id
    
    if user_id not in user_to_team:
        await update.message.reply_text("You need to register your team first using: /register <team_name>")
        return
        
    team_name = user_to_team[user_id]
    team_data = teams[team_name]
    
    score = team_data["score"]
    solved = team_data["solved_challenges"]
    members_count = list(user_to_team.values()).count(team_name)
    
    summary = f"📊 Team Summary: {team_name}\n\n"
    summary += f"👥 Members: {members_count}/3\n"
    summary += f"⭐ Total Score: {score} pts\n"
    summary += f"✅ Solved Challenges ({len(solved)}):\n"
    
    if solved:
        for flag in solved:
            challenge = CHALLENGES[flag]
            summary += f"  - {challenge['name']} ({challenge['points']} pts)\n"
    else:
        summary += "  - None yet. Keep hacking!"
        
    await update.message.reply_text(summary)

async def submit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Submit a flag."""
    user_id = update.effective_user.id
    
    if user_id not in user_to_team:
        await update.message.reply_text("You need to register your team first using: /register <team_name>")
        return
        
    if not context.args:
        await update.message.reply_text("Usage: /submit <flag>\nYou can submit the flag in the format \"egg{flag_text}\" or just \"flag_text\".")
        return
        
    submitted_flag = context.args[0].strip()
    if not submitted_flag.startswith("egg{"):
        submitted_flag = f"egg{{{submitted_flag}}}"
        
    team_name = user_to_team[user_id]
    
    # Check if it's a valid flag
    if submitted_flag in CHALLENGES:
        challenge = CHALLENGES[submitted_flag]
        
        # Check if team already solved this
        if submitted_flag in teams[team_name]["solved_challenges"]:
            await update.message.reply_text(f"❌ Your team '{team_name}' has already solved '{challenge['name']}'!")
        else:
            # Award points
            teams[team_name]["solved_challenges"].append(submitted_flag)
            teams[team_name]["score"] += challenge["points"]
            
            await update.message.reply_text(
                f"✅ Correct! Flag accepted for '{challenge['name']}'.\n"
                f"Your team earned {challenge['points']} points!\n"
                f"Total Score: {teams[team_name]['score']}"
            )
    else:
        await update.message.reply_text("❌ Incorrect flag. Check the spelling or keep hacking!")

async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the scoreboard."""
    if not teams:
        await update.message.reply_text("No teams are currently on the board.")
        return
        
    # Sort teams by score (descending)
    sorted_teams = sorted(teams.items(), key=lambda x: x[1]["score"], reverse=True)
    
    scoreboard = "🏆 CTF SCOREBOARD 🏆\n\n"
    for rank, (team, data) in enumerate(sorted_teams, 1):
        solves = len(data["solved_challenges"])
        score = data["score"]
        scoreboard += f"{rank}. {team} - {score} pts ({solves} solves)\n"
        
    await update.message.reply_text(scoreboard)

async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log every message sent to the bot."""
    if update.message and update.message.text:
        user = update.effective_user
        username = user.username if user.username else "NoUsername"
        logger.info(f"[CHAT LOG] User: {user.id} (@{username}) | Name: {user.first_name} | Message: {update.message.text}")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it the bot's token.
    application = Application.builder().token(TOKEN).build()

    # Log all messages (Group -1 runs before default group 0, so it intercepts everything without blocking other handlers)
    application.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, log_all_messages), group=-1)

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("teams", teams_command))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("myteam", myteam_command))
    application.add_handler(CommandHandler("submit", submit_command))
    application.add_handler(CommandHandler("score", score_command))

    logger.info("Starting CTF Bot...")
    # Run the bot until interrupted
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
