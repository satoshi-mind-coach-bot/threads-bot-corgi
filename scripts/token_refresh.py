import json
import os
import urllib.request
import urllib.parse
from datetime import datetime

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_credentials():
    creds = {}
    env_path = os.path.join(BOT_DIR, "config", "credentials.env")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                creds[key.strip()] = value.strip()
    return creds

def save_credentials(creds):
    env_path = os.path.join(BOT_DIR, "config", "credentials.env")
    with open(env_path, "w", encoding="utf-8") as f:
        for key, value in creds.items():
            f.write(f"{key}={value}\n")

def refresh_token(token):
    url = "https://graph.threads.net/refresh_access_token"
    params = urllib.parse.urlencode({
        "grant_type": "th_refresh_token",
        "access_token": token
    })
    full_url = f"{url}?{params}"
    with urllib.request.urlopen(full_url) as res:
        return json.loads(res.read().decode("utf-8"))

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] トークンリフレッシュ開始")
    creds = load_credentials()
    token = creds["THREADS_ACCESS_TOKEN"]

    try:
        result = refresh_token(token)
        new_token = result.get("access_token")
        if new_token:
            creds["THREADS_ACCESS_TOKEN"] = new_token
            save_credentials(creds)
            print(f"[OK] トークンを更新しました")
        else:
            print(f"[ERROR] 新しいトークンが取得できませんでした: {result}")
    except Exception as e:
        print(f"[ERROR] トークンリフレッシュ失敗: {e}")
        print("Meta Developer Dashboardから手動でトークンを再生成してください。")

if __name__ == "__main__":
    main()
