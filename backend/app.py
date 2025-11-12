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

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from ai_resume_screen import analyze_resume, extract_text_from_docx

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Backend is running successfully!"}

@app.post("/analyze/")
async def analyze(jd: UploadFile = File(...), resumes: list[UploadFile] = File(...)):
    # Read JD file
    jd_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    jd_bytes = await jd.read()
    jd_temp.write(jd_bytes)
    jd_temp.close()

    # Validate JD file
    if not jd.filename.endswith(".docx"):
        return {"error": f"JD file '{jd.filename}' is not a .docx file"}

    jd_text = extract_text_from_docx(jd_temp.name)
    os.unlink(jd_temp.name)

    results = []

    for resume in resumes:
        if not resume.filename.endswith(".docx"):
            results.append({
                "Name": resume.filename,
                "Strengths": "",
                "Missing": f"Invalid file format ({resume.filename})",
                "Primary Score": 0,
                "Secondary Score": 0,
                "Overall Score": 0
            })
            continue

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        temp_bytes = await resume.read()
        temp.write(temp_bytes)
        temp.close()

        resume_text = extract_text_from_docx(temp.name)
        os.unlink(temp.name)

        analysis = analyze_resume(jd_text, resume_text)
        candidate_name = resume.filename.replace(".docx", "")

        results.append({
            "Name": candidate_name,
            **analysis
        })

    return {"results": results}


@app.get("/")
async def root():
    return {"message": "AI Resume Screening Backend is Live ✅"}
