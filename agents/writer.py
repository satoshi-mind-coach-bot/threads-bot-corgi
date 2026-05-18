import json
import os
import sys
from datetime import datetime

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_THRESHOLD = 10
GENERATE_COUNT = 20

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_text(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    env_path = os.path.join(BOT_DIR, "config", "credentials.env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return None

def main():
    queue_path = os.path.join(BOT_DIR, "data", "post_queue.json")
    history_path = os.path.join(BOT_DIR, "data", "post_history.json")

    queue = load_json(queue_path)

    if len(queue) >= QUEUE_THRESHOLD:
        print(f"[INFO] キュー残り{len(queue)}件。補充不要。")
        return

    print(f"[INFO] キュー残り{len(queue)}件。{GENERATE_COUNT}件生成します。")

    persona = load_text(os.path.join(BOT_DIR, "knowledge", "knowledge", "persona.md"))
    themes = load_json(os.path.join(BOT_DIR, "knowledge", "knowledge", "theme_tree.json"))
    patterns = load_json(os.path.join(BOT_DIR, "knowledge", "knowledge", "post_patterns.json"))
    history = load_json(history_path)

    recent_texts = [p.get("text", "")[:60] for p in history[-30:]]
    today = datetime.now().strftime("%Y%m%d")
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    prompt = f"""あなたはThreads投稿ライターです。以下のペルソナと条件に従い、{GENERATE_COUNT}件の投稿を生成してください。

## ペルソナ
{persona}

## 使用可能なテーマ
{json.dumps(themes, ensure_ascii=False, indent=2)}

## 使用可能なパターン
{json.dumps(patterns, ensure_ascii=False, indent=2)}

## 生成ルール（厳守）
- 一人称は「僕」または一人称なし。「俺」は絶対禁止
- ハッシュタグは絶対付けない
- 経歴表現は「25年以上」（「25年間」は使わない）
- 誇張・嘘の数字は禁止（例：「3000人以上と話した」等は使わない）
- パターン16種をなるべく分散させる
- テーマ5カテゴリをバランスよく使う
- 1投稿150〜300文字
- スコアが7.0未満の投稿は含めない
- 各投稿に time_slot を必ず付けること（下記定義を厳守）

## time_slot の定義（厳守）
- "朝": 「おはよう」「朝」「起きた」「今日も」など朝を連想させる表現が含まれる投稿
- "昼": 「こんにちは」「昼」「午後」など昼を連想させる表現が含まれる投稿
- "夜": 「こんばんは」「夜」「今夜」「夜中」「おやすみ」など夜を連想させる表現が含まれる投稿
- "フリー": 時間帯に関係なく読める投稿（ほとんどはこれ）
- 朝の挨拶が入っているのに time_slot が "フリー" にならないよう注意すること

## 直近の投稿（重複を避けるために参照）
{json.dumps(recent_texts, ensure_ascii=False)}

## 出力形式
JSON配列のみ出力してください。説明文・コードブロック記号は不要です。

[
  {{
    "id": "{today}_001",
    "text": "投稿本文",
    "reply_text": "",
    "pattern": "パターンid",
    "theme": "テーマカテゴリ",
    "score": 8.5,
    "time_slot": "フリー",
    "created_at": "{now_str}"
  }}
]"""

    api_key = get_api_key()
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEYが見つかりません。")
        sys.exit(1)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()

    # コードブロック除去
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    new_posts = json.loads(response_text)

    # ID重複回避
    existing_ids = {p.get("id") for p in queue + history}
    for i, post in enumerate(new_posts, 1):
        base_id = f"{today}_{i:03d}"
        post["id"] = base_id
        while post["id"] in existing_ids:
            i += 1
            post["id"] = f"{today}_{i:03d}"
        existing_ids.add(post["id"])

    queue.extend(new_posts)
    save_json(queue_path, queue)
    print(f"[OK] {len(new_posts)}件追加。キュー合計: {len(queue)}件")

if __name__ == "__main__":
    main()
