# Simulation Job Runner

A small HTTP service for running simulations asynchronously. Clients submit a job over a REST API, a Celery worker runs it in the background, and the job's status and result are stored in Postgres so they can be polled later.

## How it works

```
client ──POST /jobs──▶ FastAPI ──insert (queued)──▶ Postgres
                          │
                          └──run_job.delay(id)──▶ Redis ──▶ Celery worker
                                                               │
client ◀─GET /jobs/{id}─ FastAPI ◀──── status/result ── Postgres ◀┘
```

All code lives in the `simulation_job_runner` package under `src/`.

| Module | Purpose |
| --- | --- |
| `main.py` | FastAPI app: `/health`, `POST /jobs`, `GET /jobs/{id}` |
| `tasks.py` | Celery app (Redis broker) and the `run_job` task |
| `db.py` | SQLAlchemy engine, session factory and the `Job` model |
| `simulations.py` | Simulation functions and the `SIMULATIONS` registry |

### Job lifecycle

A job's `status` is one of:

- `queued` – created by the API, waiting for a worker
- `running` – picked up by a worker
- `done` – finished; `result` holds the simulation output
- `failed` – the simulation raised; `result` is `{"error": "<message>"}`

## Requirements

- Python 3.10+
- PostgreSQL, with a database named `simjobs`
- Redis

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Start Postgres and Redis. For example, with Docker:

```bash
docker run -d --name simjobs-pg -p 5432:5432 \
  -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=simjobs postgres
docker run -d --name simjobs-redis -p 6379:6379 redis
```

### Configuration

Connection settings are currently hardcoded:

- Postgres: `postgresql+psycopg://postgres:dev@localhost:5432/simjobs` (`src/simulation_job_runner/db.py`)
- Redis broker: `redis://localhost:6379/0` (`src/simulation_job_runner/tasks.py`)

The `jobs` table is created automatically when `simulation_job_runner.db` is imported; there are no migrations.

## Running

Start the API and a worker in separate terminals (with the venv active):

```bash
# API server
uvicorn simulation_job_runner.main:app --reload

# Celery worker
celery -A simulation_job_runner.tasks.celery_app worker --loglevel=info
```

The API is served at http://localhost:8000, with interactive docs at http://localhost:8000/docs.

## API

### `GET /health`

```json
{"status": "ok"}
```

### `POST /jobs`

Create a job and enqueue it. Returns `400` if `simulation` isn't registered.

```bash
curl -X POST localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"simulation": "heat", "params": {"steps": 100, "alpha": 0.1}}'
```

```json
{"id": 1}
```

### `GET /jobs/{id}`

Fetch a job's current state. Returns `404` if the ID doesn't exist.

```bash
curl localhost:8000/jobs/1
```

```json
{
  "id": 1,
  "simulation": "heat",
  "params": {"steps": 100, "alpha": 0.1},
  "status": "done",
  "result": {"final_temp": 5.0}
}
```

## Simulations

Registered in `SIMULATIONS` in `src/simulation_job_runner/simulations.py`. `params` are passed to the function as keyword arguments.

| Name | Params | Result | Status |
| --- | --- | --- | --- |
| `heat` | `steps: int`, `alpha: float` | `{"final_temp": float}` | Placeholder implementation |
| `transmission-line` | `n: list[int]`, `l: list[float]`, `c: list[float]`, `k: list[float]` | `{"decay_rate": float}` | Calls `tlw.get_decay_rate_raw` |

For `transmission-line`, the four lists hold one value per segment (for example `n = [n1, n2, n3, n4]`): `n` holds integer values, `l` is the position of the wave end point, `c` is the wave speed and `k` is the gain. For example:

```bash
curl -X POST localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"simulation": "transmission-line", "params": {
        "n": [15, 20, 25, 15],
        "l": [1.0, 3.0, 7.0, 7.5],
        "c": [7.0, 4.0, 3.0, 4.0],
        "k": [1.0, 2.0, 3.0, 4.0]}}'
```

### Adding a simulation

1. Write a function in `src/simulation_job_runner/simulations.py` that takes keyword arguments and returns a JSON-serializable `dict`.
2. Add it to the `SIMULATIONS` dict under the name clients will use.

Exceptions raised by the function are caught by the worker and recorded on the job as `failed`.
