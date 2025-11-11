import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000", // change to your FastAPI URL if deployed
});

export const uploadJobDescription = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return API.post("/upload_jd", formData);
};

export const uploadResumes = (files) => {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }
  return API.post("/upload_resumes", formData);
};

export const analyzeResumes = () => API.get("/analyze");
