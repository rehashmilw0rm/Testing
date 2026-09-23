"""Tiny JSON-over-HTTP helper built on the standard library."""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "polybot/0.1 (+paper-trading)"


def get_json(url, params=None, timeout=10.0, retries=2):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # 4xx is not worth retrying.
            if 400 <= e.code < 500:
                raise
            last_err = e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = e
        time.sleep(0.5 * (2 ** attempt))
    raise last_err
