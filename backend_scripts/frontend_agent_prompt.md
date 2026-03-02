### 1. Deploying this Python Backend (API)

To deploy this Python model so the internet (and your Next.js app) can reach it:

1. **Push to GitHub**: Commit the `d:\PythonScript` folder to a new GitHub repository. Ensure `master_cutoff_data.xlsx`, `trend_table.xlsx`, `college_meta.xlsx`, `branch_names.csv`, `server.py`, `simulation_engine.py`, `trend_table.py`, and `requirements.txt` are included.
2. **Deploy Platform**: Use a platform like **Render**, **Railway**, or **DigitalOcean App Platform** (Vercel is not recommended for heavy Python APIs that load large datasets into memory).
3. **Setup**:
    * **Build Command**: `pip install -r requirements.txt`
    * **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT` (The platform will automatically inject the `$PORT` environment variable).
4. **Acquire URL**: Once deployed, the platform will give you a public URL (e.g., `https://my-college-api.onrender.com`).

---

### 2. Prompt for the Next.js Agent (`dadacetwala` project)

Once your Python backend is deployed, you can give the following prompt to the agent helping you build the Next.js frontend:

> **Prompt:**  
> "I have a Python backend running a college prediction model, and I need to integrate it into this Next.js app. The backend is an exposed REST API built with FastAPI. We need to create a server action or a client-side API call that sends a POST form payload to `[YOUR_DEPLOYED_PYTHON_URL]/predict`.  
>   
> **Here is the JSON payload structure the API expects:**
> ```json
> {
>   "scores": {
>     "MHTCET": 95.0,
>     "JEE": 88.0
>   },
>   "category": "TFWS",
>   "gender": "Male",
>   "homeUniversity": "Savitribai Phule Pune University",
>   "branchPreference": ["Computer Engineering", "Information Technology"],
>   "districtPreference": ["Pune", "Mumbai"]
> }
> ```
> *(Note: The inner keys inside `scores`, like "MHTCET" or "JEE", must precisely match the exams the student has scores for. `branchPreference` and `districtPreference` are optional arrays of strings).*
>  
> **Here is the JSON Response structure the API returns on success:**
> ```json
> {
>   "success": true,
>   "results": [
>     {
>       "examType": "MHTCET",
>       "collegeCode": 6006,
>       "collegeName": "College of Engineering, Pune",
>       "branchCode": "600624510",
>       "branchName": "Electrical Engineering",
>       "district": "Pune",
>       "weighted_cutoff": 99.8,
>       "standard_cutoff": 99.8,
>       "probability": 78.4
>     }
>   ]
> }
> ```  
> Please create:
> 1. A secure environmental variable `NEXT_PUBLIC_PREDICTION_API_URL` to store this endpoint.
> 2. A data-fetching function (like a Server Action) that accepts the user's form data, builds the JSON payload correctly, and handles the `fetch` to this API.  
> 3. Ensure the UI can elegantly display the returned array of `results` (top matched colleges), handling loading states and potential errors."
