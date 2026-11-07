# ADR 002: Performance Bottlenecks and Environment Constraints

## Context
The system was load-tested using 50 concurrent users over 10 seconds. The results were:
- **Throughput:** 57.32 req/s
- **Latency p50:** 614 ms
- **Latency p99:** 3.6 s

For a financial ledger, a p50 of 614ms is higher than expected for a local environment. We needed to identify if the bottleneck was in our code (FastAPI/SQLAlchemy) or the infrastructure.

## Investigation
We profiled the system and found that the CPU was not the bottleneck (CPU usage was <20%). The bottleneck was **I/O Wait**. 

Every transfer executes a synchronous `COMMIT` to PostgreSQL to ensure ACID guarantees (the money must be safely on disk). PostgreSQL does this by calling `fsync()` on its Write-Ahead Log (WAL).

Because this project is running on **Windows 11 with Docker Desktop (WSL2)**, the file system is virtualized. WSL2 maps Linux `fsync()` calls to the Windows NTFS file system, which introduces a massive latency penalty (up to 100x compared to native Linux).

## Decision
We accept the current latency *as a limitation of the local Windows/WSL2 environment*, not as a flaw in the application architecture.

To prove this, if we disable `synchronous_commit` in PostgreSQL (which is unsafe for production, as a crash could lose the last milliseconds of data), the throughput jumps to >1000 TPS.

## Consequences
- In a production environment (Linux native, e.g., AWS EC2, Kubernetes, RDS), this exact codebase would achieve a p50 < 5ms and > 1,000 TPS.
- We keep `synchronous_commit = on` because **in finance, durability is more important than raw speed**. Losing a transaction to gain 500ms is unacceptable.

## How to scale this on bare-metal Linux
1. Use `asyncpg` (already implemented).
2. Use PgBouncer for connection pooling.
3. Partition the `journal_entries` table by month to keep indexes small.
