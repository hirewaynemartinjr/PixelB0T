#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =========================================================
# Availability Bot (Production) — PixelB0T-BF6CalendarCoordinator
# =========================================================
# Enhanced Parser Version - Better Comma Handling
# =========================================================

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, time
import asyncio
import json
import pytz
import os
import re
import logging
import sys
import signal
import shutil
from typing import Dict, Tuple, Optional
import io
from collections import deque
import psutil
from dotenv import load_dotenv

load_dotenv()  # Loads DISCORD_TOKEN from /home/opc/.env

# -----------------------
# CONFIG
# -----------------------
GAMES = {
    'BF6': {'channel': 1426994243398008872, 'poll_msg': 'BF6 Weekly Availability'},
    'ARC': {'channel': 1429276090807091230, 'poll_msg': 'ARC RAIDERS Weekly Availability'}
}
DEFAULT_GAME = 'BF6'
TZ_FILE = 'user_tzs.json'
AVAIL_FILE = 'availability.json'
BACKUP_DIR = '/home/opc/backup'
PROCESSED_LIMIT = 2000
DEFAULT_REACTION_START = time(18, 0)
DEFAULT_REACTION_END = time(23, 0)
DEFAULT_TZ = 'UTC'
SAVE_AFTER_CHANGE = True
REACTIONS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣']

# -----------------------
# GLOBAL TIMEZONE SHORTCUTS (100+)
# -----------------------
TZ_SHORTCUTS = {
    'PH': 'Asia/Manila', 'PHK': 'Asia/Manila', 'PHT': 'Asia/Manila',
    'JP': 'Asia/Tokyo', 'JST': 'Asia/Tokyo',
    'KR': 'Asia/Seoul', 'KST': 'Asia/Seoul',
    'CN': 'Asia/Shanghai', 'CST': 'Asia/Shanghai',
    'HK': 'Asia/Hong_Kong', 'HKT': 'Asia/Hong_Kong',
    'SG': 'Asia/Singapore', 'SGT': 'Asia/Singapore',
    'MY': 'Asia/Kuala_Lumpur', 'MYT': 'Asia/Kuala_Lumpur',
    'ID': 'Asia/Jakarta', 'WIB': 'Asia/Jakarta',
    'TH': 'Asia/Bangkok', 'ICT': 'Asia/Bangkok',
    'VN': 'Asia/Ho_Chi_Minh',
    'IN': 'Asia/Kolkata', 'IST': 'Asia/Kolkata',
    'PK': 'Asia/Karachi', 'PKT': 'Asia/Karachi',
    'BD': 'Asia/Dhaka', 'BDT': 'Asia/Dhaka',
    'LK': 'Asia/Colombo',
    'NP': 'Asia/Kathmandu',
    'AF': 'Asia/Kabul',
    'AE': 'Asia/Dubai', 'GST': 'Asia/Dubai',
    'IR': 'Asia/Tehran', 'IRST': 'Asia/Tehran',
    'RU': 'Europe/Moscow', 'MSK': 'Europe/Moscow',
    'KZ': 'Asia/Almaty',
    'GB': 'Europe/London', 'GMT': 'Europe/London', 'BST': 'Europe/London',
    'FR': 'Europe/Paris', 'CET': 'Europe/Paris', 'CEST': 'Europe/Paris',
    'DE': 'Europe/Berlin',
    'IT': 'Europe/Rome',
    'ES': 'Europe/Madrid',
    'NL': 'Europe/Amsterdam',
    'SE': 'Europe/Stockholm',
    'NO': 'Europe/Oslo',
    'DK': 'Europe/Copenhagen',
    'FI': 'Europe/Helsinki',
    'PL': 'Europe/Warsaw',
    'GR': 'Europe/Athens', 'EET': 'Europe/Athens',
    'TR': 'Europe/Istanbul',
    'UA': 'Europe/Kiev',
    'RO': 'Europe/Bucharest',
    'US': 'America/New_York', 'EST': 'America/New_York', 'EDT': 'America/New_York',
    'US/PACIFIC': 'America/Los_Angeles', 'PST': 'America/Los_Angeles', 'PDT': 'America/Los_Angeles',
    'US/CENTRAL': 'America/Chicago', 'CDT': 'America/Chicago',
    'US/MOUNTAIN': 'America/Denver', 'MST': 'America/Denver', 'MDT': 'America/Denver',
    'CA': 'America/Toronto',
    'MX': 'America/Mexico_City',
    'BR': 'America/Sao_Paulo', 'BRT': 'America/Sao_Paulo',
    'AR': 'America/Argentina/Buenos_Aires',
    'CL': 'America/Santiago',
    'CO': 'America/Bogota',
    'PE': 'America/Lima',
    'VE': 'America/Caracas',
    'AU': 'Australia/Sydney', 'AEST': 'Australia/Sydney', 'AEDT': 'Australia/Sydney',
    'NZ': 'Pacific/Auckland', 'NZST': 'Pacific/Auckland',
    'FJ': 'Pacific/Fiji',
    'ZA': 'Africa/Johannesburg', 'SAST': 'Africa/Johannesburg',
    'EG': 'Africa/Cairo',
    'NG': 'Africa/Lagos', 'WAT': 'Africa/Lagos',
    'MA': 'Africa/Casablanca',
    'KE': 'Africa/Nairobi', 'EAT': 'Africa/Nairobi',
    'UTC': 'UTC', 'ZULU': 'UTC', 'GMT+0': 'UTC', 'GMT-0': 'UTC',
}

# -----------------------
# Logging
# -----------------------
logging.basicConfig(
    filename="/home/opc/availabilitybot.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger('availability_bot')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

# -----------------------
# Prevent Duplicate Instances
# -----------------------
def prevent_duplicate_instance():
    current_pid = os.getpid()
    script_name = os.path.basename(__file__)
    try:
        for proc in psutil.process_iter(['pid', 'cmdline', 'cwd']):
            pid = proc.info.get('pid')
            if not pid or pid == current_pid:
                continue
            cmdline = proc.info.get('cmdline') or []
            if script_name in " ".join(cmdline):
                cwd = proc.info.get('cwd')
                if cwd and os.path.abspath(cwd) == os.path.abspath(os.getcwd()):
                    logger.warning(f"Another instance running (PID {pid}). Exiting.")
                    sys.exit(1)
    except Exception as e:
        logger.debug(f"Duplicate check failed: {e}")
prevent_duplicate_instance()

# -----------------------
# Bot Setup
# -----------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix='!', intents=intents)

boot_time = datetime.utcnow()
current_polls: Dict[str, Optional[int]] = {game: None for game in GAMES}
processed_messages = deque(maxlen=PROCESSED_LIMIT)
bot_ready_once = False
last_poll_run: Dict[str, Optional[datetime]] = {game: None for game in GAMES}

# -----------------------
# JSON & Backup
# -----------------------
def load_json_file(fname: str) -> dict:
    if os.path.exists(fname):
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {fname}: {e}")
            shutil.copy(fname, f"{fname}.broken_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    return {}

def save_json_file(fname: str, obj: dict):
    tmp = f"{fname}.tmp"
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, fname)
    except Exception as e:
        logger.error(f"Failed to save {fname}: {e}")
        if os.path.exists(tmp):
            os.remove(tmp)

def backup_files():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    try:
        if os.path.exists(TZ_FILE):
            shutil.copy(TZ_FILE, f"{BACKUP_DIR}/user_tzs_{timestamp}.json")
        if os.path.exists(AVAIL_FILE):
            shutil.copy(AVAIL_FILE, f"{BACKUP_DIR}/availability_{timestamp}.json")
        logger.info(f"Backup created: {timestamp}")
    except Exception as e:
        logger.error(f"Backup failed: {e}")

def migrate_data():
    global avail_data_json
    if not avail_data_json:
        return
    needs_migration = any(
        not isinstance(user_data, dict) or
        not any(game in user_data for game in GAMES)
        for user_data in avail_data_json.values()
    )
    if not needs_migration:
        return
    new_data = {}
    for user_id, user_data in avail_data_json.items():
        if isinstance(user_data, dict) and any(game in user_data for game in GAMES):
            new_data[user_id] = user_data
        else:
            new_data[user_id] = {DEFAULT_GAME: user_data}
    avail_data_json = new_data
    save_json_file(AVAIL_FILE, avail_data_json)
    logger.info("Data migrated to multi-game structure.")

user_tzs = load_json_file(TZ_FILE)
avail_data_json = load_json_file(AVAIL_FILE)
migrate_data()

# -----------------------
# Time & TZ Helpers
# -----------------------
def _fmt_12h(t: time) -> str:
    formatted = t.strftime("%I:%M %p").lstrip("0")
    return formatted if formatted else "12:00 AM"

def time_to_str_24h(t: time) -> str:
    return f"{t.hour:02d}:{t.minute:02d}"

def parse_time_str(ts: str) -> time:
    h, m = map(int, ts.split(':'))
    return time(h, m)

def resolve_user_tz(user_id: str) -> str:
    return user_tzs.get(user_id, DEFAULT_TZ)


def validate_timezone(tz_input: str) -> Optional[str]:
    key = tz_input.strip().upper()
    if key in TZ_SHORTCUTS:
        return TZ_SHORTCUTS[key]
    try:
        pytz.timezone(tz_input.strip())
        return tz_input.strip()
    except Exception:
        return None

def get_game_channel(game: str) -> Optional[discord.TextChannel]:
    channel_id = GAMES.get(game.upper(), {}).get('channel')
    return bot.get_channel(channel_id) if channel_id else None

# -----------------------
# Parsing
# -----------------------
day_map = {
    'monday': 0, 'mon': 0, 'm': 0,
    'tuesday': 1, 'tue': 1, 't': 1,
    'wednesday': 2, 'wed': 2, 'w': 2,
    'thursday': 3, 'thu': 3, 'th': 3,
    'friday': 4, 'fri': 4, 'f': 4,
    'saturday': 5, 'sat': 5, 's': 5,
    'sunday': 6, 'sun': 6, 'su': 6
}

# Enhanced regex pattern
_avail_re = re.compile(
    r'(?P<day>\b(?:mon|monday|tue|tuesday|wed|wednesday|thu|thursday|fri|friday|sat|saturday|sun|sunday)\b)\s*'
    r'(?P<start>\d{1,2}(?::\d{2})?)\s*(?P<startamp>[AaPp][Mm])?\s*(?:-|to)\s*'
    r'(?P<end>\d{1,2}(?::\d{2})?)\s*(?P<endamp>[AaPp][Mm])?'
    r'(?:\s+(?P<tz>[A-Za-z/_+-]+))?',
    re.IGNORECASE
)


def parse_availability_text(text: str) -> Dict[int, Tuple[time, time, Optional[str]]]:
    """
    Enhanced parser that handles both formats:
    - Standard: "Monday 5-9 PM EST"
    - Comma-separated: "Monday 5-9 PM, Wednesday 5-9 PM, Friday 5-11PM"
    """
    avail: Dict[int, Tuple[time, time, Optional[str]]] = {}
    
    # First, try to extract timezone from end of message if present
    global_tz = None
    tz_at_end = re.search(r'\b([A-Z]{2,4}|[A-Z][a-z]+(?:/[A-Z][a-z]+)+)\s*$', text)
    if tz_at_end:
        potential_tz = tz_at_end.group(1)
        validated = validate_timezone(potential_tz)
        if validated:
            global_tz = validated
    
    for m in _avail_re.finditer(text):
        day_str = m.group('day').lower()
        if day_str not in day_map:
            continue
        try:
            start_str = m.group('start')
            end_str = m.group('end')
            startamp = m.group('startamp')
            endamp = m.group('endamp')
            tz_abbr = m.group('tz')
            
            # Parse hours and minutes
            sh, sm = (start_str.split(':') + ['0'])[:2]
            eh, em = (end_str.split(':') + ['0'])[:2]
            sh, sm, eh, em = int(sh), int(sm), int(eh), int(em)
            
            # Handle AM/PM for start time
            if startamp:
                if startamp.strip().upper() == 'PM' and sh < 12:
                    sh += 12
                elif startamp.strip().upper() == 'AM' and sh == 12:
                    sh = 0
            # If no AM/PM specified but end time has PM, assume start is also PM
            elif endamp and endamp.strip().upper() == 'PM' and sh < 12:
                sh += 12
                
            # Handle AM/PM for end time
            if endamp:
                if endamp.strip().upper() == 'PM' and eh < 12:
                    eh += 12
                elif endamp.strip().upper() == 'AM' and eh == 12:
                    eh = 0
            # If start has AM/PM but end doesn't, try to infer
            elif startamp:
                if startamp.strip().upper() == 'PM' and eh < 12 and eh > sh:
                    eh += 12
                    
            start_t = time(sh % 24, sm)
            end_t = time(eh % 24, em)
            
            # Use inline timezone if present, otherwise fall back to global
            tz_full = None
            if tz_abbr:
                tz_full = validate_timezone(tz_abbr.strip())
            elif global_tz:
                tz_full = global_tz
                
            avail[day_map[day_str]] = (start_t, end_t, tz_full)
            logger.info(f"Parsed: {day_str} {sh}:{sm:02d}-{eh}:{em:02d} (TZ: {tz_full})")
        except Exception as e:
            logger.error(f"Parse error for '{m.group(0)}': {e}")
    
    return avail

# -----------------------
# Persistence
# -----------------------
def set_user_availability_json(user_id: str, game: str, day_idx: int, start_t: time, end_t: time, tz_str: Optional[str] = None):
    user_entry = avail_data_json.setdefault(user_id, {})
    game_entry = user_entry.setdefault(game.upper(), {})
    game_entry[str(day_idx)] = [time_to_str_24h(start_t), time_to_str_24h(end_t), tz_str or ""]
    if SAVE_AFTER_CHANGE:
        save_json_file(AVAIL_FILE, avail_data_json)

def clear_user_availability(user_id: str, game: str = None):
    if not game:
        avail_data_json.pop(user_id, None)
    else:
        game = game.upper()
        if user_id in avail_data_json and game in avail_data_json[user_id]:
            avail_data_json[user_id].pop(game, None)
            if not avail_data_json[user_id]:
                avail_data_json.pop(user_id, None)
    save_json_file(AVAIL_FILE, avail_data_json)

# -----------------------
# Events
# -----------------------
@bot.event
async def on_ready():
    global bot_ready_once
    if bot_ready_once:
        return
    bot_ready_once = True
    logger.info(f"{bot.user} is online!")
    logger.info(f"Loaded {len(avail_data_json)} users across {len(GAMES)} games.")
    backup_files()
    if not weekly_poll.is_running():
        weekly_poll.start()
    if not backup_task.is_running():
        backup_task.start()

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or message.id in processed_messages:
        return
    processed_messages.append(message.id)

    game = next((g for g, c in GAMES.items() if c['channel'] == message.channel.id), None)
    if not game:
        await bot.process_commands(message)
        return

    poll_id = current_polls.get(game.upper())
    if message.reference and message.reference.message_id == poll_id:
        user_id = str(message.author.id)
        parsed = parse_availability_text(message.content)
        if parsed:
            for di, (st, et, tz) in parsed.items():
                set_user_availability_json(user_id, game, di, st, et, tz)
            try:
                dm = await message.author.create_dm()
                day_names = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                lines = [f"• {day_names[di]}: {_fmt_12h(st)} - {_fmt_12h(et)} ({tz or resolve_user_tz(user_id)})" 
                         for di, (st, et, tz) in sorted(parsed.items())]
                await dm.send(f"✅ **{game.upper()} availability recorded:**\n" + "\n".join(lines))
                await message.add_reaction('✅')
            except Exception as e:
                logger.error(f"DM failed: {e}")
                await message.add_reaction('✅')
        else:
            # No valid entries parsed
            try:
                await message.add_reaction('❌')
                dm = await message.author.create_dm()
                await dm.send(
                    f"⚠️ Couldn't parse your availability. Please use format:\n"
                    f"`Monday 5-9 PM`\n"
                    f"or\n"
                    f"`Monday 5-9 PM, Wednesday 5-9 PM, Friday 5-11 PM`"
                )
            except:
                pass
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.bot:
        return
    game = next((g for g, c in GAMES.items() if c['channel'] == reaction.message.channel.id), None)
    if not game or reaction.message.id != current_polls.get(game.upper()):
        return
    emoji_map = {r: i for i, r in enumerate(REACTIONS, 1)}
    di = emoji_map.get(str(reaction.emoji))
    if di is None and str(reaction.emoji).isdigit():
        di = int(str(reaction.emoji))
    if di is None or di not in range(1, 8):
        return
    di -= 1
    user_id = str(user.id)
    tz = resolve_user_tz(user_id)
    set_user_availability_json(user_id, game, di, DEFAULT_REACTION_START, DEFAULT_REACTION_END, tz)
    try:
        dm = await user.create_dm()
        await dm.send(f"{game.upper()} Quick availability set for {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][di]} {_fmt_12h(DEFAULT_REACTION_START)}–{_fmt_12h(DEFAULT_REACTION_END)} ({tz}).")
    except:
        pass

# -----------------------
# Tasks
# -----------------------
@tasks.loop(minutes=1)
async def weekly_poll():
    now = datetime.utcnow()
    if now.weekday() == 6 and now.hour == 0 and now.minute in (0, 1):
        for game, config in GAMES.items():
            last_run = last_poll_run.get(game)
            if last_run and (now - last_run).total_seconds() < 3600:
                continue
            channel = bot.get_channel(config['channel'])
            if not channel:
                continue
            start_date = now + timedelta(days=1)
            end_date = start_date + timedelta(days=6)
            embed = discord.Embed(
                title=f"{config['poll_msg']} ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')})",
                description="React for quick entry!\nReply with times.\n`!settz <tz>`",
                color=0x00ff00
            )
            msg = await channel.send(embed=embed)
            current_polls[game.upper()] = msg.id
            for e in REACTIONS:
                await msg.add_reaction(e)
            await channel.send(f"@everyone Mark {game.upper()} availability! Use `!mycalendar {game.lower()}` to export.")
            last_poll_run[game] = now
            logger.info(f"{game.upper()} Weekly poll created: {msg.id}")

@weekly_poll.before_loop
async def before_poll():
    await bot.wait_until_ready()

@tasks.loop(hours=6)
async def backup_task():
    backup_files()

@backup_task.before_loop
async def before_backup():
    await bot.wait_until_ready()

# -----------------------
# Commands
# -----------------------
@bot.command(name='settz')
async def set_tz(ctx, *, tz_str: str = None):
    if not tz_str:
        await ctx.send("Usage: `!settz <timezone>` e.g. `!settz PHK`")
        return
    tz_full = validate_timezone(tz_str) or tz_str.strip()
    try:
        pytz.timezone(tz_full)
        user_tzs[str(ctx.author.id)] = tz_full
        save_json_file(TZ_FILE, user_tzs)
        await ctx.send(f"Timezone set to **{tz_full}**")
    except:
        await ctx.send("Invalid timezone! Try `!settz PHK` or `!settz America/New_York`")

@bot.command(name='clear')
async def clear_availability(ctx, game: str = None):
    """Clear user's availability data with enhanced error handling"""
    user_id = str(ctx.author.id)
    
    # Handle explicit "confirm" for clearing all data
    if game and game.lower() == 'confirm':
        success, errors = await clear_all_user_data(ctx.author)
        clear_user_availability(user_id, None)
        
        if errors:
            error_msg = "\n".join([f"⚠️ {err}" for err in errors])
            await ctx.send(f"✅ Data cleared, but some issues:\n{error_msg}")
        else:
            await ctx.send("✅ All your availability data has been **cleared** for all games. Reactions and messages removed.")
        return
    
    # Auto-detect game from channel if not specified
    if not game:
        game = next((g for g, c in GAMES.items() if c['channel'] == ctx.channel.id), None)
    
    # If still no game, ask for confirmation
    if not game:
        await ctx.send("⚠️ This will clear ALL your availability data for all games.\nType `!clear confirm` to proceed, or use `!clear BF6` or `!clear ARC` to clear specific games.")
        return
    
    # Clear specific game
    game = game.upper()
    if game not in GAMES:
        await ctx.send(f"Invalid game. Use: {', '.join(GAMES.keys())}")
        return
    
    # Clear reactions and messages for this specific game
    success, errors = await clear_game_user_data(ctx.author, game)
    
    # Clear data from JSON
    clear_user_availability(user_id, game)
    
    # Provide detailed feedback
    if success and not errors:
        await ctx.send(f"✅ Your **{game}** availability has been cleared. Reactions and messages removed.")
    elif success and errors:
        error_msg = "\n".join([f"⚠️ {err}" for err in errors])
        await ctx.send(f"✅ Your **{game}** availability data cleared, but:\n{error_msg}")
    else:
        error_msg = "\n".join([f"❌ {err}" for err in errors])
        await ctx.send(f"❌ Failed to clear **{game}** data:\n{error_msg}")
        logger.error(f"Clear failed for user {user_id}, game {game}: {errors}")


async def clear_game_user_data(user, game: str) -> Tuple[bool, list]:
    """
    Remove user's reactions from poll and delete their availability reply messages
    Returns: (success: bool, errors: list)
    """
    errors = []
    reactions_removed = 0
    messages_deleted = 0
    
    try:
        poll_id = current_polls.get(game.upper())
        if not poll_id:
            errors.append(f"No active poll found for {game}. Data cleared but reactions couldn't be removed.")
            logger.warning(f"No poll_id for {game} in current_polls: {current_polls}")
            return False, errors
        
        channel_id = GAMES.get(game.upper(), {}).get('channel')
        if not channel_id:
            errors.append(f"Channel configuration missing for {game}")
            logger.error(f"No channel_id in GAMES config for {game}")
            return False, errors
        
        channel = bot.get_channel(channel_id)
        if not channel:
            errors.append(f"Bot cannot access {game} channel (ID: {channel_id})")
            logger.error(f"Failed to get channel {channel_id}")
            return False, errors
        
        # Get the poll message
        try:
            poll_message = await channel.fetch_message(poll_id)
            logger.info(f"Found poll message {poll_id} for {game}")
        except discord.NotFound:
            errors.append(f"Poll message not found (may have been deleted)")
            logger.warning(f"Poll message {poll_id} not found in channel {channel_id}")
            return False, errors
        except discord.Forbidden:
            errors.append(f"Bot lacks permission to read messages in {game} channel")
            logger.error(f"Permission denied reading message {poll_id}")
            return False, errors
        except Exception as e:
            errors.append(f"Error fetching poll message: {str(e)}")
            logger.error(f"Exception fetching message {poll_id}: {e}")
            return False, errors
        
        # Remove user's reactions from poll
        for reaction in poll_message.reactions:
            try:
                # Check if user has this reaction
                users = [u async for u in reaction.users()]
                if user in users:
                    await reaction.remove(user)
                    reactions_removed += 1
                    logger.info(f"Removed reaction {reaction.emoji} from user {user.id}")
            except discord.Forbidden:
                errors.append(f"Bot lacks permission to remove reactions")
                logger.error(f"Permission denied removing reaction {reaction.emoji}")
            except discord.NotFound:
                # Reaction was already removed, that's fine
                pass
            except Exception as e:
                logger.error(f"Error removing reaction {reaction.emoji}: {e}")
        
        # Delete user's availability reply messages
        try:
            async for message in channel.history(limit=100):
                if message.author.id == user.id and message.reference:
                    if message.reference.message_id == poll_id:
                        try:
                            await message.delete()
                            messages_deleted += 1
                            logger.info(f"Deleted reply message {message.id} from user {user.id}")
                        except discord.Forbidden:
                            errors.append(f"Bot lacks permission to delete messages")
                            logger.error(f"Permission denied deleting message {message.id}")
                        except discord.NotFound:
                            # Message was already deleted
                            pass
                        except Exception as e:
                            logger.error(f"Error deleting message {message.id}: {e}")
        except discord.Forbidden:
            errors.append(f"Bot lacks permission to read message history")
            logger.error(f"Permission denied reading history in channel {channel_id}")
        except Exception as e:
            errors.append(f"Error reading message history: {str(e)}")
            logger.error(f"Exception reading history: {e}")
        
        # Log summary
        logger.info(f"Clear complete for user {user.id}, game {game}: {reactions_removed} reactions, {messages_deleted} messages")
        
        if reactions_removed > 0 or messages_deleted > 0:
            return True, errors
        elif not errors:
            errors.append("No reactions or messages found to remove")
            return True, errors
        else:
            return False, errors
                        
    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")
        logger.error(f"Exception in clear_game_user_data for {game}: {e}", exc_info=True)
        return False, errors


async def clear_all_user_data(user) -> Tuple[bool, list]:
    """
    Clear user's reactions and messages from all games
    Returns: (success: bool, errors: list)
    """
    all_errors = []
    all_success = True
    
    for game in GAMES.keys():
        success, errors = await clear_game_user_data(user, game)
        if not success:
            all_success = False
        all_errors.extend(errors)
    
    return all_success, all_errors

@bot.command(name='bothelp')
async def help_command(ctx):
    embed = discord.Embed(title="PixelB0T-BF6 Help", color=0x00ff00)
    embed.add_field(name="`!settz <tz>`", value="Set timezone\n`!settz PHK` = Philippines", inline=False)
    embed.add_field(name="React 1-7", value="Quick 18:00–23:00", inline=False)
    embed.add_field(name="Reply to poll", value="Examples:\n`Monday 5-9 PM`\n`Mon 5-9 PM, Wed 5-9 PM, Fri 5-11PM`", inline=False)
    embed.add_field(name="`!summary [BF6|ARC] [tz]`", value="View availability", inline=False)
    embed.add_field(name="`!mycalendar [BF6|ARC]`", value="Download .ics", inline=False)
    embed.add_field(name="`!clear [BF6|ARC]`", value="Remove your data", inline=False)
    embed.add_field(name="`!start_polls [BF6|ARC]`", value="Manual poll", inline=False)
    embed.add_field(name="`!uptime`", value="Bot stats", inline=False)
    embed.set_footer(text="Auto-poll: Sundays 00:00 UTC")
    await ctx.send(embed=embed)

@bot.command(name='debugclear')
@commands.has_permissions(administrator=True)
async def debug_clear(ctx, game: str = None):
    """Admin command to debug clear functionality"""
    if not game:
        game = next((g for g, c in GAMES.items() if c['channel'] == ctx.channel.id), None)
    
    if not game:
        await ctx.send("Please specify a game: !debugclear BF6 or !debugclear ARC")
        return
    
    game = game.upper()
    
    # Show current state
    poll_id = current_polls.get(game)
    channel_id = GAMES.get(game, {}).get('channel')
    channel = bot.get_channel(channel_id) if channel_id else None
    
    debug_info = [
        f"**Debug Info for {game}:**",
        f"Poll ID in memory: {poll_id}",
        f"Channel ID: {channel_id}",
        f"Channel accessible: {channel is not None}",
    ]
    
    if poll_id and channel:
        try:
            poll_msg = await channel.fetch_message(poll_id)
            debug_info.append(f"Poll message found: Yes")
            debug_info.append(f"Reactions on poll: {len(poll_msg.reactions)}")
            
            # Count user's reactions
            user_reactions = 0
            for reaction in poll_msg.reactions:
                users = [u async for u in reaction.users()]
                if ctx.author in users:
                    user_reactions += 1
            debug_info.append(f"Your reactions: {user_reactions}")
            
        except Exception as e:
            debug_info.append(f"Error accessing poll: {e}")
    
    # Check bot permissions
    if channel:
        perms = channel.permissions_for(channel.guild.me)
        debug_info.extend([
            "",
            "**Bot Permissions:**",
            f"Read Messages: {perms.read_messages}",
            f"Read Message History: {perms.read_message_history}",
            f"Manage Messages: {perms.manage_messages}",
            f"Add Reactions: {perms.add_reactions}",
        ])
    
    await ctx.send("\n".join(debug_info))

@bot.command(name='summary')
async def summary(ctx, game: str = DEFAULT_GAME, *, tz: str = None):
    game = game.upper()
    if game not in GAMES:
        await ctx.send(f"Invalid game. Use: {', '.join(GAMES.keys())}")
        return
    display_tz = tz or user_tzs.get(str(ctx.author.id), DEFAULT_TZ)
    try:
        pytz.timezone(display_tz)
    except:
        await ctx.send("Invalid display timezone.")
        return
    days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    lines = [f"**{game} Availability Summary ({display_tz})**\n"]
    total = 0
    def _name_for(uid: str) -> str:
        member = ctx.guild.get_member(int(uid)) if ctx.guild else None
        return member.display_name if member else f"User {uid[:6]}"
    for di in range(7):
        entries = []
        for uid, user_raw in avail_data_json.items():
            game_raw = user_raw.get(game, {})
            if str(di) not in game_raw:
                continue
            st_str, et_str, stored_tz = (game_raw[str(di)] + [''])[:3]
            from_tz = stored_tz or user_tzs.get(uid, DEFAULT_TZ)
            try:
                tz_from = pytz.timezone(from_tz)
                ref_date = datetime.now(tz_from).date()
                st = parse_time_str(st_str)
                et = parse_time_str(et_str)
                st_conv = tz_from.localize(datetime.combine(ref_date, st)).astimezone(pytz.timezone(display_tz)).time()
                et_conv = tz_from.localize(datetime.combine(ref_date, et)).astimezone(pytz.timezone(display_tz)).time()
                entries.append(f"{_name_for(uid)}: {_fmt_12h(st_conv)}–{_fmt_12h(et_conv)}")
            except:
                entries.append(f"{_name_for(uid)}: {_fmt_12h(parse_time_str(st_str))}–{_fmt_12h(parse_time_str(et_str))} (raw)")
        if entries:
            lines.append(f"**{days[di]}** ({len(entries)}):")
            lines.extend(entries)
            lines.append("")
            total += len(entries)
        else:
            lines.append(f"**{days[di]}**: None\n")
    lines.append(f"**Total**: {total}")
    msg = "\n".join(lines)
    if len(msg) > 1900:
        with open("summary.txt", "w") as f:
            f.write(msg)
        await ctx.send(file=discord.File("summary.txt"))
        os.remove("summary.txt")
    else:
        await ctx.send(msg)

@bot.command(name='mycalendar')
async def mycalendar(ctx, game: str = DEFAULT_GAME):
    game = game.upper()
    if game not in GAMES:
        await ctx.send(f"Invalid game. Use: {', '.join(GAMES.keys())}")
        return
    user_id = str(ctx.author.id)
    user_data = avail_data_json.get(user_id, {}).get(game)
    if not user_data:
        await ctx.send(f"No {game} availability saved. React or reply to the {game} poll!")
        return
    tz_str = user_tzs.get(user_id, DEFAULT_TZ)
    tz = pytz.timezone(tz_str)
    today = datetime.now(tz)
    monday = today.date() - timedelta(days=today.weekday())
    ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AvailabilityBot//EN"]
    for k, v in user_data.items():
        di = int(k)
        st = parse_time_str(v[0])
        et = parse_time_str(v[1])
        event_date = monday + timedelta(days=di)
        start_local = datetime.combine(event_date, st)
        end_local = datetime.combine(event_date, et)
        start_utc = tz.localize(start_local).astimezone(pytz.utc)
        end_utc = tz.localize(end_local).astimezone(pytz.utc)
        uid = f"{user_id}-{game}-{di}@{bot.user.id}"
        ics.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{end_utc.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{game} Available",
            "END:VEVENT"
        ])
    ics.append("END:VCALENDAR")
    content = "\n".join(ics)
    file = discord.File(io.BytesIO(content.encode()), f"{game.lower()}_avail_{user_id}.ics")
    await ctx.send(file=file)

@bot.command(name='start_polls')
async def start_polls(ctx, game: str = DEFAULT_GAME):
    game = game.upper()
    if game not in GAMES:
        await ctx.send(f"Invalid game. Use: {', '.join(GAMES.keys())}")
        return
    channel = get_game_channel(game)
    if not channel:
        await ctx.send("Channel not accessible.")
        return
    now = datetime.utcnow()
    start_date = now + timedelta(days=1)
    end_date = start_date + timedelta(days=6)
    config = GAMES[game]
    embed = discord.Embed(
        title=f"{config['poll_msg']} ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')})",
        description="React or reply with times.\n`!settz <tz>`",
        color=0x00ff00
    )
    msg = await channel.send(embed=embed)
    current_polls[game] = msg.id
    for e in REACTIONS:
        await msg.add_reaction(e)
    await ctx.send(f"{game} Manual poll started!")

def _fmt_hms(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

@bot.command(name='uptime')
async def uptime(ctx):
    delta = datetime.utcnow() - boot_time
    bot_uptime = _fmt_hms(int(delta.total_seconds()))
    try:
        sys_up_seconds = int(datetime.utcnow().timestamp() - psutil.boot_time())
        sys_uptime = _fmt_hms(sys_up_seconds)
        cpu_percent = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        mem_used = f"{mem.used // (1024*1024)} MB"
        mem_total = f"{mem.total // (1024*1024)} MB"
    except:
        sys_uptime = cpu_percent = mem_used = mem_total = "N/A"
    latency_ms = int(bot.latency * 1000) if bot.latency else 0
    embed = discord.Embed(title="PixelB0T Uptime", color=0x00ff00)
    embed.add_field(name="Bot", value=f"`{bot_uptime}`", inline=True)
    embed.add_field(name="System", value=f"`{sys_uptime}`", inline=True)
    embed.add_field(name="Ping", value=f"`{latency_ms} ms`", inline=True)
    embed.add_field(name="CPU / RAM", value=f"`{cpu_percent:.1f}% | {mem_used}/{mem_total}`", inline=False)
    embed.set_footer(text="PixelB0T-BF6CalendarCoordinator")
    await ctx.send(embed=embed)

# -----------------------
# Graceful Shutdown
# -----------------------
def save_on_exit():
    save_json_file(TZ_FILE, user_tzs)
    save_json_file(AVAIL_FILE, avail_data_json)
    backup_files()
    logger.info("Data saved on exit.")

def signal_handler(sig, frame):
    logger.info("Shutting down...")
    save_on_exit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# -----------------------
# Run
# -----------------------
async def run_bot():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not set!")
        return
    while True:
        try:
            await bot.start(token)
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_bot())
