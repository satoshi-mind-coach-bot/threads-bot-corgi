import json
import os
import sys
import urllib.request
import urllib.parse

def refresh_token(token):
    url = "https://graph.threads.net/refresh_access_token"
    params = urllib.parse.urlencode({
        "grant_type": "th_refresh_token",
        "access_token": token
    })
    with urllib.request.urlopen(f"{url}?{params}") as res:
        return json.loads(res.read().decode("utf-8"))

token = os.environ.get("THREADS_ACCESS_TOKEN")
if not token:
    print("ERROR: THREADS_ACCESS_TOKEN not set", file=sys.stderr)
    sys.exit(1)

result = refresh_token(token)
new_token = result.get("access_token")
if not new_token:
    print(f"ERROR: {result}", file=sys.stderr)
    sys.exit(1)

print(new_token)
