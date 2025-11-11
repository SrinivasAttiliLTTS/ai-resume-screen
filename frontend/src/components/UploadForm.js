import React, { useState } from "react";
import { uploadJobDescription, uploadResumes, analyzeResumes } from "../api";

const UploadForm = ({ setResults }) => {
  const [jdFile, setJdFile] = useState(null);
  const [resumeFiles, setResumeFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      if (jdFile) await uploadJobDescription(jdFile);
      if (resumeFiles.length > 0) await uploadResumes(resumeFiles);
      const { data } = await analyzeResumes();
      setResults(data);
    } catch (error) {
      alert("Error analyzing resumes. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2>Resume Screening Tool</h2>

      <div className="upload-section">
        <label>Upload Job Description (JD):</label>
        <input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setJdFile(e.target.files[0])} />
      </div>

      <div className="upload-section">
        <label>Upload Resumes:</label>
        <input multiple type="file" accept=".pdf,.docx,.txt" onChange={(e) => setResumeFiles([...e.target.files])} />
      </div>

      <button disabled={loading} onClick={handleAnalyze}>
        {loading ? "Analyzing..." : "Analyze"}
      </button>
    </div>
  );
};

export default UploadForm;
