import docx2txt
import nltk
import re

nltk.download('punkt', quiet=True)

def extract_text_from_docx(file_path):
    return docx2txt.process(file_path)

def tokenize_text(text):
    return [word.lower() for word in nltk.word_tokenize(text) if word.isalpha()]

def analyze_resume(jd_text, resume_text):
    jd_tokens = tokenize_text(jd_text)
    resume_tokens = tokenize_text(resume_text)

    # Extract skill sections
    jd_primary = extract_section(jd_text, "Primary Skills")
    jd_secondary = extract_section(jd_text, "Secondary Skills")
    jd_other = extract_section(jd_text, "Other Skills")

    primary_score, primary_strengths, primary_missing = score_section(jd_primary, resume_tokens)
    secondary_score, secondary_strengths, secondary_missing = score_section(jd_secondary, resume_tokens)

    # Weighted average
    overall_score = round((primary_score * 0.8) + (secondary_score * 0.2), 2)

    strengths = list(set(primary_strengths + secondary_strengths))
    missing = list(set(primary_missing + secondary_missing))

    return {
        "Strengths": ", ".join(strengths) if strengths else "None",
        "Missing": ", ".join(missing) if missing else "None",
        "Primary_Score": round(primary_score, 2),
        "Secondary_Score": round(secondary_score, 2),
        "Overall_Score": overall_score
    }

def extract_section(text, section_name):
    pattern = rf"{section_name}:(.*?)(?:\n[A-Z]|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return [word.strip().lower() for word in re.split(r'[,\n]', match.group(1)) if word.strip()]
    return []

def score_section(skill_list, resume_tokens):
    if not skill_list:
        return 0, [], []
    matched = [skill for skill in skill_list if skill.lower() in resume_tokens]
    score = (len(matched) / len(skill_list)) * 100
    missing = list(set(skill_list) - set(matched))
    return score, matched, missing
