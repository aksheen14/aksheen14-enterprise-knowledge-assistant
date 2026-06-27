import { useNavigate } from "react-router-dom";

export default function Navbar() {
    const navigate = useNavigate();
    const email = localStorage.getItem("email");

    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("email");
        navigate("/login");
    };

    return (
        <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
            {/* logo + name */}
            <div
                className="flex items-center gap-3 cursor-pointer"
                onClick={() => navigate("/dashboard")}
            >
                <div className="bg-blue-600 text-white rounded-lg w-8 h-8 flex items-center justify-center font-bold text-sm">
                    EK
                </div>
                <span className="font-semibold text-gray-800 text-sm">
                    Enterprise Knowledge Assistant
                </span>
            </div>

            {/* right side */}
            {email && (
                <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-500">{email}</span>
                    <button
                        onClick={handleLogout}
                        className="text-sm text-white bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg transition"
                    >
                        Logout
                    </button>
                </div>
            )}
        </nav>
    );
}