import os
import time
import datetime
import requests  # <--- This is the library you just verified

# --- CONFIGURATION ---
# PASTE YOUR NEW DISCORD URL INSIDE THE QUOTES BELOW:
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK", "ChangeMe")

def check_internet():
    # Ping Google (8.8.8.8). 0 means success.
    response = os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1")
    if response == 0:
        return True
    else:
        return False

def send_discord_alert(message):
    data = {"content": message}
    try:
        requests.post(WEBHOOK_URL, json=data)
        print(" -> Discord Alert Sent!")
    except Exception as e:
        print(f" -> Failed to send Discord alert: {e}")

print("--- Watchdog Started ---")

# Send a test message immediately to prove it works
send_discord_alert("✅ Watchdog is starting up! Monitoring has begun.")

while True:
    is_connected = check_internet()
    now = datetime.datetime.now()
    
    if is_connected:
        print(f"[{now}] Internet is ONLINE")
    else:
        print(f"[{now}] Internet is OFFLINE !!!")
        send_discord_alert(f"🚨 ALERT: Internet is DOWN at {now}")
        
    time.sleep(10)
