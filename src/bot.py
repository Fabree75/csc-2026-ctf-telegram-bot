import logging
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config_loader import load_config
from utils import * # Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO,
    handlers=[
        logging.FileHandler("ctf_bot_chat.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Helper Logic ---

def get_team(user_id):
    """Helper to get the Team object for a specific user ID."""
    team_id = USER_TO_TEAM.get(user_id)
    if team_id:
        return TEAMS.get(team_id)
    return None

# --- Commands ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        "<b>🏆 Welcome to the 2026 CTF Bot! 🏆</b>\n\n"
        "Here are the commands you can use:\n"
        "/teams - View registered teams\n"
        "/signup - Create a new team\n"
        "/join - Join an existing team\n"
        "/challenges - View your currently unlocked challenges\n"
        "/myteam - View your team's progress\n"
        "/submit - Submit a flag for points\n"
        "/score - View the global scoreboard"
    )
    await update.message.reply_text(welcome_text, parse_mode='HTML')

async def teams_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the list of available teams with their IDs for joining."""
    if not TEAMS:
        await update.message.reply_text("No teams are currently available.")
        return
        
    teams_list = "<b>🏆 Available Teams 🏆</b>\n\n"
    teams_list += "To join a team, use: <code>/join &lt;team_id&gt;</code>\n\n"
    
    for team_id, team in TEAMS.items():
        # HTML is safe for IDs with underscores
        teams_list += f"• <b>{team.name}</b>\n  ID: <code>{team_id}</code>\n"
        teams_list += f"  Members: {len(team.member_ids)}/3\n\n"
        
    await update.message.reply_text(teams_list, parse_mode='HTML')

async def signup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Register a new team."""
    user_id = update.effective_user.id
    
    if user_id in USER_TO_TEAM:
        await update.message.reply_text("❌ You are already in a team! Use /myteam to see details.")
        return

    if not context.args:
        await update.message.reply_text("Usage: <code>/signup &lt;team_name&gt;</code>", parse_mode='HTML')
        return

    team_name = " ".join(context.args)
    new_team = signup_team(team_name, user_id)
    
    TEAMS[new_team.team_id] = new_team
    USER_TO_TEAM[user_id] = new_team.team_id
    
    response = (
        f"🎉 <b>Team '{team_name}' created successfully!</b>\n\n"
        f"🆔 Your Team ID is: <code>{new_team.team_id}</code>\n"
        f"Share this ID with up to 2 friends so they can <code>/join</code> you!"
    )
    await update.message.reply_text(response, parse_mode='HTML')

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allow a user to join a team using its ID."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("Usage: <code>/join &lt;team_id&gt;</code>\nExample: <code>/join team_1_a7b2c9</code>", parse_mode='HTML')
        return
        
    target_id = context.args[0].strip()
    
    if user_id in USER_TO_TEAM:
        current_team_id = USER_TO_TEAM[user_id]
        current_team = TEAMS.get(current_team_id)
        await update.message.reply_text(f"You are already in team: <b>{current_team.name}</b>.", parse_mode='HTML')
        return

    if target_id not in TEAMS:
        await update.message.reply_text("❌ Invalid Team ID. Use /teams to find the correct ID.")
        return
        
    team = TEAMS[target_id]
    
    if len(team.member_ids) >= 3:
        await update.message.reply_text(f"❌ Team <b>{team.name}</b> is already full (max 3 players).", parse_mode='HTML')
        return
        
    team.member_ids.append(user_id)
    USER_TO_TEAM[user_id] = target_id
    team.save(TEAMS_DIR)
    
    await update.message.reply_text(
        f"✅ Success! You have joined <b>{team.name}</b>.\n"
        "Use /challenges to see your current tasks.", 
        parse_mode='HTML'
    )

async def challenges_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays challenges currently unlocked for the user's team."""
    team = get_team(update.effective_user.id)
    if not team:
        await update.message.reply_text("You aren't on a team yet!")
        return

    if not team.active_challenges:
        await update.message.reply_text("You have no active challenges.")
        return

    response = "<b>🎯 Your Active Challenges 🎯</b>\n\n"

    for chall_id in team.active_challenges:
        challenge = CHALLENGES.get(chall_id)
        if challenge:
            response += f"--- \n{challenge.format_message()}\n\n"
    
    await update.message.reply_text(response, parse_mode='HTML')

async def myteam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    team = get_team(update.effective_user.id)
    if not team:
        await update.message.reply_text("You need to be registered to a team first.")
        return
    
    summary = (
        f"📊 <b>Team Summary: {team.name}</b>\n"
        f"🆔 ID: <code>{team.team_id}</code>\n"
        f"⭐ Total Score: {team.score} pts\n"
        f"✅ Solved: {len(team.solved_challenges)}\n"
        f"🔓 Active: {len(team.active_challenges)}"
    )
    await update.message.reply_text(summary, parse_mode='HTML')

async def submit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args and context.args[0].strip().lower() == "ctf{egg_hunt}":
        msg = "🥚 Secret Easter Egg accepted! 🥚\n\n"
        msg += "For one of the prizes last year, we\n"
        msg += "ordered a proxmark off amazon\n"
        msg += "yet we haven't had many occasions to use it\n"
        msg += "even so we really wanted to make a\n"
        msg += "riddle out of it."
        await update.message.reply_text(msg)
        return
    
    team = get_team(update.effective_user.id)
    if not team:
        await update.message.reply_text("Register to a team first!")
        return
        
    if not context.args:
        await update.message.reply_text("Usage: <code>/submit &lt;flag&gt;</code>", parse_mode='HTML')
        return

    submitted_flag = context.args[0].strip()

    for chall_id in list(team.active_challenges):
        challenge = CHALLENGES.get(chall_id)
        if challenge and submitted_flag in challenge.flags:
            success, new_unlocks = team.solve(challenge)
            if success:
                team.save(TEAMS_DIR)
                
                response = f"✨ <b>CORRECT!</b>\nPoints earned: {challenge.points}\nTotal Score: {team.score}\n\n"
                
                if new_unlocks:
                    response += "🔓 <b>New challenges have been unlocked!</b>\n\n"
                
                response += "🚀 <b>Your Available Challenges:</b>\n"
                for active_id in team.active_challenges:
                    c = CHALLENGES.get(active_id)
                    if c:
                        response += f"--- \n{c.format_message()}\n\n"
                
                await update.message.reply_text(response, parse_mode='HTML')
                return

    await update.message.reply_text("❌ Incorrect flag or challenge already solved.")

async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not TEAMS:
        await update.message.reply_text("The scoreboard is empty.")
        return
    
    sorted_teams = sorted(TEAMS.values(), key=lambda x: x.score, reverse=True)
    
    scoreboard = "<b>🏆 CTF SCOREBOARD 🏆</b>\n\n"
    for rank, team in enumerate(sorted_teams, 1):
        scoreboard += f"{rank}. <b>{team.name}</b> - {team.score} pts\n"
        
    await update.message.reply_text(scoreboard, parse_mode='HTML')

async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        user = update.effective_user
        logger.info(f"[CHAT] {user.id} (@{user.username}): {update.message.text}")

# --- Main ---

def main() -> None:
    config = load_config()
    token = config.get("BOT_TOKEN")

    if not token:
        print("❌ No BOT_TOKEN found in config.yml. Exiting.")
        return
    
    load_all_teams()
    load_all_challenges()
    
    application = Application.builder().token(token).build()

    application.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, log_all_messages), group=-1)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("teams", teams_command))
    application.add_handler(CommandHandler("signup", signup_command))
    application.add_handler(CommandHandler("join", join_command))
    application.add_handler(CommandHandler("challenges", challenges_command))
    application.add_handler(CommandHandler("myteam", myteam_command))
    application.add_handler(CommandHandler("submit", submit_command))
    application.add_handler(CommandHandler("score", score_command))

    logger.info("Bot is polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()