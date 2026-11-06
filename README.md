# 💰 Daily Expense Tracker (EMS)

A sleek, lightweight, and modern **Daily Expense Tracker** built with **Python**, **Flask**, and **SQLite**. It lets you quickly log daily expenses, track monthly budgets, view interactive charts, filter history, and export data to CSV.

---

## 🌟 Key Features

1. **⚡ Fast & Modern Dashboard**
   - Real-time KPI summaries: **Today's Spend**, **This Week**, **This Month**, and **Daily Average**.
   - Multiple currency support (₹ INR, $ USD, € EUR, £ GBP, etc.) with instant switching.

2. **📊 Visual Charts & Statistics**
   - **Category Breakdown (Donut Chart)**: Visual slice of where your money goes with percentages.
   - **Daily Spending Trend (Bar Chart)**: Daily totals over selected timeframes.
   - **Payment Method Distribution (Bar Chart)**: Cash, UPI, Cards, Net Banking split.

3. **📝 Effortless Expense Logging**
   - Date, categorized tags with emojis (🍔 Food, 🛒 Groceries, 🚗 Transportation, 💡 Utilities, etc.).
   - Payment method (UPI, Cash, Credit Card, Debit Card, etc.).
   - Edit and delete transactions inline at any time.

4. **🎯 Monthly Budget Tracking**
   - Set spending limits (Overall monthly limit or per-category limits).
   - Visual progress bars with color-coded alert badges:
     - 🟢 Normal (<70%)
     - 🟡 Warning (70% - 90%)
     - 🔴 Exceeded (>90% or over budget)

5. **🔍 Filter, Search & Export**
   - Quick date preset buttons: *Today*, *Last 7 Days*, *This Month*, *Last 30 Days*, *All Time*.
   - Filter by specific Category and Payment Method.
   - Instant search across notes and descriptions.
   - **One-click Export to CSV** for your filtered records.

6. **💾 Local SQLite Database**
   - Zero configuration required.
   - Data is stored securely in `data/expenses.db`.

---

## 🚀 Quick Start

### Option 1: Double-Click Launcher (Windows)
Simply double-click:
```
run.bat
```
This automatically initializes the environment, launches the app, and opens your browser at `http://localhost:5000`.

---

### Option 2: Command Line

1. **Activate virtual environment:**
   ```powershell
   .\.venv\Scripts\activate
   ```

2. **Install dependencies (if not already installed):**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open in browser:**
   ```
   http://localhost:5000
   ```

---

## 📁 Project Structure

```
ems/
├── app.py                 # Flask server & REST API endpoints
├── config.py              # Categories, payment options & currency configuration
├── database.py            # SQLite database schema, CRUD operations & aggregations
├── requirements.txt       # Minimal Python dependencies
├── run.bat                # 1-click Windows batch launcher
├── run.ps1                # 1-click PowerShell launcher
├── .gitignore             # Git ignore file for Python & SQLite files
├── data/                  # Local SQLite database directory
│   └── expenses.db        # SQLite database file
├── templates/
│   └── index.html         # Responsive web dashboard UI (Tailwind + FontAwesome + Chart.js)
└── static/
    └── js/
        └── app.js         # Reactive frontend controller & charts integration
```
