import logging
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config_loader import load_config
from utils import * # This should now include your Challenge and Team class definitions


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
        "🏆 Welcome to the 2026 CTF Bot! 🏆\n\n"
        "Here are the commands you can use:\n"
        "/teams - View registered teams\n"
        "/signup <team_name> - Create a new team\n"
        "/join <team_id> - Join an existing team\n"
        "/challenges - View your currently unlocked challenges\n"
        "/myteam - View your team's progress\n"
        "/submit <flag> - Submit a flag for points\n"
        "/score - View the global scoreboard"
    )
    await update.message.reply_text(welcome_text)

async def teams_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the list of available teams with their IDs for joining."""
    if not TEAMS:
        await update.message.reply_text("No teams are currently available.")
        return
        
    teams_list = "🏆 **Available Teams** 🏆\n\n"
    teams_list += "To join a team, use: `/join <team_id>`\n\n"
    
    for team_id, team in TEAMS.items():
        # Display the Name and the ID (which is the filename stem)
        teams_list += f"• **{team.name}**\n  ID: ` {team_id} `\n"
        teams_list += f"  Members: {len(team.member_ids)}/3\n\n"
        
    await update.message.reply_text(teams_list, parse_mode='Markdown')

async def signup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Register a new team."""
    user_id = update.effective_user.id
    
    # 1. Check if user is already in a team
    if user_id in USER_TO_TEAM:
        await update.message.reply_text("❌ You are already in a team! Use /myteam to see details.")
        return

    # 2. Ensure they provided a name
    if not context.args:
        await update.message.reply_text("Usage: `/signup <team_name>`", parse_mode='Markdown')
        return

    team_name = " ".join(context.args)
    
    # 3. Create the team using the logic from utils.py
    new_team = signup_team(team_name, user_id)
    
    # 4. Update the global RAM lookups
    TEAMS[new_team.team_id] = new_team
    USER_TO_TEAM[user_id] = new_team.team_id
    
    response = (
        f"🎉 **Team '{team_name}' created successfully!**\n\n"
        f"🆔 Your Team ID is: `{new_team.team_id}`\n"
        f"Share this ID with up to 2 friends so they can `/join` you!"
    )
    await update.message.reply_text(response, parse_mode='Markdown')

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allow a user to join a team using its ID."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("Usage: `/join <team_id>`\nExample: `/join team_1_a7b2c9`", parse_mode='Markdown')
        return
        
    target_id = context.args[0].strip()
    
    # 1. Check if user is already on a team
    if user_id in USER_TO_TEAM:
        current_team_id = USER_TO_TEAM[user_id]
        current_team = TEAMS.get(current_team_id)
        await update.message.reply_text(f"You are already in team: **{current_team.name}**.", parse_mode='Markdown')
        return

    # 2. Check if the team ID exists
    if target_id not in TEAMS:
        await update.message.reply_text("❌ Invalid Team ID. Use /teams to find the correct ID.")
        return
        
    team = TEAMS[target_id]
    
    # 3. Check if team is full
    if len(team.member_ids) >= 3:
        await update.message.reply_text(f"❌ Team **{team.name}** is already full (max 3 players).", parse_mode='Markdown')
        return
        
    # 4. Join the team
    team.member_ids.append(user_id)
    USER_TO_TEAM[user_id] = target_id
    
    # 5. Persist the change to the team's JSON file
    team.save(TEAMS_DIR)
    
    await update.message.reply_text(
        f"✅ Success! You have joined **{team.name}**.\n"
        "Use /challenges to see your current tasks.", 
        parse_mode='Markdown'
    )

async def challenges_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays challenges currently unlocked for the user's team."""
    team = get_team(update.effective_user.id)
    if not team:
        await update.message.reply_text("You aren't on a team yet!")
        return

    if not team.active_challenges:
        await update.message.reply_text("You have no active challenges. Contact an admin if this is an error.")
        return

    response = "🎯 **Your Active Challenges** 🎯\n\n"

    print(CHALLENGES.keys())
    print(team.active_challenges)

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
        f"📊 **Team Summary: {team.name}**\n"
        f"🆔 ID: `{team.team_id}`\n"
        f"⭐ Total Score: {team.score} pts\n"
        f"✅ Solved: {len(team.solved_challenges)}\n"
        f"🔓 Active: {len(team.active_challenges)}"
    )
    await update.message.reply_text(summary, parse_mode='Markdown')

async def submit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    team = get_team(update.effective_user.id)
    if not team:
        await update.message.reply_text("Register to a team first!")
        return
        
    if not context.args:
        await update.message.reply_text("Usage: /submit <flag>")
        return
        
    submitted_flag = context.args[0].strip()
    
    # Check against all active challenges for this team
    for chall_id in list(team.active_challenges):
        challenge = CHALLENGES.get(chall_id)
        if challenge and submitted_flag in challenge.flags:
            # Solve logic handles points, moving from active to solved, and unlocking new ones
            success, new_unlocks = team.solve(challenge)
            if success:
                team.save(TEAMS_DIR) # Persist progress to JSON file
                
                # Build the response message
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
        
    # Sort teams by score
    sorted_teams = sorted(TEAMS.values(), key=lambda x: x.score, reverse=True)
    
    scoreboard = "🏆 **CTF SCOREBOARD** 🏆\n\n"
    for rank, team in enumerate(sorted_teams, 1):
        scoreboard += f"{rank}. {team.name} - {team.score} pts\n"
        
    await update.message.reply_text(scoreboard, parse_mode='Markdown')

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
    
    # Initialize the data
    load_all_teams() # Loads TEAMS and USER_TO_TEAM from the teams directory JSON files
    load_all_challenges() # Loads CHALLENGES from the challenges directory JSON files
    
    application = Application.builder().token(token).build()

    # Middleware-style logging
    application.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, log_all_messages), group=-1)

    # Handlers
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