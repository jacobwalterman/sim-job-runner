from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import Job, SessionLocal

class JobCreate(BaseModel):
    simulation: str
    params: dict

app = FastAPI()


def run_heat(steps: int, alpha: float):
    return {"final_temp": 0.5 * alpha * steps}   # fake for now

def run_transmission_line(decay_rate: float):
    return {"decay_rate": decay_rate}   # fake for now

SIMULATIONS = {
        "heat": run_heat,
        "transmission-line": run_transmission_line
        }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/jobs")
def create_job(job: JobCreate):
    try: 
        fn = SIMULATIONS[job.simulation]
    except KeyError:
        raise HTTPException(status_code=400, detail="unknown simulation")
    
    try: 
        result = fn(**job.params)
    except TypeError:
        raise HTTPException(status_code=400, detail="invalid params")

    with SessionLocal() as session:
        some_job = Job(simulation=job.simulation, params=job.params, status="done", result=result)
        session.add(some_job)
        session.commit()
        return {"id": some_job.id}


@app.get("/jobs/{id}")
def get_job(id: int):
    with SessionLocal() as session:
        job = session.get(Job, id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job ID")
        return {
            "id": job.id,
            "simulation": job.simulation, 
            "params": job.params,
            "status": job.status,
            "result": job.result
            }
