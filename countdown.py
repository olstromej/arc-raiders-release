#!/usr/bin/env python3
"""
Arc Raiders weekly countdown poster.

Usage:
  # one-shot (good for testing)
  python countdown.py --once

  # run as a daemon that posts every Monday at 10:00 local time
  python countdown.py
"""
import argparse
import datetime
import json
import os
import random
import sys
import time
from typing import List

import requests

# ====== CONFIG ======
WEBHOOK_URL = "https://discord.com/api/webhooks/1420481165693026324/SB81pgThvD3TFVZMeZNkTc-TRHWvQDgqHXnfjMG2h9czMTyp9NodsCBdIz5Dcu5Nl15W"

ASSETS_DIR = "assets"
HEADER_IMAGES = [
    os.path.join(ASSETS_DIR, "header1.jpg"),
    os.path.join(ASSETS_DIR, "header2.jpg"),
    os.path.join(ASSETS_DIR, "header3.jpg"),
]
THUMBNAIL = os.path.join(ASSETS_DIR, "logo.png")

# Event datetimes (local system time)
SERVER_SLAM = datetime.datetime(2025, 10, 17, 0, 0, 0)
GAME_RELEASE = datetime.datetime(2025, 10, 30, 0, 0, 0)

COLORS = [
    0x1ABC9C,  # teal
    0xE74C3C,  # red
    0x3498DB,  # blue
    0x9B59B6,  # purple
    0xF1C40F,  # yellow
    0x2ECC71,  # green
]

# Scheduler config
POST_TIME = "10:00"  # 10 AM every Monday
LAST_POST_FILE = ".last_post"

# ====== HELPERS ======
def now():
    return datetime.datetime.now()

def get_countdown(target: datetime.datetime):
    delta = target - now()
    if delta.total_seconds() <= 0:
        return None
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    return f"{days}d {hours}h {minutes}m"

def read_last_post_date():
    if not os.path.exists(LAST_POST_FILE):
        return None
    try:
        with open(LAST_POST_FILE, "r") as f:
            return f.read().strip()
    except Exception:
        return None

def write_last_post_date(date_str: str):
    with open(LAST_POST_FILE, "w") as f:
        f.write(date_str)

def build_embed(fields: List[dict], color: int, header_filename: str = None, thumb_filename: str = None, title: str = None):
    embed = {
        "title": title or "📢 Arc Raiders Weekly Countdown",
        "description": "Get ready, Raiders! Here are the upcoming events:",
        "color": color,
        "fields": fields,
        "footer": {"text": "Arc Raiders • Stay Ready, Raiders!"},
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    if thumb_filename:
        embed["thumbnail"] = {"url": f"attachment://{os.path.basename(thumb_filename)}"}
    if header_filename:
        embed["image"] = {"url": f"attachment://{os.path.basename(header_filename)}"}
    return embed

def post_with_attachments(webhook_url: str, payload: dict, attachment_paths: List[str]):
    files = []
    file_objs = []
    try:
        for p in attachment_paths:
            if p and os.path.exists(p):
                fobj = open(p, "rb")
                file_objs.append(fobj)
                files.append(("file", (os.path.basename(p), fobj)))
        resp = requests.post(webhook_url, data={"payload_json": json.dumps(payload)}, files=files, timeout=15)
        resp.raise_for_status()
        return resp
    finally:
        for fo in file_objs:
            try:
                fo.close()
            except Exception:
                pass

# ====== MAIN POST LOGIC ======
def send_countdown_once():
    server_cd = get_countdown(SERVER_SLAM)
    release_cd = get_countdown(GAME_RELEASE)

    fields = []
    if server_cd:
        fields.append(
            {"name": "🔥 Server Slam", "value": f"Begins in: **{server_cd}**\n📅 October 17, 2025", "inline": False}
        )
    if release_cd:
        fields.append(
            {"name": "🚀 Official Game Release", "value": f"Launches in: **{release_cd}**\n📅 October 30, 2025", "inline": False}
        )

    if not fields:
        final_embed = {
            "title": "🎉 Arc Raiders — All Events Complete!",
            "description": "Both the Server Slam and the Official Release dates are in the past. Enjoy the game!",
            "color": random.choice(COLORS),
            "footer": {"text": "Arc Raiders • Stay Ready, Raiders!"},
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        payload = {"username": "Arc Raiders Countdown", "embeds": [final_embed]}
        attachments = [p for p in (random.choice(HEADER_IMAGES), THUMBNAIL) if p]
        post_with_attachments(WEBHOOK_URL, payload, attachments)
        print("Posted final message; all events are complete.")
        return "both_past"

    color = random.choice(COLORS)
    header = next((p for p in HEADER_IMAGES if os.path.exists(p)), None)
    thumb = THUMBNAIL if os.path.exists(THUMBNAIL) else None

    embed = build_embed(fields=fields, color=color, header_filename=header, thumb_filename=thumb)
    payload = {"username": "Arc Raiders Countdown", "embeds": [embed]}

    attachments = [p for p in (header, thumb) if p]
    post_with_attachments(WEBHOOK_URL, payload, attachments)
    print("Posted countdown.")
    return "ok"

# ====== SCHEDULER ======
def run_daemon():
    import schedule
    def job():
        today_str = datetime.date.today().isoformat()
        last = read_last_post_date()
        if last == today_str:
            print("Already posted today. Skipping.")
            return
        result = send_countdown_once()
        write_last_post_date(today_str)
        if result == "both_past":
            sys.exit(0)
    schedule.every().monday.at(POST_TIME).do(job)
    while True:
        schedule.run_pending()
        time.sleep(30)

# ====== CLI ======
def main():
    parser = argparse.ArgumentParser(description="Arc Raiders countdown webhook poster.")
    parser.add_argument("--once", action="store_true", help="Send one message now and exit.")
    args = parser.parse_args()

    if args.once:
        send_countdown_once()
    else:
        run_daemon()

if __name__ == "__main__":
    main()
