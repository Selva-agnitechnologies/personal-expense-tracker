import sqlite3
import csv
import io
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from config import DB_PATH

def get_connection():
    """Returns a SQLite connection with row factory enabled for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database tables and indexes."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                payment_method TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Monthly budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                UNIQUE(year, month, category)
            )
        """)
        
        # Indexes for fast search and aggregation
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_lookup ON budgets(year, month, category)")
        
        conn.commit()

def add_expense(exp_date: str, category: str, amount: float, payment_method: str, description: str = "") -> int:
    """Inserts a new expense record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO expenses (date, category, amount, payment_method, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (exp_date, category, round(float(amount), 2), payment_method, description.strip())
        )
        conn.commit()
        return cursor.lastrowid

def update_expense(expense_id: int, exp_date: str, category: str, amount: float, payment_method: str, description: str = "") -> bool:
    """Updates an existing expense record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE expenses
            SET date = ?, category = ?, amount = ?, payment_method = ?, description = ?
            WHERE id = ?
            """,
            (exp_date, category, round(float(amount), 2), payment_method, description.strip(), expense_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def delete_expense(expense_id: int) -> bool:
    """Deletes an expense record by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_expense(expense_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a single expense by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_expenses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Queries expenses with flexible filters and returns a list of dictionaries."""
    query = "SELECT id, date, category, amount, payment_method, description, created_at FROM expenses WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if payment_method and payment_method != "All":
        query += " AND payment_method = ?"
        params.append(payment_method)
    if search and search.strip():
        query += " AND (description LIKE ? OR category LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term])
        
    query += " ORDER BY date DESC, id DESC"
    
    if limit:
        query += " LIMIT ?"
        params.append(limit)
        
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def get_summary_metrics(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Calculates KPI statistics: today, this week, this month, selected range, and daily average."""
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    month_start_str = today.replace(day=1).strftime("%Y-%m-%d")
    week_start_str = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Today's total
        cursor.execute("SELECT COALESCE(SUM(amount), 0), COUNT(id) FROM expenses WHERE date = ?", (today_str,))
        today_row = cursor.fetchone()
        today_total = today_row[0]
        today_count = today_row[1]
        
        # This week's total
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date >= ? AND date <= ?", (week_start_str, today_str))
        week_total = cursor.fetchone()[0]
        
        # This month's total
        cursor.execute("SELECT COALESCE(SUM(amount), 0), COUNT(id) FROM expenses WHERE date >= ? AND date <= ?", (month_start_str, today_str))
        month_row = cursor.fetchone()
        month_total = month_row[0]
        month_count = month_row[1]
        
        # Filtered range total
        filter_query = "SELECT COALESCE(SUM(amount), 0), COUNT(id) FROM expenses WHERE 1=1"
        f_params = []
        if start_date:
            filter_query += " AND date >= ?"
            f_params.append(start_date)
        if end_date:
            filter_query += " AND date <= ?"
            f_params.append(end_date)
            
        cursor.execute(filter_query, f_params)
        range_row = cursor.fetchone()
        range_total = range_row[0]
        range_count = range_row[1]
        
        # Daily average for this month
        day_of_month = max(today.day, 1)
        avg_daily = month_total / day_of_month
        
    return {
        "today_total": float(today_total),
        "today_count": int(today_count),
        "week_total": float(week_total),
        "month_total": float(month_total),
        "month_count": int(month_count),
        "range_total": float(range_total),
        "range_count": int(range_count),
        "avg_daily": float(avg_daily)
    }

def get_category_breakdown(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns grouped sum per category for charting."""
    query = """
        SELECT category, SUM(amount) as total, COUNT(id) as count
        FROM expenses
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
        
    query += " GROUP BY category ORDER BY total DESC"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [{"category": row["category"], "total": float(row["total"]), "count": row["count"]} for row in cursor.fetchall()]

def get_daily_trend(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns daily sum of expenses for trend charts."""
    query = """
        SELECT date, SUM(amount) as total, COUNT(id) as count
        FROM expenses
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
        
    query += " GROUP BY date ORDER BY date ASC"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [{"date": row["date"], "total": float(row["total"]), "count": row["count"]} for row in cursor.fetchall()]

def get_payment_breakdown(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns grouped sum per payment method."""
    query = """
        SELECT payment_method, SUM(amount) as total, COUNT(id) as count
        FROM expenses
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
        
    query += " GROUP BY payment_method ORDER BY total DESC"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [{"payment_method": row["payment_method"], "total": float(row["total"]), "count": row["count"]} for row in cursor.fetchall()]

def set_budget(year: int, month: int, category: str, amount: float):
    """Sets or updates a monthly budget."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO budgets (year, month, category, amount)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(year, month, category) DO UPDATE SET amount = excluded.amount
            """,
            (year, month, category, round(float(amount), 2))
        )
        conn.commit()

def get_budgets(year: int, month: int) -> List[Dict[str, Any]]:
    """Retrieves all budget targets for a specific month along with actual spending."""
    month_str = f"{year:04d}-{month:02d}"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get set budgets
        cursor.execute("SELECT id, category, amount FROM budgets WHERE year = ? AND month = ?", (year, month))
        budgets_map = {row["category"]: {"id": row["id"], "budget": float(row["amount"])} for row in cursor.fetchall()}
        
        # Get actual spending in this month grouped by category
        cursor.execute(
            """
            SELECT category, SUM(amount) as total_spent
            FROM expenses
            WHERE strftime('%Y-%m', date) = ?
            GROUP BY category
            """,
            (month_str,)
        )
        spending_map = {row["category"]: float(row["total_spent"]) for row in cursor.fetchall()}
        
        # Also overall month total
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE strftime('%Y-%m', date) = ?", (month_str,))
        overall_spent = float(cursor.fetchone()[0])
        
    results = []
    # If there is an overall budget
    if "Overall" in budgets_map:
        ov_b = budgets_map["Overall"]["budget"]
        results.append({
            "category": "🌟 Overall Monthly Budget",
            "budget": ov_b,
            "spent": overall_spent,
            "remaining": ov_b - overall_spent,
            "pct": round((overall_spent / ov_b * 100), 1) if ov_b > 0 else 0,
            "id": budgets_map["Overall"]["id"]
        })
        
    # Categories with budgets
    for cat, b_info in budgets_map.items():
        if cat == "Overall":
            continue
        spent = spending_map.get(cat, 0.0)
        results.append({
            "category": cat,
            "budget": b_info["budget"],
            "spent": spent,
            "remaining": b_info["budget"] - spent,
            "pct": round((spent / b_info["budget"] * 100), 1) if b_info["budget"] > 0 else 0,
            "id": b_info["id"]
        })
        
    return results

def delete_budget(budget_id: int) -> bool:
    """Deletes a budget by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        conn.commit()
        return cursor.rowcount > 0

def export_csv_string(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    search: Optional[str] = None
) -> str:
    """Generates a CSV string representation of expenses for download."""
    records = get_expenses(start_date, end_date, category, payment_method, search)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Category", "Amount", "Payment Method", "Description", "Created At"])
    for r in records:
        writer.writerow([r["id"], r["date"], r["category"], r["amount"], r["payment_method"], r["description"], r["created_at"]])
    return output.getvalue()

def seed_sample_data():
    """Seeds sample transactions across recent days for demonstration."""
    sample_items = [
        (-6, "🛒 Groceries", 1450.0, "📱 UPI / Digital Wallet", "Weekly supermarket essentials"),
        (-5, "🍔 Food & Dining", 420.0, "📱 UPI / Digital Wallet", "Lunch at cafe with team"),
        (-5, "🚗 Transportation", 180.0, "💵 Cash", "Metro recharge & auto ride"),
        (-4, "💡 Bills & Utilities", 1250.0, "💳 Credit Card", "Broadband internet bill"),
        (-3, "🍔 Food & Dining", 350.0, "📱 UPI / Digital Wallet", "Dinner takeout"),
        (-2, "🛍️ Shopping", 1899.0, "💳 Credit Card", "Sneakers online sale"),
        (-2, "🚗 Transportation", 120.0, "📱 UPI / Digital Wallet", "Cab commute"),
        (-1, "🏥 Health & Medical", 450.0, "📱 UPI / Digital Wallet", "Pharmacy prescription"),
        (0, "🍔 Food & Dining", 240.0, "📱 UPI / Digital Wallet", "Morning breakfast & coffee"),
        (0, "📦 Subscriptions", 499.0, "💳 Credit Card", "OTT streaming plan")
    ]
    today = date.today()
    for days_offset, category, amount, p_method, desc in sample_items:
        d = (today + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        add_expense(d, category, amount, p_method, desc)
        
    # Seed sample budget for this month
    set_budget(today.year, today.month, "Overall", 15000.0)
    set_budget(today.year, today.month, "🍔 Food & Dining", 4000.0)
    set_budget(today.year, today.month, "🛒 Groceries", 5000.0)
