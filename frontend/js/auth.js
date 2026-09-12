/**
 * KhetSaathi - Authentication & Global Navigation Guard
 */

function renderNavbar() {
    const user = getCurrentUser();
    const currentPath = window.location.pathname;

    const navContainer = document.getElementById("main-nav-container");
    if (!navContainer) return;

    let authSection = "";
    if (user) {
        const roleColors = {
            farmer: "bg-success",
            owner: "bg-warning text-dark",
            laborer: "bg-info text-dark",
            admin: "bg-danger"
        };
        const roleBadge = roleColors[user.role] || "bg-secondary";

        authSection = `
            <li class="nav-item dropdown me-2">
                <a class="nav-link position-relative" href="#" id="notifDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false" onclick="loadNavbarNotifications()">
                    <i class="bi bi-bell-fill fs-5"></i>
                    <span id="nav-unread-badge" class="position-absolute top-1 start-100 translate-middle badge rounded-pill bg-danger d-none">
                        0
                    </span>
                </a>
                <ul class="dropdown-menu dropdown-menu-end shadow-sm" aria-labelledby="notifDropdown" style="width: 320px; max-height: 380px; overflow-y: auto;" id="navbar-notif-list">
                    <li class="dropdown-header d-flex justify-content-between align-items-center">
                        <span>Notifications</span>
                        <a href="javascript:void(0)" class="text-decoration-none small text-success" onclick="markAllNotificationsAsRead()">Mark all read</a>
                    </li>
                    <li class="text-center py-3 text-muted small" id="notif-loading-item">Loading notifications...</li>
                </ul>
            </li>
            <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle d-flex align-items-center gap-2" href="#" id="userMenuDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                    <div class="rounded-circle bg-success text-white d-flex align-items-center justify-content-center fw-bold" style="width: 32px; height: 32px; font-size: 0.85rem;">
                        ${user.name.charAt(0).toUpperCase()}
                    </div>
                    <span>${user.name.split(" ")[0]}</span>
                    <span class="badge ${roleBadge} text-capitalize" style="font-size: 0.7rem;">${user.role}</span>
                </a>
                <ul class="dropdown-menu dropdown-menu-end shadow-sm" aria-labelledby="userMenuDropdown">
                    <li><h6 class="dropdown-header text-truncate">${user.email}</h6></li>
                    <li><a class="dropdown-item" href="dashboard.html"><i class="bi bi-speedometer2 me-2"></i>My Dashboard</a></li>
                    <li><a class="dropdown-item" href="bookings.html"><i class="bi bi-calendar2-check me-2"></i>My Bookings</a></li>
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item text-danger" href="javascript:void(0)" onclick="logoutUser()"><i class="bi bi-box-arrow-right me-2"></i>Log Out</a></li>
                </ul>
            </li>
        `;
    } else {
        authSection = `
            <li class="nav-item me-2">
                <a class="btn btn-outline-success btn-sm px-3" href="login.html">Login</a>
            </li>
            <li class="nav-item">
                <a class="btn btn-primary-khet btn-sm px-3" href="register.html">Sign Up</a>
            </li>
        `;
    }

    const navHtml = `
        <nav class="navbar navbar-expand-lg navbar-light bg-white border-bottom sticky-top shadow-sm py-2">
            <div class="container">
                <a class="navbar-brand d-flex align-items-center gap-2" href="index.html">
                    <span class="fs-4">🌾</span>
                    <span>KhetSaathi</span>
                    <span class="badge brand-badge rounded-pill">खेती साथी</span>
                </a>
                <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarSupportedContent">
                    <ul class="navbar-nav me-auto mb-2 mb-lg-0 ms-lg-3">
                        <li class="nav-item">
                            <a class="nav-link ${currentPath.endsWith("equipment.html") ? "active" : ""}" href="equipment.html">
                                <i class="bi bi-truck me-1"></i> Farm Equipment
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${currentPath.endsWith("labor.html") ? "active" : ""}" href="labor.html">
                                <i class="bi bi-people me-1"></i> Farm Labor
                            </a>
                        </li>
                        ${user ? `
                        <li class="nav-item">
                            <a class="nav-link ${currentPath.endsWith("bookings.html") ? "active" : ""}" href="bookings.html">
                                <i class="bi bi-calendar-check me-1"></i> Bookings
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${currentPath.endsWith("dashboard.html") ? "active" : ""}" href="dashboard.html">
                                <i class="bi bi-speedometer2 me-1"></i> Dashboard
                            </a>
                        </li>
                        ` : ""}
                        <li class="nav-item">
                            <a class="nav-link ${currentPath.endsWith("faq.html") ? "active" : ""}" href="faq.html">
                                <i class="bi bi-question-circle me-1"></i> FAQ & Help
                            </a>
                        </li>
                    </ul>
                    <ul class="navbar-nav ms-auto mb-2 mb-lg-0 align-items-lg-center">
                        ${authSection}
                    </ul>
                </div>
            </div>
        </nav>
    `;

    navContainer.innerHTML = navHtml;

    // Load unread badge if logged in
    if (user) {
        checkUnreadNotificationBadge();
    }
}

async function checkUnreadNotificationBadge() {
    try {
        const res = await fetchApi("/api/notifications/unread-count");
        const badge = document.getElementById("nav-unread-badge");
        if (badge && res && res.unread_count > 0) {
            badge.innerText = res.unread_count > 9 ? "9+" : res.unread_count;
            badge.classList.remove("d-none");
        } else if (badge) {
            badge.classList.add("d-none");
        }
    } catch (e) {
        // Silently ignore background badge errors
    }
}

async function loadNavbarNotifications() {
    const listEl = document.getElementById("navbar-notif-list");
    if (!listEl) return;

    try {
        const notifs = await fetchApi("/api/notifications?limit=8");
        if (!notifs || notifs.length === 0) {
            listEl.innerHTML = `
                <li class="dropdown-header d-flex justify-content-between align-items-center">
                    <span>Notifications</span>
                </li>
                <li class="text-center py-3 text-muted small">No notifications yet.</li>
            `;
            return;
        }

        let itemsHtml = `
            <li class="dropdown-header d-flex justify-content-between align-items-center">
                <span>Notifications</span>
                <a href="javascript:void(0)" class="text-decoration-none small text-success" onclick="markAllNotificationsAsRead()">Mark all read</a>
            </li>
        `;

        notifs.forEach(n => {
            itemsHtml += `
                <li>
                    <a class="dropdown-item py-2 border-bottom ${n.is_read ? 'text-muted' : 'fw-bold bg-light'}" href="bookings.html" onclick="markSingleNotifRead(${n.id})">
                        <div class="small">${n.message}</div>
                        <div class="text-muted" style="font-size: 0.72rem;">${formatDate(n.created_at)}</div>
                    </a>
                </li>
            `;
        });

        listEl.innerHTML = itemsHtml;
    } catch (err) {
        listEl.innerHTML = `<li class="text-center py-2 text-danger small">Failed to load alerts</li>`;
    }
}

async function markSingleNotifRead(id) {
    try {
        await fetchApi(`/api/notifications/${id}/read`, { method: "PATCH" });
        checkUnreadNotificationBadge();
    } catch (e) {}
}

async function markAllNotificationsAsRead() {
    try {
        await fetchApi("/api/notifications/mark-all-read", { method: "POST" });
        showToast("All notifications marked as read");
        const badge = document.getElementById("nav-unread-badge");
        if (badge) badge.classList.add("d-none");
        loadNavbarNotifications();
    } catch (err) {
        showToast("Failed to mark notifications read", "error");
    }
}

function logoutUser() {
    clearAuthSession();
    showToast("You have been logged out.");
    setTimeout(() => {
        window.location.href = "index.html";
    }, 800);
}

function requireAuth(allowedRoles = []) {
    const user = getCurrentUser();
    if (!user) {
        showToast("Please log in to access this page.", "warning");
        setTimeout(() => {
            window.location.href = "login.html";
        }, 1000);
        return false;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(user.role) && user.role !== "admin") {
        showToast("Access restricted: Your account role does not have permission.", "error");
        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 1200);
        return false;
    }
    return true;
}

// Auto-run on DOM ready
document.addEventListener("DOMContentLoaded", renderNavbar);
