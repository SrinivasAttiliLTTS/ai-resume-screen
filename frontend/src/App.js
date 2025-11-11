import React, { useState } from "react";
import axios from "axios";
import "./App.css";
import { API_URL } from "./config";

function App() {
  const [jd, setJd] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!jd || resumes.length === 0) {
      alert("Please upload a JD and at least one resume.");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("jd", jd);
    resumes.forEach((r) => formData.append("resumes", r));

    try {
      const res = await axios.post(`${API_URL}/analyze/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResults(res.data.results);
    } catch (err) {
      console.error(err);
      alert("Error analyzing resumes.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>AI Resume Screening</h1>

      <div className="upload-section">
        <div>
          <h3>Upload Job Description (.docx)</h3>
          <input type="file" onChange={(e) => setJd(e.target.files[0])} />
        </div>

        <div>
          <h3>Upload Resumes (.docx)</h3>
          <input type="file" multiple onChange={(e) => setResumes([...e.target.files])} />
        </div>

        <button onClick={handleSubmit} disabled={loading}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      <div className="results-section">
        {results.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Strengths</th>
                <th>Missing</th>
                <th>Primary Score</th>
                <th>Secondary Score</th>
                <th>Overall Score</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i}>
                  <td>{r.Name}</td>
                  <td>{r.Strengths}</td>
                  <td>{r.Missing}</td>
                  <td>{r.Primary_Score}</td>
                  <td>{r.Secondary_Score}</td>
                  <td>{r.Overall_Score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No results yet. Upload files and click Analyze.</p>
        )}
      </div>
    </div>
  );
}

export default App;
