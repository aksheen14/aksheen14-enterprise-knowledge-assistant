import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login, register } from "../api/client";

export default function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isRegistering, setIsRegistering] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            if (isRegistering) {
                await register(email, password);
                // after registering, log them in automatically
                const res = await login(email, password);
                localStorage.setItem("token", res.data.token);
                localStorage.setItem("email", email);
            } else {
                const res = await login(email, password);
                localStorage.setItem("token", res.data.token);
                localStorage.setItem("email", email);
            }
            navigate("/dashboard");
        } catch (err) {
            setError(err.response?.data?.error || "Something went wrong");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="bg-white p-8 rounded-2xl shadow-md w-full max-w-md">

                {/* title */}
                <h1 className="text-2xl font-bold text-gray-800 mb-1">
                    Enterprise Knowledge Assistant
                </h1>
                <p className="text-gray-500 text-sm mb-6">
                    {isRegistering ? "Create an account" : "Sign in to your account"}
                </p>

                {/* error message */}
                {error && (
                    <div className="bg-red-50 text-red-600 text-sm px-4 py-3 rounded-lg mb-4">
                        {error}
                    </div>
                )}

                {/* form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Email
                        </label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="you@example.com"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg text-sm transition disabled:opacity-50"
                    >
                        {loading ? "Please wait..." : isRegistering ? "Create account" : "Sign in"}
                    </button>
                </form>

                {/* toggle register/login */}
                <p className="text-center text-sm text-gray-500 mt-6">
                    {isRegistering ? "Already have an account?" : "Don't have an account?"}
                    <button
                        onClick={() => setIsRegistering(!isRegistering)}
                        className="text-blue-600 hover:underline ml-1"
                    >
                        {isRegistering ? "Sign in" : "Register"}
                    </button>
                </p>
            </div>
        </div>
    );
}