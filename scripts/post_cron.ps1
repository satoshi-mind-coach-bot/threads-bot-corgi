# post_cron.ps1 - 2時間おきに1件投稿

$BOT_DIR = "C:\Users\isesa\OneDrive\Desktop\threads-bot"
$LOG = "$BOT_DIR\logs\post_cron.log"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content -Path $LOG -Value $line -Encoding UTF8
}

if (Test-Path "$BOT_DIR\KILL_SWITCH") {
    Log "KILL_SWITCH active. Exiting."
    exit 0
}

Log "投稿実行中..."
$result = & python "$BOT_DIR\agents\poster.py" 2>&1
Log $result
Log "投稿処理完了"
