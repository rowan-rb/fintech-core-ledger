import asyncio
import httpx
import time
import os
import sys
import random
import statistics

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from benchmark.setup_accounts import setup_accounts

API_URL = "http://127.0.0.1:8000/transfer"

async def worker(client, account_ids, duration, results):
    end_time = time.time() + duration
    while time.time() < end_time:
        from_acc = random.choice(account_ids)
        to_acc = random.choice(account_ids)
        while from_acc == to_acc:
            to_acc = random.choice(account_ids)
            
        payload = {
            "from_account": str(from_acc),
            "to_account": str(to_acc),
            "amount": 10.00
        }
        start = time.perf_counter()
        try:
            response = await client.post(API_URL, json=payload, timeout=5.0)
            latency = (time.perf_counter() - start) * 1000 # ms
            results.append((latency, response.status_code == 200))
        except Exception:
            latency = (time.perf_counter() - start) * 1000
            results.append((latency, False))

async def run_benchmark(num_users=50, duration=10):
    print(f"--- BENCHMARK REAL: {num_users} usuarios concurrentes durante {duration}s ---")
    account_ids = setup_accounts(1000)

    results = []
    limits = httpx.Limits(max_connections=num_users, max_keepalive_connections=num_users)
    
    async with httpx.AsyncClient(limits=limits) as client:
        start_time = time.perf_counter()
        tasks = [worker(client, account_ids, duration, results) for _ in range(num_users)]
        await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

    latencies = [r[0] for r in results]
    successes = sum(1 for r in results if r[1])
    total_requests = len(results)
    failures = total_requests - successes
    
    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    tps = total_requests / total_time
    
    print(f"\n--- RESULTADOS REALES ---")
    print(f"Peticiones Totales: {total_requests}")
    print(f"Throughput: {tps:.2f} req/s")
    print(f"Latencia p50: {p50:.2f} ms")
    print(f"Latencia p95: {p95:.2f} ms")
    print(f"Latencia p99: {p99:.2f} ms")
    print(f"Exitos: {successes} | Fallos: {failures}")
    print("-" * 40)

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_benchmark(num_users=50, duration=10))
