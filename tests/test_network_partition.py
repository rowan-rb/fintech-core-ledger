import pytest
import time
import httpx
import requests
import os
import sys
import subprocess
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fintech_ledger.db import SessionLocal
from fintech_ledger.models import Account

TOXIPROXY_API = "http://127.0.0.1:8474"
API_URL = "http://127.0.0.1:8001/transfer" # Puerto distinto para no chocar con verify.ps1

def test_network_partition_causes_timeout():
    """Simula caída de red usando Toxiproxy y un Uvicorn temporal."""
    db = SessionLocal()
    acc1 = Account(name="Sender", account_type="ASSET")
    acc2 = Account(name="Receiver", account_type="ASSET")
    db.add(acc1)
    db.add(acc2)
    db.commit()
    from_acc = str(acc1.id)
    to_acc = str(acc2.id)
    db.close()

    # Configurar Toxiproxy
    requests.post(f"{TOXIPROXY_API}/proxies", json={
        "name": "postgres_proxy",
        "listen": "0.0.0.0:5434",
        "upstream": "postgres:5432",
        "enabled": True
    }, timeout=5)

    # 1. Arrancar una API temporal apuntando a Toxiproxy (5434)
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+asyncpg://fintech:fintech@localhost:5434/fintech"
    
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "fintech_ledger.api:app", "--port", "8001"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(3) # Dar tiempo a que arranque

    # 2. Inyectar latencia de 10 segundos
    requests.post(f"{TOXIPROXY_API}/proxies/postgres_proxy/toxics", json={
        "name": "latency_down",
        "type": "latency",
        "attributes": {"latency": 10000}
    }, timeout=5)
    
    print("\nRED CAÍDA: Inyectando 10 segundos de latencia a Postgres...")
    
    # 3. Hacer petición y verificar timeout
    start = time.time()
    try:
        httpx.post(API_URL, json={
            "from_account": from_acc,
            "to_account": to_acc,
            "amount": 10.00
        }, timeout=3.0)
        assert False, "La petición debería haber fallado por timeout."
    except httpx.TimeoutException:
        elapsed = time.time() - start
        print(f"Timeout detectado correctamente (el cliente se rindió después de {elapsed:.2f}s).")
    finally:
        # 4. Limpiar: restaurar red y matar API temporal
        requests.delete(f"{TOXIPROXY_API}/proxies/postgres_proxy/toxics/latency_down", timeout=5)
        print("Red restaurada.")
        api_process.terminate()
        api_process.wait(timeout=5)
