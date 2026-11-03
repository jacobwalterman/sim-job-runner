from celery import Celery
from db import Job, SessionLocal
from simulations import SIMULATIONS

celery_app = Celery("simjobs", broker="redis://localhost:6379/0")

@celery_app.task
def run_job(job_id):
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        if job is None:
            return
        try:
            fn = SIMULATIONS[job.simulation]
            result = fn(**job.params)
        except Exception as e:
            job.status = "failed"
            job.result = {"error": str(e)}
            session.commit()
            return
        job.result = result
        job.status = "done"
        session.commit()
