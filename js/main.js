/**
 * KhetSaathi - Core Frontend Application Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;

    if (path.endsWith("index.html") || path === "/" || path.endsWith("/")) {
        initHomePage();
    } else if (path.endsWith("equipment.html")) {
        initEquipmentPage();
    } else if (path.endsWith("labor.html")) {
        initLaborPage();
    } else if (path.endsWith("bookings.html")) {
        initBookingsPage();
    } else if (path.endsWith("dashboard.html")) {
        initDashboardPage();
    } else if (path.endsWith("login.html")) {
        initLoginPage();
    } else if (path.endsWith("register.html")) {
        initRegisterPage();
    }
});

// ==========================================
// 1. HOME PAGE CONTROLLER
// ==========================================
async function initHomePage() {
    try {
        // Load featured equipment (limit 3)
        const equipment = await fetchApi("/api/equipment?limit=3&available_only=true");
        const container = document.getElementById("featured-equipment-container");
        if (container) {
            if (!equipment || equipment.length === 0) {
                container.innerHTML = `<div class="col-12 text-center text-muted py-4">No equipment listings currently available.</div>`;
            } else {
                container.innerHTML = equipment.map(item => createEquipmentCardHtml(item)).join("");
            }
        }

        // Load featured labor (limit 3)
        const labor = await fetchApi("/api/labor?limit=3&available_only=true");
        const laborContainer = document.getElementById("featured-labor-container");
        if (laborContainer) {
            if (!labor || labor.length === 0) {
                laborContainer.innerHTML = `<div class="col-12 text-center text-muted py-4">No laborer profiles currently available.</div>`;
            } else {
                laborContainer.innerHTML = labor.map(item => createLaborCardHtml(item)).join("");
            }
        }
    } catch (err) {
        console.error("Failed to load home page content:", err);
    }
}

// ==========================================
// 2. EQUIPMENT PAGE CONTROLLER
// ==========================================
let currentSelectedEquipment = null;

async function initEquipmentPage() {
    // Load categories
    try {
        const categories = await fetchApi("/api/equipment/categories");
        const categorySelect = document.getElementById("filter-category");
        if (categorySelect && categories) {
            categories.forEach(cat => {
                const opt = document.createElement("option");
                opt.value = cat;
                opt.textContent = cat;
                categorySelect.appendChild(opt);
            });
        }
    } catch (e) {}

    // Attach search listener
    const searchForm = document.getElementById("equipment-search-form");
    if (searchForm) {
        searchForm.addEventListener("submit", (e) => {
            e.preventDefault();
            loadEquipmentList();
        });
    }

    // Live filter reset
    const resetBtn = document.getElementById("btn-reset-filters");
    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            if (searchForm) searchForm.reset();
            loadEquipmentList();
        });
    }

    // Initial load
    loadEquipmentList();
}

async function loadEquipmentList() {
    const container = document.getElementById("equipment-list-container");
    if (!container) return;

    container.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-success" role="status">
                <span class="visually-hidden">Loading equipment...</span>
            </div>
        </div>
    `;

    const q = document.getElementById("search-query")?.value || "";
    const category = document.getElementById("filter-category")?.value || "";
    const location = document.getElementById("filter-location")?.value || "";
    const maxRate = document.getElementById("filter-max-rate")?.value || "";
    const availableOnly = document.getElementById("filter-available")?.checked || false;

    let url = `/api/equipment?limit=50`;
    if (q) url += `&q=${encodeURIComponent(q)}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    if (location) url += `&location=${encodeURIComponent(location)}`;
    if (maxRate) url += `&max_rate=${encodeURIComponent(maxRate)}`;
    if (availableOnly) url += `&available_only=true`;

    try {
        const items = await fetchApi(url);
        if (!items || items.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="fs-1 text-muted mb-3">🚜</div>
                    <h5 class="text-muted">No machinery found matching your criteria</h5>
                    <p class="small text-muted">Try clearing some filters or searching for another district.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = items.map(item => createEquipmentCardHtml(item)).join("");
    } catch (err) {
        container.innerHTML = `<div class="col-12 alert alert-danger">Error loading equipment: ${err.message}</div>`;
    }
}

function getCategoryFallbackImage(category) {
    const catLower = (category || "").toLowerCase();
    if (catLower.includes("harvester")) return "/img/harvester.svg";
    if (catLower.includes("rotavator") || catLower.includes("tillage")) return "/img/rotavator.svg";
    if (catLower.includes("pump") || catLower.includes("irrigation")) return "/img/solar_pump.svg";
    if (catLower.includes("drone")) return "/img/drone_sprayer.svg";
    if (catLower.includes("spray")) return "/img/knapsack_sprayer.svg";
    if (catLower.includes("seeder") || catLower.includes("planter")) return "/img/seed_drill.svg";
    if (catLower.includes("leveler")) return "/img/laser_leveler.svg";
    if (catLower.includes("tiller")) return "/img/power_tiller.svg";
    return "/img/tractor_red.svg";
}

function createEquipmentCardHtml(item) {
    const fallback = getCategoryFallbackImage(item.category);
    const imgUrl = item.image_url || fallback;

    return `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card custom-card h-100 shadow-sm border-0">
                <div class="position-relative overflow-hidden" style="background-color: #0f241a;">
                    <img src="${imgUrl}" class="card-img-top card-img-top-crop" alt="${item.name}" onerror="this.onerror=null; this.src='${fallback}';">
                    <span class="badge ${item.is_available ? 'bg-success' : 'bg-secondary'} position-absolute top-0 end-0 m-3 shadow-sm px-2 py-1">
                        ${item.is_available ? 'Ready for Rent' : 'Currently in Field'}
                    </span>
                    <span class="badge bg-dark bg-opacity-75 position-absolute bottom-0 start-0 m-3 px-2 py-1">
                        <i class="bi bi-gear-fill me-1 text-warning"></i>${item.category}
                    </span>
                </div>
                <div class="card-body d-flex flex-column p-3">
                    <h5 class="card-title fw-bold text-truncate mb-1" title="${item.name}">${item.name}</h5>
                    <p class="text-muted small mb-2"><i class="bi bi-geo-alt-fill text-danger me-1"></i>${item.location}</p>
                    <p class="card-text text-muted small flex-grow-1 lh-base" style="display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                        ${item.description || "Certified agricultural machinery verified for seasonal farming operations."}
                    </p>
                    <div class="d-flex justify-content-between align-items-center mt-3 pt-2 border-top">
                        <div>
                            <span class="price-tag">${formatINR(item.rental_rate)}</span>
                            <span class="price-unit">/ day</span>
                        </div>
                        <button class="btn btn-primary-khet btn-sm px-3" onclick='openBookingModal(${JSON.stringify(item).replace(/'/g, "&apos;")}, "equipment")'>
                            Rent Equipment
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ==========================================
// 3. LABOR PAGE CONTROLLER
// ==========================================
async function initLaborPage() {
    try {
        const skills = await fetchApi("/api/labor/skills");
        const skillSelect = document.getElementById("filter-skill");
        if (skillSelect && skills) {
            skills.forEach(skill => {
                const opt = document.createElement("option");
                opt.value = skill;
                opt.textContent = skill;
                skillSelect.appendChild(opt);
            });
        }
    } catch (e) {}

    const searchForm = document.getElementById("labor-search-form");
    if (searchForm) {
        searchForm.addEventListener("submit", (e) => {
            e.preventDefault();
            loadLaborList();
        });
    }

    const resetBtn = document.getElementById("btn-reset-labor-filters");
    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            if (searchForm) searchForm.reset();
            loadLaborList();
        });
    }

    loadLaborList();
}

async function loadLaborList() {
    const container = document.getElementById("labor-list-container");
    if (!container) return;

    container.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-success" role="status">
                <span class="visually-hidden">Loading laborers...</span>
            </div>
        </div>
    `;

    const q = document.getElementById("search-labor-query")?.value || "";
    const skill = document.getElementById("filter-skill")?.value || "";
    const location = document.getElementById("filter-labor-location")?.value || "";
    const maxWage = document.getElementById("filter-max-wage")?.value || "";
    const availableOnly = document.getElementById("filter-labor-available")?.checked || false;

    let url = `/api/labor?limit=50`;
    if (q) url += `&q=${encodeURIComponent(q)}`;
    if (skill) url += `&skill_type=${encodeURIComponent(skill)}`;
    if (location) url += `&location=${encodeURIComponent(location)}`;
    if (maxWage) url += `&max_wage=${encodeURIComponent(maxWage)}`;
    if (availableOnly) url += `&available_only=true`;

    try {
        const items = await fetchApi(url);
        if (!items || items.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="fs-1 text-muted mb-3">👨‍🌾</div>
                    <h5 class="text-muted">No farm workers found matching your criteria</h5>
                    <p class="small text-muted">Try broadening your location or skill filter.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = items.map(item => createLaborCardHtml(item)).join("");
    } catch (err) {
        container.innerHTML = `<div class="col-12 alert alert-danger">Error loading labor: ${err.message}</div>`;
    }
}

function createLaborCardHtml(item) {
    const userName = item.user ? item.user.name : "Agricultural Worker";
    return `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card custom-card h-100 shadow-sm border-0">
                <div class="card-body d-flex flex-column p-3">
                    <div class="d-flex align-items-center justify-content-between mb-3">
                        <div class="d-flex align-items-center gap-2">
                            <div class="rounded-circle bg-success text-white d-flex align-items-center justify-content-center fw-bold" style="width: 44px; height: 44px;">
                                <i class="bi bi-person-fill fs-5"></i>
                            </div>
                            <div>
                                <h6 class="fw-bold mb-0">${userName}</h6>
                                <span class="badge bg-light text-dark border">${item.skill_type}</span>
                            </div>
                        </div>
                        <span class="badge ${item.is_available ? 'bg-success' : 'bg-secondary'}">
                            ${item.is_available ? 'Available' : 'Busy'}
                        </span>
                    </div>
                    <p class="text-muted small mb-2"><i class="bi bi-geo-alt-fill text-danger me-1"></i>${item.location}</p>
                    <p class="card-text text-muted small flex-grow-1 lh-base">
                        ${item.description || "Experienced farm operator ready for harvest and field operations."}
                    </p>
                    <div class="d-flex justify-content-between align-items-center mt-3 pt-2 border-top">
                        <div>
                            <span class="price-tag">${formatINR(item.wage_rate)}</span>
                            <span class="price-unit">/ day</span>
                        </div>
                        <button class="btn btn-primary-khet btn-sm px-3" onclick='openBookingModal(${JSON.stringify(item).replace(/'/g, "&apos;")}, "labor")'>
                            Hire Labor
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ==========================================
// 4. BOOKING MODAL & SUBMISSION
// ==========================================
let activeBookingItem = null;
let activeItemType = "equipment";

function openBookingModal(item, itemType) {
    const user = getCurrentUser();
    if (!user) {
        showToast("Please log in to make a booking.", "warning");
        setTimeout(() => { window.location.href = "login.html"; }, 1000);
        return;
    }

    if (user.role !== "farmer" && user.role !== "admin") {
        showToast("Only farmers can create booking requests.", "error");
        return;
    }

    activeBookingItem = item;
    activeItemType = itemType;

    const modalTitle = document.getElementById("bookingModalTitle");
    const itemNameEl = document.getElementById("booking-item-name");
    const itemRateEl = document.getElementById("booking-item-rate");
    const itemLocationEl = document.getElementById("booking-item-location");

    const title = itemType === "equipment" ? item.name : `${item.skill_type} (${item.user ? item.user.name : "Worker"})`;
    const rate = itemType === "equipment" ? item.rental_rate : item.wage_rate;

    if (modalTitle) modalTitle.innerText = itemType === "equipment" ? "Book Farm Equipment" : "Hire Farm Labor";
    if (itemNameEl) itemNameEl.innerText = title;
    if (itemRateEl) itemRateEl.innerText = `${formatINR(rate)} / day`;
    if (itemLocationEl) itemLocationEl.innerText = item.location;

    // Set default dates (tomorrow to 3 days after)
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dayAfter = new Date(tomorrow);
    dayAfter.setDate(dayAfter.getDate() + 2);

    const startInput = document.getElementById("booking-start-date");
    const endInput = document.getElementById("booking-end-date");

    const formatDateIso = (d) => d.toISOString().split("T")[0];
    if (startInput) {
        startInput.min = formatDateIso(today);
        startInput.value = formatDateIso(tomorrow);
        startInput.onchange = calculateBookingTotal;
    }
    if (endInput) {
        endInput.min = formatDateIso(tomorrow);
        endInput.value = formatDateIso(dayAfter);
        endInput.onchange = calculateBookingTotal;
    }

    calculateBookingTotal();

    const bookingModalEl = document.getElementById("bookingModal");
    if (bookingModalEl) {
        const modal = new bootstrap.Modal(bookingModalEl);
        modal.show();
    }
}

function calculateBookingTotal() {
    if (!activeBookingItem) return;

    const startVal = document.getElementById("booking-start-date")?.value;
    const endVal = document.getElementById("booking-end-date")?.value;
    const rate = activeItemType === "equipment" ? activeBookingItem.rental_rate : activeBookingItem.wage_rate;

    const daysEl = document.getElementById("booking-calculated-days");
    const totalEl = document.getElementById("booking-calculated-total");

    if (!startVal || !endVal) return;

    const startDate = new Date(startVal);
    const endDate = new Date(endVal);

    if (endDate < startDate) {
        if (daysEl) daysEl.innerText = "Invalid dates";
        if (totalEl) totalEl.innerText = "₹0.00";
        return;
    }

    const diffTime = Math.abs(endDate - startDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // inclusive
    const total = diffDays * rate;

    if (daysEl) daysEl.innerText = `${diffDays} Day(s)`;
    if (totalEl) totalEl.innerText = formatINR(total);
}

async function submitBookingForm() {
    if (!activeBookingItem) return;

    const startDate = document.getElementById("booking-start-date")?.value;
    const endDate = document.getElementById("booking-end-date")?.value;

    if (!startDate || !endDate) {
        showToast("Please select both start and end dates.", "warning");
        return;
    }

    const btn = document.getElementById("btn-confirm-booking");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Booking...`;
    }

    try {
        const payload = {
            item_type: activeItemType,
            item_id: activeBookingItem.id,
            start_date: startDate,
            end_date: endDate
        };

        const res = await fetchApi("/api/bookings", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        showToast(`Booking #${res.id} created successfully!`, "success");

        const bookingModalEl = document.getElementById("bookingModal");
        if (bookingModalEl) {
            const modal = bootstrap.Modal.getInstance(bookingModalEl);
            if (modal) modal.hide();
        }

        setTimeout(() => {
            window.location.href = "bookings.html";
        }, 1200);

    } catch (err) {
        showToast(err.message, "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = "Proceed to Pay & Confirm";
        }
    }
}

// ==========================================
// 5. BOOKINGS TRACKER PAGE CONTROLLER
// ==========================================
async function initBookingsPage() {
    if (!requireAuth()) return;

    const filterStatus = document.getElementById("filter-booking-status");
    if (filterStatus) {
        filterStatus.addEventListener("change", loadBookingsList);
    }

    loadBookingsList();
}

async function loadBookingsList() {
    const container = document.getElementById("bookings-list-container");
    if (!container) return;

    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-success" role="status">
                <span class="visually-hidden">Loading bookings...</span>
            </div>
        </div>
    `;

    const statusVal = document.getElementById("filter-booking-status")?.value || "";
    let url = "/api/bookings";
    if (statusVal) url += `?status_filter=${statusVal}`;

    try {
        const bookings = await fetchApi(url);
        if (!bookings || bookings.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 bg-white rounded-3 border">
                    <div class="fs-1 text-muted mb-3">📅</div>
                    <h5 class="text-muted">No bookings found</h5>
                    <p class="small text-muted">You have no booking records in this view.</p>
                    <a href="equipment.html" class="btn btn-primary-khet btn-sm mt-2">Explore Equipment</a>
                </div>
            `;
            return;
        }

        container.innerHTML = bookings.map(b => createBookingCardHtml(b)).join("");
    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger">Error loading bookings: ${err.message}</div>`;
    }
}

function createBookingCardHtml(booking) {
    const user = getCurrentUser();
    const isFarmer = user && user.id === booking.farmer_id;
    const isOwner = user && (user.id === booking.owner_id || user.role === "admin");

    const statusBadgeClasses = {
        pending: "badge-pending",
        confirmed: "badge-confirmed",
        ongoing: "badge-ongoing",
        completed: "badge-completed",
        cancelled: "badge-cancelled"
    };

    const badgeClass = statusBadgeClasses[booking.status] || "bg-secondary";
    const itemTitle = booking.item_details ? booking.item_details.name : `Item #${booking.item_id}`;

    const stepOrder = ["pending", "confirmed", "ongoing", "completed"];
    const currentIndex = stepOrder.indexOf(booking.status);

    let stepperHtml = "";
    if (booking.status !== "cancelled") {
        stepperHtml = `
            <div class="stepper-container">
                <div class="step-node ${currentIndex >= 0 ? 'active' : ''} ${currentIndex > 0 ? 'completed' : ''}">
                    <div class="step-circle"><i class="bi bi-receipt"></i></div>
                    <div class="step-label">Pending</div>
                </div>
                <div class="step-node ${currentIndex >= 1 ? 'active' : ''} ${currentIndex > 1 ? 'completed' : ''}">
                    <div class="step-circle"><i class="bi bi-credit-card-2-front"></i></div>
                    <div class="step-label">Confirmed</div>
                </div>
                <div class="step-node ${currentIndex >= 2 ? 'active' : ''} ${currentIndex > 2 ? 'completed' : ''}">
                    <div class="step-circle"><i class="bi bi-gear-wide-connected"></i></div>
                    <div class="step-label">Ongoing</div>
                </div>
                <div class="step-node ${currentIndex >= 3 ? 'active' : ''}">
                    <div class="step-circle"><i class="bi bi-check-lg"></i></div>
                    <div class="step-label">Completed</div>
                </div>
            </div>
        `;
    } else {
        stepperHtml = `
            <div class="alert alert-danger py-2 small mb-3">
                <i class="bi bi-x-circle-fill me-1"></i> This booking has been cancelled.
            </div>
        `;
    }

    let actionsHtml = "";
    if (booking.status === "pending" && isFarmer) {
        actionsHtml += `
            <button class="btn btn-success btn-sm fw-bold" onclick="initiateRazorpayPayment(${booking.id}, ${booking.total_amount})">
                <i class="bi bi-credit-card me-1"></i> Pay Now (${formatINR(booking.total_amount)})
            </button>
        `;
    }

    if (booking.status === "confirmed" && isOwner) {
        actionsHtml += `
            <button class="btn btn-primary btn-sm" onclick="updateBookingState(${booking.id}, 'ongoing')">
                <i class="bi bi-arrow-right-circle me-1"></i> Handover / Start (Ongoing)
            </button>
        `;
    }

    if (booking.status === "ongoing") {
        if (isFarmer) {
            actionsHtml += `
                <button class="btn btn-outline-primary btn-sm me-2" onclick="openExtendModal(${booking.id}, '${booking.end_date}')">
                    <i class="bi bi-calendar-plus me-1"></i> Extend Booking
                </button>
            `;
        }
        if (isOwner || isFarmer) {
            actionsHtml += `
                <button class="btn btn-success btn-sm" onclick="openReturnModal(${booking.id}, '${booking.end_date}')">
                    <i class="bi bi-box-arrow-in-down me-1"></i> Return / Complete
                </button>
            `;
        }
    }

    if (["pending", "confirmed"].includes(booking.status)) {
        actionsHtml += `
            <button class="btn btn-outline-danger btn-sm ms-2" onclick="cancelBookingAction(${booking.id})">
                Cancel
            </button>
        `;
    }

    return `
        <div class="card shadow-sm mb-4 border rounded-3 overflow-hidden">
            <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div class="d-flex align-items-center gap-2">
                    <span class="fs-5">${booking.item_type === 'equipment' ? '🚜' : '👨‍🌾'}</span>
                    <h6 class="mb-0 fw-bold">${itemTitle}</h6>
                    <span class="badge ${badgeClass} text-uppercase ms-2" style="font-size: 0.72rem;">${booking.status}</span>
                </div>
                <div class="text-muted small">
                    Booking #${booking.id} • Created ${formatDate(booking.created_at)}
                </div>
            </div>
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-7">
                        ${stepperHtml}
                        <div class="row g-2 small text-muted mt-2">
                            <div class="col-sm-6">
                                <div><strong class="text-dark">Dates:</strong> ${formatDate(booking.start_date)} to ${formatDate(booking.end_date)}</div>
                                <div><strong class="text-dark">Type:</strong> <span class="text-capitalize">${booking.item_type}</span></div>
                            </div>
                            <div class="col-sm-6">
                                <div><strong class="text-dark">Farmer:</strong> ${booking.farmer ? booking.farmer.name : 'Farmer'}</div>
                                <div><strong class="text-dark">Owner/Laborer:</strong> ${booking.owner ? booking.owner.name : 'Owner'}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-5 border-start-md text-md-end mt-3 mt-md-0">
                        <div class="mb-2">
                            <div class="text-muted small">Total Rental / Wage</div>
                            <div class="fs-4 fw-bold text-success">${formatINR(booking.total_amount)}</div>
                            ${booking.late_fee > 0 ? `<div class="text-danger small fw-bold">Includes Late Fee: ${formatINR(booking.late_fee)}</div>` : ''}
                            ${booking.extension_days > 0 ? `<div class="text-info small">Extended by ${booking.extension_days} day(s)</div>` : ''}
                        </div>
                        <div class="d-flex justify-content-md-end gap-2 flex-wrap">
                            ${actionsHtml}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ==========================================
// 6. PAYMENT CHECKOUT & SIMULATOR
// ==========================================
let activePaymentBookingId = null;

async function initiateRazorpayPayment(bookingId, amount) {
    activePaymentBookingId = bookingId;

    try {
        showToast("Initiating Razorpay payment order...", "info");
        const order = await fetchApi("/api/payments/create-order", {
            method: "POST",
            body: JSON.stringify({ booking_id: bookingId })
        });

        if (window.Razorpay && order.key_id && !order.key_id.startsWith("rzp_test_placeholder")) {
            const options = {
                key: order.key_id,
                amount: order.amount,
                currency: "INR",
                name: "KhetSaathi",
                description: `Booking #${bookingId} Payment`,
                order_id: order.order_id,
                handler: async function (response) {
                    await verifyPaymentSignatureOnBackend(
                        bookingId,
                        response.razorpay_order_id,
                        response.razorpay_payment_id,
                        response.razorpay_signature
                    );
                },
                prefill: {
                    name: getCurrentUser()?.name || "",
                    email: getCurrentUser()?.email || ""
                },
                theme: {
                    color: "#2d6a4f"
                }
            };
            const rzp = new window.Razorpay(options);
            rzp.open();
        } else {
            openTestPaymentSimulator(bookingId, order.order_id, amount);
        }
    } catch (err) {
        showToast(err.message, "error");
    }
}

function openTestPaymentSimulator(bookingId, orderId, amount) {
    const modalEl = document.getElementById("testPaymentModal");
    if (!modalEl) {
        const simHtml = `
            <div class="modal fade" id="testPaymentModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title fw-bold"><i class="bi bi-credit-card-2-front me-2"></i>Razorpay Sandbox Simulator</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-4 text-center">
                            <div class="badge bg-warning text-dark mb-3 px-3 py-2">Test / Sandbox Gateway Mode</div>
                            <h4 class="fw-bold mb-1" id="sim-amount">${formatINR(amount)}</h4>
                            <p class="text-muted small mb-4">Booking #${bookingId} • Order: <span id="sim-order-id" class="font-monospace">${orderId}</span></p>
                            
                            <div class="alert alert-light border small text-start mb-4">
                                <i class="bi bi-info-circle-fill text-primary me-1"></i>
                                Razorpay test mode simulation verifies HMAC signature and advances booking state to <strong>Confirmed</strong>.
                            </div>

                            <div class="d-grid gap-2">
                                <button class="btn btn-success fw-bold py-2" onclick="simulatePaymentVerification(true)">
                                    <i class="bi bi-check-circle-fill me-1"></i> Simulate Successful Payment
                                </button>
                                <button class="btn btn-outline-danger py-2" onclick="simulatePaymentVerification(false)">
                                    <i class="bi bi-x-circle me-1"></i> Simulate Payment Failure
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML("beforeend", simHtml);
    }

    document.getElementById("sim-amount").innerText = formatINR(amount);
    document.getElementById("sim-order-id").innerText = orderId;
    window.currentSimOrderId = orderId;

    const bsModal = new bootstrap.Modal(document.getElementById("testPaymentModal"));
    bsModal.show();
}

async function simulatePaymentVerification(isSuccess) {
    const bookingId = activePaymentBookingId;
    const orderId = window.currentSimOrderId;
    const paymentId = "pay_sim_" + Math.random().toString(36).substr(2, 8);
    const signature = isSuccess ? "mock_test_signature_valid" : "invalid_signature";

    const modalEl = document.getElementById("testPaymentModal");
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }

    await verifyPaymentSignatureOnBackend(bookingId, orderId, paymentId, signature);
}

async function verifyPaymentSignatureOnBackend(bookingId, orderId, paymentId, signature) {
    try {
        showToast("Verifying payment signature with backend...", "info");
        const res = await fetchApi("/api/payments/verify", {
            method: "POST",
            body: JSON.stringify({
                booking_id: bookingId,
                razorpay_order_id: orderId,
                razorpay_payment_id: paymentId,
                razorpay_signature: signature
            })
        });

        showToast("Payment verified! Booking is now CONFIRMED.", "success");
        setTimeout(() => {
            loadBookingsList();
        }, 1000);
    } catch (err) {
        showToast(`Payment verification failed: ${err.message}`, "error");
        setTimeout(() => {
            loadBookingsList();
        }, 1000);
    }
}

async function updateBookingState(bookingId, targetStatus) {
    try {
        await fetchApi(`/api/bookings/${bookingId}/status`, {
            method: "PATCH",
            body: JSON.stringify({ status: targetStatus })
        });
        showToast(`Booking updated to ${targetStatus.toUpperCase()}`, "success");
        loadBookingsList();
    } catch (err) {
        showToast(err.message, "error");
    }
}

function openExtendModal(bookingId, currentEndDate) {
    const days = prompt("Enter additional days to extend this booking (1-30):", "2");
    if (!days) return;

    const daysInt = parseInt(days, 10);
    if (isNaN(daysInt) || daysInt <= 0 || daysInt > 30) {
        showToast("Please enter a valid number of days between 1 and 30.", "warning");
        return;
    }

    extendBookingApi(bookingId, daysInt);
}

async function extendBookingApi(bookingId, days) {
    try {
        const res = await fetchApi(`/api/bookings/${bookingId}/extend`, {
            method: "POST",
            body: JSON.stringify({ extension_days: days })
        });
        showToast(`Booking extended by ${days} day(s)! New total: ${formatINR(res.total_amount)}`, "success");
        loadBookingsList();
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function openReturnModal(bookingId, scheduledEndDate) {
    if (!confirm(`Confirm equipment return for Booking #${bookingId}? Late fees will apply if past scheduled due date (${formatDate(scheduledEndDate)}).`)) {
        return;
    }

    try {
        const today = new Date().toISOString().split("T")[0];
        const res = await fetchApi(`/api/bookings/${bookingId}/return`, {
            method: "POST",
            body: JSON.stringify({ return_date: today })
        });

        if (res.late_fee > 0) {
            showToast(`Equipment returned! Late fee applied: ${formatINR(res.late_fee)}`, "warning");
        } else {
            showToast("Equipment returned on time! Booking marked Completed.", "success");
        }
        loadBookingsList();
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function cancelBookingAction(bookingId) {
    if (!confirm("Are you sure you want to cancel this booking?")) return;

    try {
        await fetchApi(`/api/bookings/${bookingId}/cancel`, { method: "POST" });
        showToast("Booking cancelled successfully.", "info");
        loadBookingsList();
    } catch (err) {
        showToast(err.message, "error");
    }
}

// ==========================================
// 7. DASHBOARD PAGE CONTROLLER
// ==========================================
async function initDashboardPage() {
    if (!requireAuth()) return;

    const user = getCurrentUser();
    const roleContainer = document.getElementById("dashboard-role-content");
    if (!roleContainer) return;

    if (user.role === "admin") {
        renderAdminDashboard(roleContainer);
    } else if (user.role === "owner") {
        renderOwnerDashboard(roleContainer);
    } else if (user.role === "laborer") {
        renderLaborerDashboard(roleContainer);
    } else {
        renderFarmerDashboard(roleContainer);
    }
}

async function renderFarmerDashboard(container) {
    container.innerHTML = `
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="card border-0 shadow-sm bg-success text-white p-3 rounded-3">
                    <div class="fs-6 opacity-75">Active Rentals</div>
                    <h3 class="fw-bold my-1" id="dash-active-count">-</h3>
                    <small>Currently in field</small>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card border-0 shadow-sm bg-warning text-dark p-3 rounded-3">
                    <div class="fs-6 opacity-75">Pending Payment</div>
                    <h3 class="fw-bold my-1" id="dash-pending-count">-</h3>
                    <small>Awaiting confirmation</small>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card border-0 shadow-sm bg-primary text-white p-3 rounded-3">
                    <div class="fs-6 opacity-75">Completed Bookings</div>
                    <h3 class="fw-bold my-1" id="dash-completed-count">-</h3>
                    <small>Returned without issue</small>
                </div>
            </div>
        </div>

        <div class="card border-0 shadow-sm rounded-3">
            <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                <h5 class="fw-bold mb-0">My Recent Bookings</h5>
                <a href="bookings.html" class="btn btn-outline-success btn-sm">View All Bookings</a>
            </div>
            <div class="card-body p-0" id="farmer-recent-bookings">
                <div class="text-center py-4 text-muted">Loading bookings...</div>
            </div>
        </div>
    `;

    try {
        const bookings = await fetchApi("/api/bookings");
        const active = bookings.filter(b => b.status === "ongoing").length;
        const pending = bookings.filter(b => b.status === "pending").length;
        const completed = bookings.filter(b => b.status === "completed").length;

        document.getElementById("dash-active-count").innerText = active;
        document.getElementById("dash-pending-count").innerText = pending;
        document.getElementById("dash-completed-count").innerText = completed;

        const recentContainer = document.getElementById("farmer-recent-bookings");
        if (bookings.length === 0) {
            recentContainer.innerHTML = `<div class="text-center py-4 text-muted">No bookings made yet. <a href="equipment.html">Explore Equipment</a></div>`;
        } else {
            recentContainer.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Item</th>
                                <th>Dates</th>
                                <th>Status</th>
                                <th>Total</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${bookings.slice(0, 5).map(b => `
                                <tr>
                                    <td>
                                        <div class="fw-bold">${b.item_details ? b.item_details.name : 'Item #' + b.item_id}</div>
                                        <div class="text-muted small text-capitalize">${b.item_type}</div>
                                    </td>
                                    <td class="small">${formatDate(b.start_date)} - ${formatDate(b.end_date)}</td>
                                    <td><span class="badge ${b.status === 'confirmed' ? 'bg-primary' : b.status === 'ongoing' ? 'bg-info' : b.status === 'completed' ? 'bg-success' : 'bg-warning text-dark'} text-capitalize">${b.status}</span></td>
                                    <td class="fw-bold text-success">${formatINR(b.total_amount)}</td>
                                    <td><a href="bookings.html" class="btn btn-outline-dark btn-sm">Manage</a></td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            `;
        }
    } catch (e) {}
}

async function renderOwnerDashboard(container) {
    const user = getCurrentUser();
    container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
            <div>
                <h4 class="fw-bold mb-1">Equipment Owner Control Panel</h4>
                <p class="text-muted small mb-0">Manage your farm machinery, view rental requests, and track revenue.</p>
            </div>
            <button class="btn btn-primary-khet" data-bs-toggle="modal" data-bs-target="#addEquipmentModal">
                <i class="bi bi-plus-circle me-1"></i> Add Equipment
            </button>
        </div>

        <div class="card border-0 shadow-sm rounded-3 mb-4">
            <div class="card-header bg-white py-3">
                <h5 class="fw-bold mb-0">My Equipment Inventory</h5>
            </div>
            <div class="card-body p-0" id="owner-equipment-table">
                <div class="text-center py-4 text-muted">Loading inventory...</div>
            </div>
        </div>

        <div class="card border-0 shadow-sm rounded-3">
            <div class="card-header bg-white py-3">
                <h5 class="fw-bold mb-0">Incoming Booking Requests</h5>
            </div>
            <div class="card-body p-0" id="owner-incoming-bookings">
                <div class="text-center py-4 text-muted">Loading requests...</div>
            </div>
        </div>
    `;

    loadOwnerInventory(user.id);
    loadOwnerIncomingBookings();
}

async function loadOwnerInventory(ownerId) {
    const tableContainer = document.getElementById("owner-equipment-table");
    if (!tableContainer) return;

    try {
        const items = await fetchApi(`/api/equipment?owner_id=${ownerId}`);
        if (!items || items.length === 0) {
            tableContainer.innerHTML = `<div class="text-center py-4 text-muted">You haven't listed any machinery yet. Click "Add Equipment" above!</div>`;
            return;
        }

        tableContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>Equipment</th>
                            <th>Category</th>
                            <th>Rate / Day</th>
                            <th>Location</th>
                            <th>Availability</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${items.map(item => `
                            <tr>
                                <td>
                                    <div class="fw-bold">${item.name}</div>
                                    <div class="text-muted small text-truncate" style="max-width: 250px;">${item.description || ''}</div>
                                </td>
                                <td><span class="badge bg-light text-dark border">${item.category}</span></td>
                                <td class="fw-bold text-success">${formatINR(item.rental_rate)}</td>
                                <td class="small">${item.location}</td>
                                <td>
                                    <div class="form-check form-switch">
                                        <input class="form-check-input" type="checkbox" role="switch" ${item.is_available ? 'checked' : ''} onchange="toggleEquipmentAvailabilityApi(${item.id})">
                                        <label class="form-check-label small">${item.is_available ? 'Available' : 'Unavailable'}</label>
                                    </div>
                                </td>
                                <td>
                                    <button class="btn btn-outline-danger btn-sm" onclick="deleteEquipmentApi(${item.id})">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    } catch (err) {
        tableContainer.innerHTML = `<div class="alert alert-danger m-3">Error loading inventory: ${err.message}</div>`;
    }
}

async function loadOwnerIncomingBookings() {
    const container = document.getElementById("owner-incoming-bookings");
    if (!container) return;

    try {
        const bookings = await fetchApi("/api/bookings");
        if (!bookings || bookings.length === 0) {
            container.innerHTML = `<div class="text-center py-4 text-muted">No booking requests received yet.</div>`;
            return;
        }

        container.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>Booking ID</th>
                            <th>Item</th>
                            <th>Farmer</th>
                            <th>Dates</th>
                            <th>Status</th>
                            <th>Amount</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${bookings.map(b => `
                            <tr>
                                <td class="fw-bold">#${b.id}</td>
                                <td>${b.item_details ? b.item_details.name : 'Item #' + b.item_id}</td>
                                <td>${b.farmer ? b.farmer.name : 'Farmer'}</td>
                                <td class="small">${formatDate(b.start_date)} to ${formatDate(b.end_date)}</td>
                                <td><span class="badge ${b.status === 'confirmed' ? 'bg-primary' : b.status === 'ongoing' ? 'bg-info' : b.status === 'completed' ? 'bg-success' : 'bg-warning text-dark'} text-capitalize">${b.status}</span></td>
                                <td class="fw-bold text-success">${formatINR(b.total_amount)}</td>
                                <td>
                                    <a href="bookings.html" class="btn btn-sm btn-outline-success">Manage</a>
                                </td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    } catch (err) {}
}

async function toggleEquipmentAvailabilityApi(id) {
    try {
        await fetchApi(`/api/equipment/${id}/toggle-availability`, { method: "PATCH" });
        showToast("Equipment availability updated");
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function deleteEquipmentApi(id) {
    if (!confirm("Are you sure you want to delete this equipment listing?")) return;
    try {
        await fetchApi(`/api/equipment/${id}`, { method: "DELETE" });
        showToast("Equipment listing removed");
        const user = getCurrentUser();
        loadOwnerInventory(user.id);
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function submitAddEquipmentForm(e) {
    e.preventDefault();
    const name = document.getElementById("add-equip-name").value;
    const category = document.getElementById("add-equip-category").value;
    const rental_rate = parseFloat(document.getElementById("add-equip-rate").value);
    const location = document.getElementById("add-equip-location").value;
    const description = document.getElementById("add-equip-desc").value;
    const image_url = document.getElementById("add-equip-image-url").value || getCategoryFallbackImage(category);

    try {
        await fetchApi("/api/equipment", {
            method: "POST",
            body: JSON.stringify({
                name, category, rental_rate, location, description, image_url, is_available: true
            })
        });

        showToast("Equipment listed successfully!", "success");
        const modalEl = document.getElementById("addEquipmentModal");
        if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }
        const user = getCurrentUser();
        loadOwnerInventory(user.id);
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function renderLaborerDashboard(container) {
    container.innerHTML = `
        <div class="row g-4">
            <div class="col-lg-5">
                <div class="card border-0 shadow-sm rounded-3">
                    <div class="card-header bg-white py-3">
                        <h5 class="fw-bold mb-0">My Work Profile</h5>
                    </div>
                    <div class="card-body" id="laborer-profile-card">
                        <div class="text-center py-4 text-muted">Loading profile...</div>
                    </div>
                </div>
            </div>
            <div class="col-lg-7">
                <div class="card border-0 shadow-sm rounded-3">
                    <div class="card-header bg-white py-3">
                        <h5 class="fw-bold mb-0">Incoming Hiring Requests</h5>
                    </div>
                    <div class="card-body p-0" id="laborer-bookings-card">
                        <div class="text-center py-4 text-muted">Loading requests...</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    loadLaborerProfileData();
    loadLaborerBookings();
}

async function loadLaborerProfileData() {
    const card = document.getElementById("laborer-profile-card");
    if (!card) return;

    try {
        const profile = await fetchApi("/api/labor/me");
        card.innerHTML = `
            <form onsubmit="updateLaborerProfileForm(event)">
                <div class="mb-3">
                    <label class="form-label small fw-bold">Primary Skill / Role</label>
                    <input type="text" class="form-control" id="labor-edit-skill" value="${profile.skill_type}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Daily Wage Rate (₹ / Day)</label>
                    <input type="number" class="form-control" id="labor-edit-wage" value="${profile.wage_rate}" min="100" required>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">District / Operating Location</label>
                    <input type="text" class="form-control" id="labor-edit-location" value="${profile.location}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Experience / Bio</label>
                    <textarea class="form-control" id="labor-edit-desc" rows="3">${profile.description || ''}</textarea>
                </div>
                <div class="form-check form-switch mb-3">
                    <input class="form-check-input" type="checkbox" id="labor-edit-available" ${profile.is_available ? 'checked' : ''}>
                    <label class="form-check-label fw-bold">Ready for Work</label>
                </div>
                <button type="submit" class="btn btn-primary-khet w-100">Save Profile Updates</button>
            </form>
        `;
    } catch (err) {
        card.innerHTML = `
            <div class="alert alert-warning small">No labor profile found yet. Create one now:</div>
            <form onsubmit="updateLaborerProfileForm(event)">
                <div class="mb-3">
                    <label class="form-label small fw-bold">Skill Type</label>
                    <input type="text" class="form-control" id="labor-edit-skill" placeholder="e.g. Tractor Driver, Harvesting" required>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Daily Wage Rate (₹)</label>
                    <input type="number" class="form-control" id="labor-edit-wage" placeholder="600" required>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Location</label>
                    <input type="text" class="form-control" id="labor-edit-location" placeholder="e.g. Meerut, UP" required>
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">Description</label>
                    <textarea class="form-control" id="labor-edit-desc" rows="2"></textarea>
                </div>
                <button type="submit" class="btn btn-primary-khet w-100">Create Labor Profile</button>
            </form>
        `;
    }
}

async function updateLaborerProfileForm(e) {
    e.preventDefault();
    const skill_type = document.getElementById("labor-edit-skill").value;
    const wage_rate = parseFloat(document.getElementById("labor-edit-wage").value);
    const location = document.getElementById("labor-edit-location").value;
    const description = document.getElementById("labor-edit-desc").value;
    const is_available = document.getElementById("labor-edit-available")?.checked ?? true;

    try {
        await fetchApi("/api/labor", {
            method: "POST",
            body: JSON.stringify({ skill_type, wage_rate, location, description, is_available })
        });
        showToast("Profile updated successfully!");
        loadLaborerProfileData();
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function loadLaborerBookings() {
    const card = document.getElementById("laborer-bookings-card");
    if (!card) return;

    try {
        const bookings = await fetchApi("/api/bookings");
        if (!bookings || bookings.length === 0) {
            card.innerHTML = `<div class="text-center py-4 text-muted">No hire requests received yet.</div>`;
            return;
        }

        card.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>Farmer</th>
                            <th>Dates</th>
                            <th>Status</th>
                            <th>Earnings</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${bookings.map(b => `
                            <tr>
                                <td class="fw-bold">${b.farmer ? b.farmer.name : 'Farmer'}</td>
                                <td class="small">${formatDate(b.start_date)} to ${formatDate(b.end_date)}</td>
                                <td><span class="badge ${b.status === 'confirmed' ? 'bg-primary' : b.status === 'ongoing' ? 'bg-info' : b.status === 'completed' ? 'bg-success' : 'bg-warning text-dark'} text-capitalize">${b.status}</span></td>
                                <td class="fw-bold text-success">${formatINR(b.total_amount)}</td>
                                <td><a href="bookings.html" class="btn btn-outline-dark btn-sm">View</a></td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    } catch (e) {}
}

async function renderAdminDashboard(container) {
    container.innerHTML = `
        <div class="row g-3 mb-4" id="admin-stats-cards">
            <div class="col-12 text-center py-4">Loading operational statistics...</div>
        </div>

        <div class="card border-0 shadow-sm rounded-3 mb-4">
            <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                <h5 class="fw-bold mb-0">User Management</h5>
                <span class="badge bg-secondary" id="admin-user-count">Total Users</span>
            </div>
            <div class="card-body p-0" id="admin-users-table">
                <div class="text-center py-4 text-muted">Loading users...</div>
            </div>
        </div>

        <div class="card border-0 shadow-sm rounded-3">
            <div class="card-header bg-white py-3">
                <h5 class="fw-bold mb-0">Platform Booking Audit</h5>
            </div>
            <div class="card-body p-0" id="admin-bookings-audit">
                <div class="text-center py-4 text-muted">Loading bookings...</div>
            </div>
        </div>
    `;

    loadAdminStats();
    loadAdminUsers();
    loadAdminBookings();
}

async function loadAdminStats() {
    const statsContainer = document.getElementById("admin-stats-cards");
    if (!statsContainer) return;

    try {
        const stats = await fetchApi("/api/admin/stats");
        statsContainer.innerHTML = `
            <div class="col-sm-6 col-lg-3">
                <div class="card border-0 shadow-sm p-3 rounded-3 bg-white">
                    <div class="text-muted small">Registered Users</div>
                    <h3 class="fw-bold my-1 text-primary">${stats.total_users}</h3>
                    <div class="small text-muted">Farmers, Owners, Laborers</div>
                </div>
            </div>
            <div class="col-sm-6 col-lg-3">
                <div class="card border-0 shadow-sm p-3 rounded-3 bg-white">
                    <div class="text-muted small">Equipment Listed</div>
                    <h3 class="fw-bold my-1 text-success">${stats.total_equipment}</h3>
                    <div class="small text-success">${stats.active_equipment} currently active</div>
                </div>
            </div>
            <div class="col-sm-6 col-lg-3">
                <div class="card border-0 shadow-sm p-3 rounded-3 bg-white">
                    <div class="text-muted small">Total Bookings</div>
                    <h3 class="fw-bold my-1 text-info">${stats.total_bookings}</h3>
                    <div class="small text-muted">${stats.ongoing_bookings} active in field</div>
                </div>
            </div>
            <div class="col-sm-6 col-lg-3">
                <div class="card border-0 shadow-sm p-3 rounded-3 bg-white">
                    <div class="text-muted small">Platform Volume</div>
                    <h3 class="fw-bold my-1 text-success">${formatINR(stats.total_revenue)}</h3>
                    <div class="small text-muted">Successful payments</div>
                </div>
            </div>
        `;
    } catch (err) {
        statsContainer.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
    }
}

async function loadAdminUsers() {
    const tableContainer = document.getElementById("admin-users-table");
    if (!tableContainer) return;

    try {
        const users = await fetchApi("/api/admin/users");
        document.getElementById("admin-user-count").innerText = `${users.length} Users`;

        tableContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>User</th>
                            <th>Role</th>
                            <th>Phone</th>
                            <th>Location</th>
                            <th>Account Status</th>
                            <th>Toggle</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(u => `
                            <tr>
                                <td>
                                    <div class="fw-bold">${u.name}</div>
                                    <div class="text-muted small">${u.email}</div>
                                </td>
                                <td><span class="badge ${u.role === 'admin' ? 'bg-danger' : u.role === 'owner' ? 'bg-warning text-dark' : u.role === 'laborer' ? 'bg-info text-dark' : 'bg-success'} text-capitalize">${u.role}</span></td>
                                <td class="small">${u.phone || 'N/A'}</td>
                                <td class="small">${u.address || 'N/A'}</td>
                                <td>
                                    <span class="badge ${u.is_active ? 'bg-success' : 'bg-danger'}">
                                        ${u.is_active ? 'Active' : 'Deactivated'}
                                    </span>
                                </td>
                                <td>
                                    ${u.role !== 'admin' ? `
                                        <button class="btn btn-sm ${u.is_active ? 'btn-outline-danger' : 'btn-outline-success'}" onclick="toggleUserStatusApi(${u.id})">
                                            ${u.is_active ? 'Suspend' : 'Activate'}
                                        </button>
                                    ` : '<span class="text-muted small">Superadmin</span>'}
                                </td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    } catch (e) {}
}

async function toggleUserStatusApi(userId) {
    try {
        await fetchApi(`/api/admin/users/${userId}/toggle-status`, { method: "PATCH" });
        showToast("User status updated");
        loadAdminUsers();
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function loadAdminBookings() {
    const tableContainer = document.getElementById("admin-bookings-audit");
    if (!tableContainer) return;

    try {
        const bookings = await fetchApi("/api/admin/bookings");
        tableContainer.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>ID</th>
                            <th>Item</th>
                            <th>Farmer</th>
                            <th>Owner</th>
                            <th>Dates</th>
                            <th>Status</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${bookings.map(b => `
                            <tr>
                                <td class="fw-bold">#${b.id}</td>
                                <td>${b.item_details ? b.item_details.name : 'Item #' + b.item_id}</td>
                                <td>${b.farmer ? b.farmer.name : 'N/A'}</td>
                                <td>${b.owner ? b.owner.name : 'N/A'}</td>
                                <td class="small">${formatDate(b.start_date)} - ${formatDate(b.end_date)}</td>
                                <td><span class="badge ${b.status === 'confirmed' ? 'bg-primary' : b.status === 'ongoing' ? 'bg-info' : b.status === 'completed' ? 'bg-success' : 'bg-warning text-dark'} text-capitalize">${b.status}</span></td>
                                <td class="fw-bold text-success">${formatINR(b.total_amount)}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    } catch (e) {}
}

// ==========================================
// 8. LOGIN & REGISTRATION CONTROLLERS
// ==========================================
function initLoginPage() {
    const form = document.getElementById("login-form");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("login-email").value;
            const password = document.getElementById("login-password").value;
            const btn = document.getElementById("btn-login");

            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Logging in...`;

            try {
                const res = await fetchApi("/api/users/login", {
                    method: "POST",
                    body: JSON.stringify({ email, password })
                });

                setAuthSession(res.access_token, res.user);
                showToast(`Welcome back, ${res.user.name}!`, "success");

                setTimeout(() => {
                    window.location.href = "dashboard.html";
                }, 800);
            } catch (err) {
                showToast(err.message, "error");
            } finally {
                btn.disabled = false;
                btn.innerHTML = "Log In";
            }
        });
    }
}

function quickFillLogin(email, password) {
    const emailInput = document.getElementById("login-email");
    const passwordInput = document.getElementById("login-password");
    if (emailInput && passwordInput) {
        emailInput.value = email;
        passwordInput.value = password;
        showToast(`Filled credentials for ${email}`, "info");
    }
}

function initRegisterPage() {
    let selectedRole = "farmer";

    const roleButtons = document.querySelectorAll(".role-select-card");
    roleButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            roleButtons.forEach(b => b.classList.remove("border-success", "bg-light"));
            btn.classList.add("border-success", "bg-light");
            selectedRole = btn.getAttribute("data-role");
            const hiddenRoleInput = document.getElementById("register-role");
            if (hiddenRoleInput) hiddenRoleInput.value = selectedRole;
        });
    });

    const form = document.getElementById("register-form");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name = document.getElementById("reg-name").value;
            const email = document.getElementById("reg-email").value;
            const password = document.getElementById("reg-password").value;
            const phone = document.getElementById("reg-phone").value;
            const address = document.getElementById("reg-address").value;
            const role = selectedRole;
            const btn = document.getElementById("btn-register");

            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Registering...`;

            try {
                await fetchApi("/api/users/register", {
                    method: "POST",
                    body: JSON.stringify({ name, email, password, role, phone, address })
                });

                showToast("Account created successfully! Please log in.", "success");
                setTimeout(() => {
                    window.location.href = "login.html";
                }, 1200);
            } catch (err) {
                showToast(err.message, "error");
            } finally {
                btn.disabled = false;
                btn.innerHTML = "Create Account";
            }
        });
    }
}
