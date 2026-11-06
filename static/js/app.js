// Daily Expense Tracker - Application Logic

let currencySymbol = localStorage.getItem("ems_currency") || "₹";
let currentPreset = "thismonth";
let categoryChartInstance = null;
let trendChartInstance = null;
let paymentChartInstance = null;
let currentExpensesCache = [];

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
    initCurrency();
    initBudgetSelectors();
    setPreset("thismonth");
});

// Currency formatting
function initCurrency() {
    const selector = document.getElementById("currencySelector");
    if (selector) {
        // match existing symbol
        for (let opt of selector.options) {
            if (opt.value === currencySymbol) {
                selector.value = currencySymbol;
                break;
            }
        }
    }
    updateCurrencyLabels();
}

function changeCurrency(symbol) {
    currencySymbol = symbol;
    localStorage.setItem("ems_currency", symbol);
    updateCurrencyLabels();
    renderExpenses(currentExpensesCache);
    loadAllData();
}

function updateCurrencyLabels() {
    document.querySelectorAll(".currencyLabel").forEach(el => {
        el.textContent = currencySymbol;
    });
}

function formatAmount(val) {
    if (val === undefined || val === null || isNaN(val)) return `${currencySymbol}0.00`;
    return `${currencySymbol}${parseFloat(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Preset Handler
function setPreset(preset) {
    currentPreset = preset;
    const today = new Date();
    const todayStr = formatDate(today);

    let start = "";
    let end = todayStr;

    if (preset === "today") {
        start = todayStr;
    } else if (preset === "7days") {
        const d = new Date();
        d.setDate(d.getDate() - 6);
        start = formatDate(d);
    } else if (preset === "thismonth") {
        start = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-01`;
    } else if (preset === "30days") {
        const d = new Date();
        d.setDate(d.getDate() - 29);
        start = formatDate(d);
    } else if (preset === "all") {
        start = "";
        end = "";
    }

    document.getElementById("filterStartDate").value = start;
    document.getElementById("filterEndDate").value = end;

    // Update preset pills styling
    document.querySelectorAll(".preset-btn").forEach(btn => {
        if (btn.getAttribute("data-preset") === preset) {
            btn.className = "preset-btn px-3 py-1.5 text-xs font-semibold rounded-lg border border-brand-500 bg-brand-50 text-brand-700";
        } else {
            btn.className = "preset-btn px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors";
        }
    });

    loadAllData();
}

function onCustomDateChange() {
    // When dates manually selected, unselect preset pills
    document.querySelectorAll(".preset-btn").forEach(btn => {
        btn.className = "preset-btn px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors";
    });
    applyFilters();
}

function formatDate(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function getFilterParams() {
    const start = document.getElementById("filterStartDate").value;
    const end = document.getElementById("filterEndDate").value;
    const cat = document.getElementById("filterCategory").value;
    const pay = document.getElementById("filterPayment").value;
    const search = document.getElementById("filterSearch").value;

    const params = new URLSearchParams();
    if (start) params.append("start_date", start);
    if (end) params.append("end_date", end);
    if (cat && cat !== "All") params.append("category", cat);
    if (pay && pay !== "All") params.append("payment_method", pay);
    if (search && search.trim()) params.append("search", search.trim());

    return params;
}

function applyFilters() {
    loadAllData();
}

// Master Load Data
async function loadAllData() {
    const params = getFilterParams();
    await Promise.all([
        loadKPIs(params),
        loadExpenses(params),
        loadCharts(params),
        loadBudgets()
    ]);
}

// Load KPIs
async function loadKPIs(params) {
    try {
        const res = await fetch(`/api/metrics?${params.toString()}`);
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById("kpiToday").textContent = formatAmount(data.today_total);
        document.getElementById("kpiTodayCount").textContent = `${data.today_count} transaction${data.today_count === 1 ? '' : 's'}`;

        document.getElementById("kpiWeek").textContent = formatAmount(data.week_total);
        document.getElementById("kpiMonth").textContent = formatAmount(data.month_total);
        document.getElementById("kpiMonthCount").textContent = `${data.month_count} transaction${data.month_count === 1 ? '' : 's'}`;

        document.getElementById("kpiAvgDaily").textContent = formatAmount(data.avg_daily);
    } catch (e) {
        console.error("Failed to load KPIs", e);
    }
}

// Load Expenses
async function loadExpenses(params) {
    try {
        const res = await fetch(`/api/expenses?${params.toString()}`);
        if (!res.ok) return;
        const data = await res.json();
        currentExpensesCache = data.expenses || [];
        renderExpenses(currentExpensesCache);
    } catch (e) {
        console.error("Failed to load expenses", e);
    }
}

function renderExpenses(expenses) {
    const tbody = document.getElementById("expensesTableBody");
    const emptyState = document.getElementById("emptyState");
    const totalBadge = document.getElementById("filteredTotalBadge");
    const historySummaryText = document.getElementById("historySummaryText");

    tbody.innerHTML = "";

    if (!expenses || expenses.length === 0) {
        emptyState.classList.remove("hidden");
        totalBadge.textContent = `Total: ${formatAmount(0)}`;
        historySummaryText.textContent = "0 transactions matching filter";
        return;
    }

    emptyState.classList.add("hidden");

    let totalSum = 0;
    expenses.forEach(item => {
        totalSum += item.amount;
        const tr = document.createElement("tr");
        tr.className = "hover:bg-slate-50 transition-colors";

        const formattedDate = new Date(item.date).toLocaleDateString(undefined, {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });

        tr.innerHTML = `
            <td class="px-5 py-3 whitespace-nowrap text-slate-600 font-medium">${formattedDate}</td>
            <td class="px-5 py-3 whitespace-nowrap">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100">
                    ${escapeHtml(item.category)}
                </span>
            </td>
            <td class="px-5 py-3 text-slate-700 font-medium">${escapeHtml(item.description || "—")}</td>
            <td class="px-5 py-3 whitespace-nowrap text-slate-500">
                <span class="inline-flex items-center text-xs font-medium bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md">
                    ${escapeHtml(item.payment_method)}
                </span>
            </td>
            <td class="px-5 py-3 whitespace-nowrap text-right font-bold text-slate-900">${formatAmount(item.amount)}</td>
            <td class="px-5 py-3 whitespace-nowrap text-center space-x-1">
                <button onclick="openEditModal(${item.id}, '${item.date}', '${escapeAttr(item.category)}', ${item.amount}, '${escapeAttr(item.payment_method)}', '${escapeAttr(item.description || '')}')" title="Edit" class="p-1.5 text-slate-400 hover:text-indigo-600 rounded-lg hover:bg-slate-100">
                    <i class="fa-solid fa-pen text-xs"></i>
                </button>
                <button onclick="deleteExpense(${item.id})" title="Delete" class="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50">
                    <i class="fa-solid fa-trash-can text-xs"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    totalBadge.textContent = `Total (${expenses.length}): ${formatAmount(totalSum)}`;
    historySummaryText.textContent = `Showing ${expenses.length} transaction${expenses.length === 1 ? '' : 's'}`;
}

// Load Charts
async function loadCharts(params) {
    try {
        const [catRes, dailyRes, payRes] = await Promise.all([
            fetch(`/api/charts/category?${params.toString()}`),
            fetch(`/api/charts/daily?${params.toString()}`),
            fetch(`/api/charts/payment?${params.toString()}`)
        ]);

        const catData = await catRes.json();
        const dailyData = await dailyRes.json();
        const payData = await payRes.json();

        renderCategoryChart(catData);
        renderDailyTrendChart(dailyData);
        renderPaymentChart(payData);
    } catch (e) {
        console.error("Failed to load charts", e);
    }
}

const modernPalette = [
    '#6366f1', '#ec4899', '#f59e0b', '#10b981', '#3b82f6',
    '#8b5cf6', '#14b8a6', '#f43f5e', '#84cc16', '#06b6d4',
    '#eab308', '#64748b'
];

function renderCategoryChart(data) {
    const ctx = document.getElementById("categoryChart").getContext("2d");
    const totalBadge = document.getElementById("categoryChartTotal");

    const totalSum = data.reduce((acc, curr) => acc + curr.total, 0);
    totalBadge.textContent = totalSum > 0 ? formatAmount(totalSum) : "";

    if (categoryChartInstance) categoryChartInstance.destroy();

    if (!data || data.length === 0) {
        categoryChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['No Data'],
                datasets: [{ data: [1], backgroundColor: ['#e2e8f0'] }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });
        return;
    }

    categoryChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.category),
            datasets: [{
                data: data.map(d => d.total),
                backgroundColor: modernPalette.slice(0, data.length),
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 12, font: { size: 11, family: 'Inter, sans-serif' }, padding: 12 }
                },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const val = ctx.raw || 0;
                            const pct = totalSum > 0 ? Math.round((val / totalSum) * 100) : 0;
                            return ` ${formatAmount(val)} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderDailyTrendChart(data) {
    const ctx = document.getElementById("trendChart").getContext("2d");
    if (trendChartInstance) trendChartInstance.destroy();

    const labels = data.map(d => {
        const parts = d.date.split("-");
        return `${parts[1]}/${parts[2]}`;
    });
    const values = data.map(d => d.total);

    trendChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Spent',
                data: values,
                backgroundColor: '#4f46e5',
                borderRadius: 6,
                maxBarThickness: 32
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        callback: function(v) { return `${currencySymbol}${v}`; },
                        font: { size: 10 }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(ctx) { return ` Spent: ${formatAmount(ctx.raw)}`; }
                    }
                }
            }
        }
    });
}

function renderPaymentChart(data) {
    const ctx = document.getElementById("paymentChart").getContext("2d");
    if (paymentChartInstance) paymentChartInstance.destroy();

    paymentChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.payment_method),
            datasets: [{
                data: data.map(d => d.total),
                backgroundColor: '#0d9488',
                borderRadius: 6,
                maxBarThickness: 24
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        callback: function(v) { return `${currencySymbol}${v}`; },
                        font: { size: 10 }
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 11 } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(ctx) { return ` Total: ${formatAmount(ctx.raw)}`; }
                    }
                }
            }
        }
    });
}

// Monthly Budgets
async function loadBudgets() {
    const now = new Date();
    try {
        const res = await fetch(`/api/budgets?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
        if (!res.ok) return;
        const data = await res.json();
        renderBudgets(data.budgets, now);
    } catch (e) {
        console.error("Failed to load budgets", e);
    }
}

function renderBudgets(budgets, dateObj) {
    const container = document.getElementById("budgetsList");
    const monthLabel = document.getElementById("currentBudgetMonthLabel");
    monthLabel.textContent = `(${dateObj.toLocaleString('default', { month: 'long', year: 'numeric' })})`;

    if (!budgets || budgets.length === 0) {
        container.innerHTML = `<p class="text-xs text-slate-400 italic py-3 text-center">No budgets set for this month. Click "+ Set Limits" to create one.</p>`;
        return;
    }

    container.innerHTML = "";
    budgets.forEach(b => {
        let barColor = "bg-emerald-500";
        let statusBadge = `<span class="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md">${b.pct}%</span>`;

        if (b.pct >= 90) {
            barColor = "bg-rose-500";
            statusBadge = `<span class="text-xs font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-md animate-pulse">⚠️ ${b.pct}% (${formatAmount(Math.abs(b.remaining))} ${b.remaining < 0 ? 'over' : 'left'})</span>`;
        } else if (b.pct >= 70) {
            barColor = "bg-amber-500";
            statusBadge = `<span class="text-xs font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md">${b.pct}%</span>`;
        }

        const cappedPct = Math.min(b.pct, 100);

        const row = document.createElement("div");
        row.className = "bg-slate-50 p-3 rounded-xl border border-slate-200";
        row.innerHTML = `
            <div class="flex items-center justify-between mb-1.5">
                <span class="text-xs font-bold text-slate-800">${escapeHtml(b.category)}</span>
                <div class="flex items-center space-x-2">
                    ${statusBadge}
                    <button onclick="deleteBudget(${b.id})" class="text-slate-300 hover:text-rose-500 text-xs ml-1" title="Delete Limit">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                <div class="${barColor} h-2.5 rounded-full transition-all duration-500" style="width: ${cappedPct}%"></div>
            </div>
            <div class="flex items-center justify-between mt-1 text-[11px] text-slate-500 font-medium">
                <span>Spent: <b class="text-slate-700">${formatAmount(b.spent)}</b></span>
                <span>Budget: <b class="text-slate-700">${formatAmount(b.budget)}</b></span>
            </div>
        `;
        container.appendChild(row);
    });
}

// Modal Handlers
function openAddModal() {
    document.getElementById("addModal").classList.remove("hidden");
    document.getElementById("addAmount").focus();
}

function closeAddModal() {
    document.getElementById("addModal").classList.add("hidden");
    document.getElementById("addExpenseForm").reset();
    document.getElementById("addDate").value = formatDate(new Date());
}

async function submitAddExpense(e) {
    e.preventDefault();
    const payload = {
        date: document.getElementById("addDate").value,
        category: document.getElementById("addCategory").value,
        amount: parseFloat(document.getElementById("addAmount").value),
        payment_method: document.getElementById("addPayment").value,
        description: document.getElementById("addDesc").value
    };

    try {
        const res = await fetch("/api/expenses", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            closeAddModal();
            showToast("Expense recorded successfully!", "success");
            loadAllData();
        } else {
            showToast(data.error || "Failed to add expense", "error");
        }
    } catch (err) {
        showToast("Error connecting to server", "error");
    }
}

function openEditModal(id, date, category, amount, payment, desc) {
    document.getElementById("editId").value = id;
    document.getElementById("editDate").value = date;
    document.getElementById("editCategory").value = category;
    document.getElementById("editAmount").value = amount;
    document.getElementById("editPayment").value = payment;
    document.getElementById("editDesc").value = desc;
    document.getElementById("editModal").classList.remove("hidden");
}

function closeEditModal() {
    document.getElementById("editModal").classList.add("hidden");
}

async function submitEditExpense(e) {
    e.preventDefault();
    const id = document.getElementById("editId").value;
    const payload = {
        date: document.getElementById("editDate").value,
        category: document.getElementById("editCategory").value,
        amount: parseFloat(document.getElementById("editAmount").value),
        payment_method: document.getElementById("editPayment").value,
        description: document.getElementById("editDesc").value
    };

    try {
        const res = await fetch(`/api/expenses/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            closeEditModal();
            showToast("Expense updated!", "success");
            loadAllData();
        } else {
            showToast(data.error || "Update failed", "error");
        }
    } catch (err) {
        showToast("Server error", "error");
    }
}

async function deleteExpense(id) {
    if (!confirm("Are you sure you want to delete this expense?")) return;
    try {
        const res = await fetch(`/api/expenses/${id}`, { method: "DELETE" });
        if (res.ok) {
            showToast("Expense deleted", "info");
            loadAllData();
        }
    } catch (err) {
        showToast("Failed to delete", "error");
    }
}

// Budget Modal
function initBudgetSelectors() {
    const monthSelect = document.getElementById("budgetMonth");
    const yearSelect = document.getElementById("budgetYear");
    if (!monthSelect || !yearSelect) return;

    const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const now = new Date();

    months.forEach((m, idx) => {
        const opt = document.createElement("option");
        opt.value = idx + 1;
        opt.textContent = m;
        if (idx === now.getMonth()) opt.selected = true;
        monthSelect.appendChild(opt);
    });

    for (let y = now.getFullYear() - 1; y <= now.getFullYear() + 2; y++) {
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = y;
        if (y === now.getFullYear()) opt.selected = true;
        yearSelect.appendChild(opt);
    }
}

function openBudgetModal() {
    document.getElementById("budgetModal").classList.remove("hidden");
    document.getElementById("budgetAmount").focus();
}

function closeBudgetModal() {
    document.getElementById("budgetModal").classList.add("hidden");
    document.getElementById("budgetForm").reset();
    initBudgetSelectors();
}

async function submitBudget(e) {
    e.preventDefault();
    const payload = {
        month: parseInt(document.getElementById("budgetMonth").value),
        year: parseInt(document.getElementById("budgetYear").value),
        category: document.getElementById("budgetCategory").value,
        amount: parseFloat(document.getElementById("budgetAmount").value)
    };

    try {
        const res = await fetch("/api/budgets", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            closeBudgetModal();
            showToast("Budget target saved!", "success");
            loadBudgets();
        } else {
            showToast(data.error || "Failed to set budget", "error");
        }
    } catch (err) {
        showToast("Server error", "error");
    }
}

async function deleteBudget(id) {
    if (!confirm("Delete this budget limit?")) return;
    try {
        const res = await fetch(`/api/budgets/${id}`, { method: "DELETE" });
        if (res.ok) {
            showToast("Budget limit deleted", "info");
            loadBudgets();
        }
    } catch (err) {
        showToast("Server error", "error");
    }
}

// Export CSV
function exportCSV() {
    const params = getFilterParams();
    window.location.href = `/api/export?${params.toString()}`;
}

// Seed Demo Data
async function seedSampleData() {
    try {
        const res = await fetch("/api/seed", { method: "POST" });
        if (res.ok) {
            showToast("Loaded sample expenses and budget data!", "success");
            loadAllData();
        }
    } catch (e) {
        showToast("Failed to seed sample data", "error");
    }
}

// Toast System
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");

    let bg = "bg-slate-900 text-white";
    let icon = '<i class="fa-solid fa-circle-info mr-2 text-blue-400"></i>';
    if (type === "success") {
        bg = "bg-emerald-900 text-emerald-100 border border-emerald-700";
        icon = '<i class="fa-solid fa-circle-check mr-2 text-emerald-400"></i>';
    } else if (type === "error") {
        bg = "bg-rose-900 text-rose-100 border border-rose-700";
        icon = '<i class="fa-solid fa-triangle-exclamation mr-2 text-rose-400"></i>';
    }

    toast.className = `${bg} px-4 py-3 rounded-xl shadow-xl text-xs font-semibold flex items-center fade-in pointer-events-auto`;
    toast.innerHTML = `${icon}<span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Utility Helpers
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function escapeAttr(str) {
    if (!str) return "";
    return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

