import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { askQuestion } from "../api/client";
import { getHistory } from '../api/client';


export default function Chat() {
    const { documentId } = useParams();
    const navigate = useNavigate();
    const [question, setQuestion] = useState("");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    // 1. Create a reference to the bottom of the chat
    const messagesEndRef = useRef(null);

    // 2. Scroll function
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    // 3. Trigger scroll whenever messages change OR when loading starts/stops
    useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

    useEffect(() => {
        const loadHistory = async () => {
            try {
                // Call YOUR helper function instead of the raw client
                const response = await getHistory();
                // Make sure we use == to ignore String vs Int type issues for now
                const currentDocHistory = response.data.filter(
                    (chat) => chat.document_id == documentId 
                );

                const formattedMessages = [];
                currentDocHistory.forEach((chat) => {
                    formattedMessages.push({ role: "user", text: chat.question });
                    formattedMessages.push({ role: "ai", text: chat.answer, sources: chat.source });
                });

                setMessages(formattedMessages); 

            } catch (error) {
                console.error("Failed to fetch chat history:", error);
            }
        };

        if (documentId) {
            loadHistory();
        }
    }, [documentId]);

    const handleAsk = async () => {
        if (!question.trim()) return;
        setLoading(true);
        setError("");

        // Capture current question and clear input
        const currentQuestion = question;
        const userMessage = { role: "user", text: currentQuestion };
        const aiPlaceholder = { role: "ai", text: "", sources: [] };

        setMessages((prev) => [...prev, userMessage, aiPlaceholder]);
        setQuestion("");

        try {
            const baseUrl = import.meta.env.VITE_API_URL || "";
            const response = await fetch(`${baseUrl}/documents/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}` 
                },
                body: JSON.stringify({ 
                    question: currentQuestion, 
                    document_id: documentId 
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let isDone = false;
            let buffer = "";

            while(!isDone) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const messagesList = buffer.split('\n\n');
                
                // Keep the last partial chunk in the buffer
                buffer = messagesList.pop() || "";

                for (const message of messagesList) {
                    if (message.trim() !== "") {
                        try {
                            const parsedData = JSON.parse(message);

                            if (parsedData.type === "sources") {
                                setMessages((prev) => {
                                    const updated = [...prev];
                                    updated[updated.length - 1].sources = parsedData.data;
                                    return updated;
                                });
                            } else if (parsedData.type === "chunk") {
                                setMessages((prev) => {
                                    const updated = [...prev];
                                    updated[updated.length - 1].text += parsedData.data;
                                    return updated;
                                });
                            }
                        } catch(e) {
                            console.error("Failed to parse stream chunk:", e);
                        }
                    }
                }
            }
        }
        catch (err) {
            setError(err.message || "Something went wrong during the stream");
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleAsk();
        }
    };

    return (
        // Changed min-h-screen to h-screen so the input stays pinned to the bottom
        <div className="h-screen bg-gray-50 flex flex-col">

            {/* navbar */}
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
                <button
                    onClick={() => navigate("/dashboard")}
                    className="text-sm text-gray-500 hover:text-gray-800"
                >
                    ← Back to dashboard
                </button>
                <p className="text-sm text-gray-400">Document ID: {documentId}</p>
            </div>

            {/* messages */}
            {/* Added overflow-y-auto to allow internal scrolling */}
            <div className="flex-1 w-full px-6 py-8 space-y-6 overflow-y-auto">
                {messages.length === 0 && (
                    <div className="text-left text-gray-400 text-sm mt-20">
                        Ask a question about your document
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                        <div className={`max-w-xl rounded-2xl px-5 py-3 text-sm text-left ${
                            msg.role === "user"
                                ? "bg-blue-600 text-white"
                                : "bg-white border border-gray-200 text-gray-800"
                        }`}>
                            <p>{msg.text}</p>

                            {/* sources */}
                            {msg.sources && msg.sources.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-gray-100">
                                    <p className="text-xs text-gray-400 font-medium mb-2">Sources:</p>
                                    {msg.sources.map((source, j) => (
                                        <div key={j} className="text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2 mb-1">
                                            <span className="font-medium">Page {source.page + 1}:</span> {source.text.slice(0, 150)}...
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-white border border-gray-200 rounded-2xl px-5 py-3 text-sm text-left text-gray-400">
                            Thinking...
                        </div>
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 text-red-600 text-sm text-left px-4 py-3 rounded-lg">
                        {error}
                    </div>
                )}
                
                {/* 4. This empty div acts as the target for scrollIntoView */}
                <div ref={messagesEndRef} />
            </div>

            {/* input */}
            <div className="bg-white border-t border-gray-200 px-6 py-4">
                <div className="max-w-3xl mx-auto flex gap-3">
                    <textarea
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask a question about your document..."
                        rows={1}
                        className="flex-1 border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                    <button
                        onClick={handleAsk}
                        disabled={!question.trim() || loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-5 py-2 rounded-xl disabled:opacity-50 transition"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
}