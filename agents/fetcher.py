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

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_metrics(token, post_id):
    fields = "views,likes,replies,reposts,quotes"
    url = f"https://graph.threads.net/v1.0/{post_id}/insights?metric={fields}&access_token={token}"
    try:
        with urllib.request.urlopen(url) as res:
            data = json.loads(res.read().decode("utf-8"))
            metrics = {}
            for item in data.get("data", []):
                metrics[item["name"]] = item.get("values", [{}])[0].get("value", 0)
            return metrics
    except Exception as e:
        print(f"[WARN] メトリクス取得失敗 {post_id}: {e}")
        return {}

def main():
    creds = load_credentials()
    token = creds["THREADS_ACCESS_TOKEN"]
    history_path = os.path.join(BOT_DIR, "data", "post_history.json")
    history = load_json(history_path)

    if not history:
        print("[INFO] 投稿履歴がありません。")
        return

    # 直近3日以内の投稿のメトリクスを更新
    cutoff = datetime.now() - timedelta(days=3)
    updated = 0

    for post in history:
        post_id = post.get("post_id")
        posted_at = post.get("posted_at", "")
        if not post_id or not posted_at:
            continue
        try:
            post_time = datetime.fromisoformat(posted_at)
        except Exception:
            continue
        if post_time < cutoff:
            continue

        metrics = get_metrics(token, post_id)
        if metrics:
            post["metrics"] = metrics
            post["metrics_updated_at"] = datetime.now().isoformat()
            updated += 1
            print(f"[OK] {post_id}: views={metrics.get('views',0)} likes={metrics.get('likes',0)}")

    save_json(history_path, history)
    print(f"[INFO] {updated}件のメトリクスを更新しました。")

if __name__ == "__main__":
    main()
