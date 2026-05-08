# setup_scheduler.ps1 - 管理者権限で1回だけ実行してください

$BOT_DIR = "C:\Users\isesa\OneDrive\Desktop\threads-bot"

# daily_run: 毎朝7時
$action1 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$BOT_DIR\scripts\daily_run.ps1`""
$trigger1 = New-ScheduledTaskTrigger -Daily -At "07:00"
Register-ScheduledTask -TaskName "ThreadsBot-DailyRun" -Action $action1 -Trigger $trigger1 -RunLevel Highest -Force
Write-Host "OK: ThreadsBot-DailyRun 登録完了（毎朝7時）"

# post_cron: 2時間おき（9時〜23時）
$triggers = @()
foreach ($hour in @(9,11,13,15,17,19,21,23)) {
    $triggers += New-ScheduledTaskTrigger -Daily -At "$($hour):00"
}
$action2 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$BOT_DIR\scripts\post_cron.ps1`""
Register-ScheduledTask -TaskName "ThreadsBot-PostCron" -Action $action2 -Trigger $triggers -RunLevel Highest -Force
Write-Host "OK: ThreadsBot-PostCron 登録完了（2時間おき）"

# token_refresh: 月2回（1日と15日）
$action3 = New-ScheduledTaskAction -Execute "python" -Argument "`"$BOT_DIR\scripts\token_refresh.py`""
$trigger3a = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At "09:00"
$trigger3b = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 15 -At "09:00"
Register-ScheduledTask -TaskName "ThreadsBot-TokenRefresh" -Action $action3 -Trigger @($trigger3a, $trigger3b) -RunLevel Highest -Force
Write-Host "OK: ThreadsBot-TokenRefresh 登録完了（毎月1日・15日）"

Write-Host "`nすべてのタスクが登録されました！"
