import json
import statistics
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "http://localhost:8000/api/chat"
QUESTION = "What does FowForge do?"
REQUESTS = 10
CONCURRENCY = 3


def one_request(_):
    payload = json.dumps({"question": QUESTION}).encode()
    request = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response.read()
            return (time.perf_counter() - started) * 1000, response.status
    except Exception:
        return (time.perf_counter() - started) * 1000, 0


if __name__ == "__main__":
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        results = list(pool.map(one_request, range(REQUESTS)))
    elapsed = time.perf_counter() - started
    latencies = sorted(x[0] for x in results)
    successes = sum(status == 200 for _, status in results)
    p95_index = max(0, int(len(latencies) * 0.95) - 1)
    print(f"requests={REQUESTS} concurrency={CONCURRENCY} successes={successes}")
    print(f"p50_ms={statistics.median(latencies):.2f}")
    print(f"p95_ms={latencies[p95_index]:.2f}")
    print(f"throughput_rps={REQUESTS / elapsed:.2f}")
