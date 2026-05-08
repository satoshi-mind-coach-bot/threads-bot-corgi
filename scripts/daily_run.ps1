# daily_run.ps1 - 毎朝実行: フェッチャー → アナリスト → リサーチャー → ライター → スーパーバイザー

$BOT_DIR = "C:\Users\isesa\OneDrive\Desktop\threads-bot"
$LOG = "$BOT_DIR\logs\daily_run.log"
$CLAUDE = "claude"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content -Path $LOG -Value $line -Encoding UTF8
}

# KILL_SWITCHチェック
if (Test-Path "$BOT_DIR\KILL_SWITCH") {
    Log "KILL_SWITCH active. Exiting."
    exit 0
}

Log "=== daily_run 開始 ==="

# エラーカウントリセット
"0" | Out-File "$BOT_DIR\data\error_count.txt" -Encoding UTF8
Log "エラーカウントリセット完了"

# 1. フェッチャー（昨日の投稿のメトリクス取得）
Log "フェッチャー実行中..."
$result = & python "$BOT_DIR\agents\fetcher.py" 2>&1
Log $result
Log "フェッチャー完了"

# 2. アナリスト（パフォーマンス分析）
Log "アナリスト実行中..."
$result = & $CLAUDE -p (Get-Content "$BOT_DIR\agents\analyst.md" -Raw -Encoding UTF8) --cwd "$BOT_DIR" 2>&1
Log "アナリスト完了"

# 3. リサーチャー（ネタ収集）
Log "リサーチャー実行中..."
$result = & $CLAUDE -p (Get-Content "$BOT_DIR\agents\researcher.md" -Raw -Encoding UTF8) --cwd "$BOT_DIR" 2>&1
Log "リサーチャー完了"

# 4. ライター（投稿10本生成）
Log "ライター実行中..."
$result = & $CLAUDE -p (Get-Content "$BOT_DIR\agents\writer.md" -Raw -Encoding UTF8) --cwd "$BOT_DIR" 2>&1
Log "ライター完了"

# 5. スーパーバイザー（ヘルスチェック）
Log "スーパーバイザー実行中..."
$result = & python "$BOT_DIR\agents\supervisor.py" 2>&1
Log $result
Log "スーパーバイザー完了"

Log "=== daily_run 完了 ==="
