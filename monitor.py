import os
import time
import datetime
import requests
import json
import hashlib
import hmac
import base64

# --- CONFIGURATION (Load from Docker Environment) ---
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK", "ChangeMe")
AZURE_ID = os.getenv("AZURE_WORKSPACE_ID", "ChangeMe")
AZURE_KEY = os.getenv("AZURE_PRIMARY_KEY", "ChangeMe")
LOG_TYPE = "IronBridgeNetMon"

# --- AZURE SECURITY HANDSHAKE ---
def build_signature(customer_id, shared_key, date, content_length, method, content_type, resource):
    x_headers = 'x-ms-date:' + date
    string_to_hash = method + "\n" + str(content_length) + "\n" + content_type + "\n" + x_headers + "\n" + resource
    bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
    decoded_key = base64.b64decode(shared_key)
    encoded_hash = base64.b64encode(hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()).decode()
    authorization = "SharedKey {}:{}".format(customer_id, encoded_hash)
    return authorization

def send_to_azure(status, details):
    if AZURE_ID == "ChangeMe" or AZURE_KEY == "ChangeMe":
        print(" -> Azure keys missing. Skipping cloud log.")
        return
    json_data = [{"Time": str(datetime.datetime.utcnow()), "Status": status, "Details": details, "Server": "IronBridge-Core"}]
    body = json.dumps(json_data)
    rfc1123date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    try:
        signature = build_signature(AZURE_ID, AZURE_KEY, rfc1123date, len(body), 'POST', 'application/json', '/api/logs')
        uri = 'https://' + AZURE_ID + '.ods.opinsights.azure.com/api/logs?api-version=2016-04-01'
        headers = {'content-type': 'application/json', 'Authorization': signature, 'Log-Type': LOG_TYPE, 'x-ms-date': rfc1123date}
        response = requests.post(uri, data=body, headers=headers)
        if 200 <= response.status_code <= 299:
            print(" -> Logged to Azure Cloud successfully.")
        else:
            print(f" -> Azure Error: {response.text}")
    except Exception as e:
        print(f" -> Azure Failed: {e}")

def check_internet():
    return os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1") == 0

def send_discord_alert(message):
    if WEBHOOK_URL != "ChangeMe":
        try: requests.post(WEBHOOK_URL, json={"content": message})
        except: pass

print(f"--- Watchdog v2.0 (Hybrid Cloud) Started ---")
send_to_azure("Startup", "Watchdog service initialized")

while True:
    is_connected = check_internet()
    if not is_connected:
        send_to_azure("Outage", "Internet connectivity lost")
        send_discord_alert("🚨 ALERT: Internet is DOWN")
    time.sleep(10)
