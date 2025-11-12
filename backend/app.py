# from fastapi import FastAPI, UploadFile, File
# from fastapi.middleware.cors import CORSMiddleware
# import tempfile, os
# from ai_resume_screen import extract_text_from_docx, analyze_resume

# app = FastAPI()


# @app.get("/")
# def home():
#     return {"message": "Backend is running successfully!"}

# # Allow React frontend to access backend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.post("/analyze/")
# async def analyze(jd: UploadFile = File(...), resumes: list[UploadFile] = File(...)):
#     jd_temp = tempfile.NamedTemporaryFile(delete=False)
#     jd_temp.write(await jd.read())
#     jd_temp.close()

#     jd_text = extract_text_from_docx(jd_temp.name)
#     os.unlink(jd_temp.name)

#     results = []
#     for resume in resumes:
#         temp = tempfile.NamedTemporaryFile(delete=False)
#         temp.write(await resume.read())
#         temp.close()

#         resume_text = extract_text_from_docx(temp.name)
#         os.unlink(temp.name)

#         analysis = analyze_resume(jd_text, resume_text)
#         candidate_name = resume.filename.replace(".docx", "")
#         results.append({
#             "Name": candidate_name,
#             **analysis
#         })

#     return {"results": results}


# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 10000))
#     uvicorn.run(app, host="0.0.0.0", port=port)


# @app.get("/")
# def home():
#     return {"message": "Backend is running successfully!"}

# backend/app.py

import logging
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import tempfile
import os
from ai_resume_screen import extract_text_from_docx, analyze_resumes
import docx2txt

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend_app")

def extract_text(file_path, suffix):
    """Extract text from JD or resume file."""
    try:
        if suffix == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif suffix == ".docx":
            return extract_text_from_docx(file_path)
        else:
            # Skip PDF and others for now
            return ""
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return ""

@app.post("/analyze/")
async def analyze(jd: UploadFile = File(...), resumes: List[UploadFile] = File(...)):
    try:
        logger.info(f"Received JD: {jd.filename} size={jd.size} suffix={os.path.splitext(jd.filename)[1]}")

        # Save JD temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(jd.filename)[1]) as jd_temp:
            jd_temp.write(await jd.read())
            jd_temp.flush()
            jd_text = extract_text(jd_temp.name, os.path.splitext(jd.filename)[1])
        os.unlink(jd_temp.name)

        # Process resumes
        resume_data = []
        for resume in resumes:
            logger.info(f"Received resume: {resume.filename} size={resume.size} suffix={os.path.splitext(resume.filename)[1]}")
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume.filename)[1]) as r_temp:
                r_temp.write(await resume.read())
                r_temp.flush()
                text = extract_text(r_temp.name, os.path.splitext(resume.filename)[1])
            os.unlink(r_temp.name)
            resume_data.append((resume.filename, text))

        # Analyze resumes
        results = analyze_resumes(jd_text, resume_data)

        logger.info(f"Returning {len(results)} results")
        return JSONResponse(results)

    except Exception as e:
        logger.exception("Error analyzing resumes")
        return JSONResponse({"error": str(e)}, status_code=500)
