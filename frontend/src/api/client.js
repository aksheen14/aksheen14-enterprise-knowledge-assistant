import axios from "axios";

const API = axios.create({
    baseURL: "https://aksheen14-enterprise-knowledge-assistant-production.up.railway.app",
});

// automatically attach token to every request if it exists
API.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const register = (email, password) =>
    API.post("/auth/register", { email, password });

export const login = (email, password) =>
    API.post("/auth/login", { email, password });

export const uploadDocument = (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return API.post("/documents/upload", formData);
};

export const askQuestion = (question, document_id) =>
    API.post("/documents/ask", { question, document_id });

export const getHistory = () =>
    API.get("/documents/history");

export const getDocuments = () =>
    API.get("/documents");

export const deleteDocument = (documentId) =>
    API.delete(`/documents/${documentId}`);