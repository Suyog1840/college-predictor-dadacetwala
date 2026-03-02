from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

try:
    # When running from the root repository (e.g. Railway / Production)
    import backend_scripts.simulation_engine as se  
except ImportError:
    # When running locally inside the backend_scripts folder
    import simulation_engine as se  


app = FastAPI()

# Allow CORS so Next.js can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://dadacetwala-omega.vercel.app"  # Update with your Next.js URL in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the expected JSON payload matching the student dictionary structure
class StudentData(BaseModel):
    scores: Dict[str, float]
    category: str
    gender: str
    homeUniversity: str
    branchPreference: Optional[List[str]] = None
    districtPreference: Optional[List[str]] = None

@app.post("/predict")
def get_predictions(student: StudentData):
    # Convert Pydantic model to dictionary layout expected by simulation_engine
    student_dict = student.dict()
    
    # Run the prediction
    try:
        predictions = se.predict(student_dict)
        return {"success": True, "results": predictions}
    except Exception as e:
        return {"success": False, "error": str(e)}

# To run:
# pip install fastapi uvicorn
# uvicorn server:app --reload
