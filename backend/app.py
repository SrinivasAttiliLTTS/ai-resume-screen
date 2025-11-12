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
import os
import tempfile
import logging
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai_resume_screen import extract_text_from_file, analyze_scores

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend_app")

app = FastAPI(title="AI Resume Screening Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for production narrow to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/analyze/")
async def analyze(jd: UploadFile = File(...), resumes: list[UploadFile] = File(...)):
    try:
        # Save JD bytes to temp file
        jd_suffix = os.path.splitext(jd.filename)[1] or ".docx"
        jd_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=jd_suffix)
        jd_bytes = await jd.read()
        jd_tmp.write(jd_bytes)
        jd_tmp.flush()
        jd_tmp.close()
        logger.info("Received JD: %s size=%d suffix=%s", jd.filename, len(jd_bytes), jd_suffix)

        # Extract JD text (robust)
        jd_text = extract_text_from_file(jd_tmp.name)
        if not jd_text or len(jd_text.strip()) == 0:
            logger.warning("JD extraction produced empty text for file: %s", jd.filename)

        results = []
        for resume in resumes:
            res_suffix = os.path.splitext(resume.filename)[1] or ".docx"
            res_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=res_suffix)
            res_bytes = await resume.read()
            res_tmp.write(res_bytes)
            res_tmp.flush()
            res_tmp.close()
            logger.info("Received resume: %s size=%d suffix=%s", resume.filename, len(res_bytes), res_suffix)

            # Extract resume text robustly
            resume_text = extract_text_from_file(res_tmp.name)
            if not resume_text or len(resume_text.strip()) == 0:
                logger.warning("Resume extraction empty: %s", resume.filename)

            # If extract_text_from_file returned empty, record helpful message instead of crashing
            if not resume_text:
                results.append({
                    "Name": resume.filename,
                    "Strengths": "",
                    "Missing": "Could not extract text (unsupported or corrupted file).",
                    "Primary Score": 0.0,
                    "Secondary Score": 0.0,
                    "Overall Score": 0.0
                })
            else:
                analysis = analyze_scores(jd_text, resume_text)
                results.append({"Name": resume.filename, **analysis})

            # cleanup
            try:
                os.unlink(res_tmp.name)
            except Exception:
                logger.exception("Failed to delete temp file %s", res_tmp.name)

        # cleanup jd
        try:
            os.unlink(jd_tmp.name)
        except Exception:
            logger.exception("Failed to delete JD temp file %s", jd_tmp.name)

        return JSONResponse({"results": results})

    except Exception as e:
        logger.exception("Unhandled exception in /analyze: %s", e)
        # Return safe response with error message, frontend won't crash on missing key
        return JSONResponse({"results": [], "error": str(e)}, status_code=500)
