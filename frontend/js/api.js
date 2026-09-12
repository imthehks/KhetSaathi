/**
 * KhetSaathi - Unified API Client & Utilities
 */

const API_BASE_URL = window.location.origin.includes(":8000") || window.location.origin.includes(":3000") || window.location.origin.includes("khetsaathi")
    ? window.location.origin
    : "http://localhost:8000";

// Auth State Helpers
function getAuthToken() {
    return localStorage.getItem("khetsaathi_token");
}

function setAuthSession(token, user) {
    localStorage.setItem("khetsaathi_token", token);
    localStorage.setItem("khetsaathi_user", JSON.stringify(user));
}

function getCurrentUser() {
    const userStr = localStorage.getItem("khetsaathi_user");
    try {
        return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
        return null;
    }
}

function clearAuthSession() {
    localStorage.removeItem("khetsaathi_token");
    localStorage.removeItem("khetsaathi_user");
}

/**
 * Universal fetch wrapper with automatic JWT token attachment and error interception.
 */
async function fetchApi(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${endpoint}`;
    const token = getAuthToken();

    const headers = {
        ...(options.headers || {})
    };

    // Auto-set Content-Type: application/json unless sending FormData
    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
    }

    // Attach Bearer token if present
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        // 204 No Content
        if (response.status === 204) {
            return null;
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            // If unauthorized, clear session and optionally redirect
            if (response.status === 401) {
                console.warn("Session expired or unauthorized. Clearing session.");
                clearAuthSession();
                if (!window.location.pathname.includes("login.html") && !window.location.pathname.includes("register.html") && window.location.pathname !== "/") {
                    showToast("Session expired. Please log in again.", "warning");
                    setTimeout(() => {
                        window.location.href = "login.html";
                    }, 1200);
                }
            }
            const errorMessage = data.detail || "An unexpected error occurred.";
            throw new Error(errorMessage);
        }

        return data;
    } catch (err) {
        console.error(`API Error on [${options.method || "GET"} ${endpoint}]:`, err.message);
        throw err;
    }
}

/**
 * Currency and Date Formatters
 */
function formatINR(amount) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2
    }).format(amount || 0);
}

function formatDate(dateString) {
    if (!dateString) return "N/A";
    const d = new Date(dateString);
    return d.toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric"
    });
}

/**
 * Toast Notification Utility
 */
function showToast(message, type = "success") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toastId = "toast_" + Math.random().toString(36).substr(2, 9);
    const bgClass = type === "success" ? "bg-success text-white" :
                    type === "error" || type === "danger" ? "bg-danger text-white" :
                    type === "warning" ? "bg-warning text-dark" : "bg-primary text-white";

    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 show shadow-lg mb-2" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body fw-medium">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML("beforeend", toastHtml);

    const toastEl = document.getElementById(toastId);
    setTimeout(() => {
        if (toastEl && toastEl.parentNode) {
            toastEl.remove();
        }
    }, 4500);
}
