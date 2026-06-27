import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { uploadDocument, getDocuments, deleteDocument } from "../api/client";

export default function Dashboard() {
    const [file, setFile] = useState(null);
    const [documents, setDocuments] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [loadingDocuments, setLoadingDocuments] = useState(true);
    const [deletingDocumentId, setDeletingDocumentId] = useState(null);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const navigate = useNavigate();

    useEffect(() => {
        const fetchDocuments = async () => {
            setLoadingDocuments(true);
            try {
                const res = await getDocuments();
                setDocuments(res.data);
            } catch (err) {
                console.error("Failed to fetch documents", err);
            } finally {
                setLoadingDocuments(false);
            }
        };
        fetchDocuments();
    }, []);
    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setError("");
        setSuccess("");

        try {
            const res = await uploadDocument(file);
            console.log(res.data);
            setSuccess(`Document uploaded successfully! ID: ${res.data.document_id}`);
            setDocuments([...documents, {
                id: res.data.document_id,
                filename: file.name
            }]);
            setFile(null);
        } catch (err) {
            setError(err.response?.data?.error || "Upload failed");
        } finally {
            setUploading(false);
        }
    };

    const handleDeleteDocument = async (id) => {
        setDeletingDocumentId(id);
        setError("");
        setSuccess("");

        try {
            await deleteDocument(id);
            setDocuments((prevDocuments) => prevDocuments.filter((doc) => doc.id !== id));
            setSuccess("Document deleted successfully.");
        } catch (err) {
            setError(err.response?.data?.error || "Delete failed");
        } finally {
            setDeletingDocumentId(null);
        }
    };
    
    return (
        <div className="min-h-screen bg-gray-50">

            {/* navbar */}
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
                <h1 className="text-lg font-semibold text-gray-800">
                    Enterprise Knowledge Assistant
                </h1>
            </div>

            <div className="max-w-3xl mx-auto px-6 py-10">

                {/* upload section */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-8">
                    <h2 className="text-base font-semibold text-gray-800 mb-4">
                        Upload a document
                    </h2>

                    {error && (
                        <div className="bg-red-50 text-red-600 text-sm px-4 py-3 rounded-lg mb-4">
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="bg-green-50 text-green-600 text-sm px-4 py-3 rounded-lg mb-4">
                            {success}
                        </div>
                    )}

                    <div className="flex items-center gap-4">
                        <input
                            type="file"
                            accept=".pdf"
                            onChange={(e) => setFile(e.target.files[0])}
                            className="text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                        />
                        <button
                            onClick={handleUpload}
                            disabled={!file || uploading}
                            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50 transition"
                        >
                            {uploading ? "Uploading..." : "Upload"}
                        </button>
                    </div>
                </div>

                {/* documents list */}
                <div>
                    <h2 className="text-base font-semibold text-gray-800 mb-4">
                        Your documents
                    </h2>

                        {loadingDocuments ? (
                        <div className="text-center text-gray-500 text-sm py-12 bg-white rounded-2xl border border-gray-200">
                            <div className="inline-flex items-center gap-3">
                                <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent"></div>
                                Loading documents...
                            </div>
                        </div>
                    ) : documents.length === 0 ? (
                        <div className="text-center text-gray-400 text-sm py-12 bg-white rounded-2xl border border-gray-200">
                            No documents uploaded yet. Upload a PDF to get started.
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {documents.map((doc) => (
                                <div
                                    key={doc.id}
                                    className="bg-white rounded-xl border border-gray-200 px-5 py-4 flex justify-between items-center"
                                >
                                    <div>
                                        <p className="text-sm font-medium text-gray-800">{doc.filename}</p>
                                        <p className="text-xs text-gray-400">ID: {doc.id}</p>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <button
                                            onClick={() => navigate(`/chat/${doc.id}`)}
                                            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
                                        >
                                            Chat
                                        </button>
                                        <button
                                            onClick={() => handleDeleteDocument(doc.id)}
                                            disabled={deletingDocumentId === doc.id}
                                            className="bg-red-600 hover:bg-red-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition disabled:opacity-50"
                                        >
                                            {deletingDocumentId === doc.id ? "Deleting..." : "Delete"}
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}