import json
import time
from facebook_cli import worker
from facebook_cli.session import FacebookSession

worker.stop_worker("default")
time.sleep(2)

with FacebookSession("default") as s:
    s.page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
    s.page.wait_for_timeout(4000)
    print(json.dumps({"title": s.page.title(), "url": s.page.url}))
