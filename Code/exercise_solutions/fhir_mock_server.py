# fhir_mock_server.py

from fastapi import FastAPI, HTTPException
from fhir.resources.patient import Patient
import uvicorn
import uuid

app = FastAPI()

patients_db = {}

@app.post("/Patient")
def create_patient(patient: Patient):
    patient.id = str(uuid.uuid4())
    patients_db[patient.id] = patient
    return patient

@app.get("/Patient/{patient_id}")
def read_patient(patient_id: str):
    patient = patients_db.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)