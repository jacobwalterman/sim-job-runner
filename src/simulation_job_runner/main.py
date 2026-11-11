from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from simulation_job_runner.db import Job, SessionLocal
from simulation_job_runner.simulations import SIMULATIONS
from simulation_job_runner.tasks import run_job

class JobCreate(BaseModel):
    simulation: str
    params: dict

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/jobs")
def create_job(job: JobCreate):
    if job.simulation not in SIMULATIONS: 
        raise HTTPException(status_code=400, detail="unknown simulation")
    with SessionLocal() as session:
        some_job = Job(simulation=job.simulation, params=job.params, status="queued", result=None)
        session.add(some_job)
        session.commit()
        job_id = some_job.id
    run_job.delay(job_id)
    return {"id": job_id}

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
