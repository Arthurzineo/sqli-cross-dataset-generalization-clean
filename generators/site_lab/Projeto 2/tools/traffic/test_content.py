"""Small isolated smoke test: exactly five live content-service calls."""

import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen


BASE_URL = os.environ.get("TRAFFIC_CONTENT_URL", "http://127.0.0.1:8877")
CASES = [
    ("comment", "join"),
    ("reply", "where"),
    ("question", "group-by"),
    ("searchterm", "sleep"),
    ("tags", "select"),
]


for kind, topic in CASES:
    url = f"{BASE_URL}/gen?{urlencode({'type': kind, 'topic': topic})}"
    with urlopen(url, timeout=45) as response:  # noqa: S310 - local PoC endpoint
        payload = json.load(response)
    print(json.dumps(payload, ensure_ascii=False))
