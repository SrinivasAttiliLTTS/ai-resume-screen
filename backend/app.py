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

# backend/app.py

import os
import tempfile
import logging
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ai_resume_screen import extract_text_from_docx, analyze_resumes
import fitz  # PyMuPDF for PDF
import docx2txt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend_app")

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text(file: UploadFile):
    """Universal extractor with detailed logging"""
    try:
        suffix = os.path.splitext(file.filename)[1].lower()
        logger.info(f"Extracting text from file: {file.filename} (type: {suffix})")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        if suffix == ".docx":
            text = extract_text_from_docx(tmp_path)
        elif suffix == ".pdf":
            text = ""
            with fitz.open(tmp_path) as pdf:
                for page in pdf:
                    text += page.get_text()
        elif suffix == ".txt":
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        logger.info(f"Extracted {len(text)} characters from {file.filename}")
        return text

    except Exception as e:
        logger.error(f"Error extracting text from {file.filename}: {e}")
        return ""

@app.post("/analyze/")
async def analyze(jd: UploadFile = File(...), resumes: list[UploadFile] = File(...)):
    try:
        logger.info(f"Received JD: {jd.filename} size={jd.size} suffix={os.path.splitext(jd.filename)[1]}")
        jd_text = extract_text(jd)

        if not jd_text.strip():
            logger.error("JD extraction returned empty text")
            raise HTTPException(status_code=400, detail="Failed to extract JD text")

        resume_data = []
        for resume in resumes:
            logger.info(f"Received resume: {resume.filename} size={resume.size} suffix={os.path.splitext(resume.filename)[1]}")
            text = extract_text(resume)
            if text.strip():
                resume_data.append((resume.filename, text))
            else:
                logger.warning(f"No text extracted from {resume.filename}")

        results = analyze_resumes(jd_text, resume_data)
        logger.info(f"Returning {len(results)} results")

        return JSONResponse(content={"results": results})

    except Exception as e:
        logger.error(f"Unhandled error in analyze(): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "AI Resume Screening Backend running ✅"}
