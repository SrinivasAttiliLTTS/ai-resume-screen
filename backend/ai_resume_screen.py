# import docx2txt
# import nltk
# import re

# nltk.download('punkt', quiet=True)

# # def extract_text_from_docx(file_path):
# #     return docx2txt.process(file_path)
# def extract_text_from_docx(file_path):
#     try:
#         return docx2txt.process(file_path)
#     except Exception as e:
#         return f"Error reading file: {str(e)}"
    
# def tokenize_text(text):
#     return [word.lower() for word in nltk.word_tokenize(text) if word.isalpha()]

# def analyze_resume(jd_text, resume_text):
#     jd_tokens = tokenize_text(jd_text)
#     resume_tokens = tokenize_text(resume_text)

#     # Extract skill sections
#     jd_primary = extract_section(jd_text, "Primary Skills")
#     jd_secondary = extract_section(jd_text, "Secondary Skills")
#     jd_other = extract_section(jd_text, "Other Skills")

#     primary_score, primary_strengths, primary_missing = score_section(jd_primary, resume_tokens)
#     secondary_score, secondary_strengths, secondary_missing = score_section(jd_secondary, resume_tokens)

#     # Weighted average
#     overall_score = round((primary_score * 0.8) + (secondary_score * 0.2), 2)

#     strengths = list(set(primary_strengths + secondary_strengths))
#     missing = list(set(primary_missing + secondary_missing))

#     return {
#         "Strengths": ", ".join(strengths) if strengths else "None",
#         "Missing": ", ".join(missing) if missing else "None",
#         "Primary_Score": round(primary_score, 2),
#         "Secondary_Score": round(secondary_score, 2),
#         "Overall_Score": overall_score
#     }

# def extract_section(text, section_name):
#     pattern = rf"{section_name}:(.*?)(?:\n[A-Z]|$)"
#     match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
#     if match:
#         return [word.strip().lower() for word in re.split(r'[,\n]', match.group(1)) if word.strip()]
#     return []

# def score_section(skill_list, resume_tokens):
#     if not skill_list:
#         return 0, [], []
#     matched = [skill for skill in skill_list if skill.lower() in resume_tokens]
#     score = (len(matched) / len(skill_list)) * 100
#     missing = list(set(skill_list) - set(matched))
#     return score, matched, missing

# backend/ai_resume_screen.py
import os
import re
import docx2txt
import fitz  # PyMuPDF
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_resume_screen")

def extract_text_from_file(path: str) -> str:
    """
    Inspect extension and extract text accordingly.
    Supports: .docx, .pdf, .txt
    Returns text (empty string if extraction fails) and logs errors.
    """
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".docx":
            # docx is actually a zip archive; docx2txt will raise BadZipFile if not valid
            text = docx2txt.process(path)
            return text or ""
        elif ext == ".pdf":
            text = ""
            with fitz.open(path) as pdf:
                for page in pdf:
                    text += page.get_text()
            return text or ""
        elif ext == ".txt":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        else:
            # attempt safe fallback: try pdf then docx then text
            try:
                with fitz.open(path) as pdf:
                    text = "".join(p.get_text() for p in pdf)
                    if text.strip():
                        return text
            except Exception:
                pass
            try:
                text = docx2txt.process(path)
                if text and text.strip():
                    return text
            except Exception:
                pass
            # final fallback: read binary as text
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                logger.exception("Unable to extract text from unknown file type: %s", path)
                return ""
    except Exception as e:
        # Log full exception for Render logs and return an empty string
        logger.exception("Error extracting text from %s: %s", path, e)
        return ""

def normalize(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"[^a-z0-9\s\+\#\.\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def analyze_scores(jd_text: str, resume_text: str, primary_skills: list = None, secondary_skills: list = None):
    """
    Simple keyword-based scoring.
    primary_skills / secondary_skills optional: if provided, use them; else infer from JD by simple split.
    Returns dict with exactly the fields frontend expects.
    """
    jd_norm = normalize(jd_text)
    resume_norm = normalize(resume_text)

    jd_tokens = jd_norm.split()
    resume_tokens = set(resume_norm.split())

    # If explicit lists not provided, naive extraction from JD:
    if not primary_skills and not secondary_skills:
        # attempt to find labeled sections "Primary Skills:" etc.
        primary = []
        secondary = []
        m1 = re.search(r"primary skills?\s*[:\-]\s*(.*?)(?:secondary skills?:|\n\n|$)", jd_text, flags=re.IGNORECASE | re.DOTALL)
        m2 = re.search(r"secondary skills?\s*[:\-]\s*(.*?)(?:other skills?:|\n\n|$)", jd_text, flags=re.IGNORECASE | re.DOTALL)
        if m1:
            primary = [s.strip().lower() for s in re.split(r'[,\n;/]+', m1.group(1)) if s.strip()]
        if m2:
            secondary = [s.strip().lower() for s in re.split(r'[,\n;/]+', m2.group(1)) if s.strip()]
        # fallback: split first N tokens as primary, next as secondary
        if not primary:
            tokens = [t for t in jd_tokens if len(t) > 1]
            primary = tokens[:5]
            secondary = tokens[5:10]
    else:
        primary = [s.lower() for s in primary_skills or []]
        secondary = [s.lower() for s in secondary_skills or []]

    # match
    matched_primary = [p for p in primary if p in resume_norm]
    matched_secondary = [s for s in secondary if s in resume_norm]

    primary_score = round((len(matched_primary) / len(primary) * 100), 2) if primary else 0.0
    secondary_score = round((len(matched_secondary) / len(secondary) * 100), 2) if secondary else 0.0

    overall = round(primary_score * 0.8 + secondary_score * 0.2, 2)
    overall = min(100.0, overall)

    strengths = matched_primary + matched_secondary
    missing = [p for p in primary if p not in matched_primary] + [s for s in secondary if s not in matched_secondary]

    return {
        "Strengths": ", ".join(strengths) if strengths else "",
        "Missing": ", ".join(missing) if missing else "",
        "Primary Score": primary_score,
        "Secondary Score": secondary_score,
        "Overall Score": overall
    }
