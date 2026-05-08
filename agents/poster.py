import json
import os
import sys
import time
from datetime import datetime

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_credentials():
    # GitHub Actions: 環境変数から読み込む
    if os.environ.get("THREADS_ACCESS_TOKEN"):
        return {
            "THREADS_APP_ID": os.environ["THREADS_APP_ID"],
            "THREADS_APP_SECRET": os.environ["THREADS_APP_SECRET"],
            "THREADS_ACCESS_TOKEN": os.environ["THREADS_ACCESS_TOKEN"],
            "THREADS_USER_ID": os.environ["THREADS_USER_ID"],
        }
    # ローカル: credentials.envから読み込む
    creds = {}
    env_path = os.path.join(BOT_DIR, "config", "credentials.env")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                creds[key.strip()] = value.strip()
    return creds

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_safety():
    path = os.path.join(BOT_DIR, "config", "safety.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_kill_switch():
    kill_path = os.path.join(BOT_DIR, "KILL_SWITCH")
    if os.path.exists(kill_path):
        print("[STOP] KILL_SWITCHが有効です。投稿を中止します。")
        sys.exit(0)

def check_daily_limit(history, safety):
    today = datetime.now().strftime("%Y-%m-%d")
    today_posts = [p for p in history if p.get("posted_at", "").startswith(today)]
    if len(today_posts) >= safety["max_posts_per_day"]:
        print(f"[STOP] 本日の投稿上限（{safety['max_posts_per_day']}件）に達しています。")
        sys.exit(0)

def check_interval(history, safety):
    if not history:
        return
    last_post = history[-1]
    last_time_str = last_post.get("posted_at", "")
    if not last_time_str:
        return
    last_time = datetime.fromisoformat(last_time_str)
    elapsed = (datetime.now() - last_time).total_seconds() / 60
    min_interval = safety["min_post_interval_minutes"]
    if elapsed < min_interval:
        remaining = int(min_interval - elapsed)
        print(f"[STOP] 前回投稿から{int(elapsed)}分しか経っていません。あと{remaining}分待ってください。")
        sys.exit(0)

def increment_error(error_count_path, safety):
    count = 0
    if os.path.exists(error_count_path):
        with open(error_count_path, "r") as f:
            count = int(f.read().strip() or "0")
    count += 1
    with open(error_count_path, "w") as f:
        f.write(str(count))
    if count >= safety["max_error_count"]:
        print(f"[STOP] エラーが{count}回連続しました。KILL_SWITCHを設置します。")
        kill_path = os.path.join(BOT_DIR, "KILL_SWITCH")
        open(kill_path, "w").close()
        sys.exit(1)

def reset_error(error_count_path):
    with open(error_count_path, "w") as f:
        f.write("0")

def create_thread(token, user_id, text):
    import urllib.request
    import urllib.parse
    url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    data = urllib.parse.urlencode({
        "media_type": "TEXT",
        "text": text,
        "access_token": token
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))

def publish_thread(token, user_id, creation_id):
    import urllib.request
    import urllib.parse
    url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
    data = urllib.parse.urlencode({
        "creation_id": creation_id,
        "access_token": token
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))

def reply_to_thread(token, user_id, reply_to_id, text):
    import urllib.request
    import urllib.parse
    url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    data = urllib.parse.urlencode({
        "media_type": "TEXT",
        "text": text,
        "reply_to_id": reply_to_id,
        "access_token": token
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))

def main():
    check_kill_switch()

    creds = load_credentials()
    token = creds["THREADS_ACCESS_TOKEN"]
    user_id = creds["THREADS_USER_ID"]
    safety = load_safety()

    queue_path = os.path.join(BOT_DIR, "data", "post_queue.json")
    history_path = os.path.join(BOT_DIR, "data", "post_history.json")
    error_count_path = os.path.join(BOT_DIR, "data", "error_count.txt")

    history = load_json(history_path)
    check_daily_limit(history, safety)
    check_interval(history, safety)

    queue = load_json(queue_path)
    if not queue:
        print("[INFO] キューが空です。ライターを先に実行してください。")
        sys.exit(0)

    post = queue.pop(0)
    text = post.get("text", "")
    reply_text = post.get("reply_text", "")

    print(f"[INFO] 投稿開始: {text[:30]}...")

    try:
        # メイン投稿
        result = create_thread(token, user_id, text)
        creation_id = result["id"]
        time.sleep(3)
        published = publish_thread(token, user_id, creation_id)
        post_id = published["id"]
        print(f"[OK] 投稿完了: {post_id}")

        # リプ欄への追加テキスト
        if reply_text:
            time.sleep(2)
            reply_result = create_thread(token, user_id, reply_text)
            reply_creation_id = reply_result["id"]
            time.sleep(3)
            # reply_to_idを使ってリプとして投稿
            reply_pub = reply_to_thread(token, user_id, post_id, reply_text)
            print(f"[OK] リプ投稿完了")

        # 履歴に追加
        post["post_id"] = post_id
        post["posted_at"] = datetime.now().isoformat()
        history.append(post)
        save_json(history_path, history)
        save_json(queue_path, queue)
        reset_error(error_count_path)
        print(f"[INFO] キュー残り: {len(queue)}件")

    except Exception as e:
        print(f"[ERROR] 投稿失敗: {e}")
        increment_error(error_count_path, safety)
        sys.exit(1)

if __name__ == "__main__":
    main()
