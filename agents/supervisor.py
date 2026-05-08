import json
import os
import urllib.request
from datetime import datetime, timedelta

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

def load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_kill_switch():
    kill_path = os.path.join(BOT_DIR, "KILL_SWITCH")
    if os.path.exists(kill_path):
        print("  [警告] KILL_SWITCH が有効です。投稿は停止中。")
        return True
    print("  [OK] KILL_SWITCH なし")
    return False

def check_error_count():
    error_path = os.path.join(BOT_DIR, "data", "error_count.txt")
    count = 0
    if os.path.exists(error_path):
        with open(error_path, "r") as f:
            count = int(f.read().strip() or "0")
    if count >= 3:
        print(f"  [警告] エラーカウント: {count}回（上限に達しています）")
    else:
        print(f"  [OK] エラーカウント: {count}回")
    return count

def check_queue():
    queue_path = os.path.join(BOT_DIR, "data", "post_queue.json")
    queue = load_json(queue_path, default=[])
    count = len(queue)
    if count == 0:
        print("  [警告] キューが空です。ライターを実行してください。")
    elif count < 3:
        print(f"  [注意] キュー残り{count}件（少なめです）")
    else:
        print(f"  [OK] キュー残り: {count}件")
    return count

def check_token(token, user_id):
    url = f"https://graph.threads.net/v1.0/me?fields=id,username&access_token={token}"
    try:
        with urllib.request.urlopen(url, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
            print(f"  [OK] トークン有効 (@{data.get('username')})")
            return True
    except Exception as e:
        print(f"  [警告] トークンエラー: {e}")
        return False

def check_last_post():
    history_path = os.path.join(BOT_DIR, "data", "post_history.json")
    history = load_json(history_path, default=[])
    if not history:
        print("  [INFO] 投稿履歴なし（初回セットアップ）")
        return
    last = history[-1]
    posted_at = last.get("posted_at", "")
    try:
        last_time = datetime.fromisoformat(posted_at)
        elapsed = datetime.now() - last_time
        hours = int(elapsed.total_seconds() / 3600)
        print(f"  [OK] 最終投稿: {hours}時間前 ({posted_at[:16]})")
        if hours > 24:
            print("  [注意] 24時間以上投稿がありません")
    except Exception:
        print(f"  [INFO] 最終投稿時刻: {posted_at}")

def daily_report():
    history_path = os.path.join(BOT_DIR, "data", "post_history.json")
    history = load_json(history_path, default=[])
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    today_posts = [p for p in history if p.get("posted_at", "").startswith(today)]
    yesterday_posts = [p for p in history if p.get("posted_at", "").startswith(yesterday)]

    print(f"\n  本日の投稿数: {len(today_posts)}件")
    print(f"  昨日の投稿数: {len(yesterday_posts)}件")
    print(f"  累計投稿数: {len(history)}件")

    # 昨日の投稿のメトリクス集計
    if yesterday_posts:
        total_views = sum(p.get("metrics", {}).get("views", 0) for p in yesterday_posts)
        total_likes = sum(p.get("metrics", {}).get("likes", 0) for p in yesterday_posts)
        print(f"  昨日の合計views: {total_views} / likes: {total_likes}")

def main():
    print("=" * 40)
    print("Threads Bot ヘルスチェック")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 40)

    creds = load_credentials()
    token = creds["THREADS_ACCESS_TOKEN"]
    user_id = creds["THREADS_USER_ID"]

    print("\n【KILL_SWITCH】")
    check_kill_switch()

    print("\n【エラー状態】")
    check_error_count()

    print("\n【キュー状態】")
    check_queue()

    print("\n【トークン】")
    check_token(token, user_id)

    print("\n【最終投稿】")
    check_last_post()

    print("\n【日次レポート】")
    daily_report()

    print("\n" + "=" * 40)

if __name__ == "__main__":
    main()
