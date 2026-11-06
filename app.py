import os
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, Response
import database
import config

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize DB on start
database.init_db()

@app.route("/")
def index():
    """Renders the main dashboard page."""
    return render_template(
        "index.html",
        categories=config.CATEGORIES,
        payment_methods=config.PAYMENT_METHODS,
        currencies=config.CURRENCIES,
        default_currency=config.DEFAULT_CURRENCY,
        today_date=date.today().strftime("%Y-%m-%d")
    )

@app.route("/api/config", methods=["GET"])
def get_config():
    """Returns application configuration."""
    return jsonify({
        "categories": config.CATEGORIES,
        "payment_methods": config.PAYMENT_METHODS,
        "currencies": config.CURRENCIES,
        "default_currency": config.DEFAULT_CURRENCY
    })

@app.route("/api/metrics", methods=["GET"])
def metrics():
    """Returns top-level spending KPIs."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    data = database.get_summary_metrics(start_date, end_date)
    return jsonify(data)

@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    """Returns filtered expenses."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    category = request.args.get("category")
    payment_method = request.args.get("payment_method")
    search = request.args.get("search")
    limit = request.args.get("limit", type=int)
    
    expenses = database.get_expenses(start_date, end_date, category, payment_method, search, limit)
    return jsonify({"expenses": expenses, "count": len(expenses)})

@app.route("/api/expenses", methods=["POST"])
def create_expense():
    """Adds a new expense."""
    data = request.get_json() or {}
    exp_date = data.get("date")
    category = data.get("category")
    amount = data.get("amount")
    payment_method = data.get("payment_method")
    description = data.get("description", "")
    
    if not exp_date or not category or not amount or not payment_method:
        return jsonify({"error": "Missing required fields (date, category, amount, payment_method)"}), 400
        
    try:
        amount_val = float(amount)
        if amount_val <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400
    except ValueError:
        return jsonify({"error": "Invalid amount number"}), 400
        
    new_id = database.add_expense(exp_date, category, amount_val, payment_method, description)
    return jsonify({"success": True, "id": new_id, "message": "Expense recorded successfully!"}), 201

@app.route("/api/expenses/<int:expense_id>", methods=["PUT"])
def edit_expense(expense_id):
    """Updates an existing expense."""
    data = request.get_json() or {}
    exp_date = data.get("date")
    category = data.get("category")
    amount = data.get("amount")
    payment_method = data.get("payment_method")
    description = data.get("description", "")
    
    if not exp_date or not category or not amount or not payment_method:
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        amount_val = float(amount)
        if amount_val <= 0:
            return jsonify({"error": "Amount must be greater than zero"}), 400
    except ValueError:
        return jsonify({"error": "Invalid amount number"}), 400
        
    success = database.update_expense(expense_id, exp_date, category, amount_val, payment_method, description)
    if not success:
        return jsonify({"error": "Expense not found"}), 404
        
    return jsonify({"success": True, "message": "Expense updated successfully!"})

@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def remove_expense(expense_id):
    """Deletes an expense."""
    success = database.delete_expense(expense_id)
    if not success:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify({"success": True, "message": "Expense deleted."})

@app.route("/api/charts/category", methods=["GET"])
def chart_category():
    """Returns category breakdown for donut chart."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    data = database.get_category_breakdown(start_date, end_date)
    return jsonify(data)

@app.route("/api/charts/daily", methods=["GET"])
def chart_daily():
    """Returns daily spending trend for bar/line chart."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    data = database.get_daily_trend(start_date, end_date)
    return jsonify(data)

@app.route("/api/charts/payment", methods=["GET"])
def chart_payment():
    """Returns payment method breakdown."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    data = database.get_payment_breakdown(start_date, end_date)
    return jsonify(data)

@app.route("/api/budgets", methods=["GET"])
def get_budgets():
    """Retrieves monthly budget vs actual spend."""
    today = date.today()
    year = request.args.get("year", default=today.year, type=int)
    month = request.args.get("month", default=today.month, type=int)
    budgets = database.get_budgets(year, month)
    return jsonify({"budgets": budgets, "year": year, "month": month})

@app.route("/api/budgets", methods=["POST"])
def save_budget():
    """Sets a monthly budget."""
    data = request.get_json() or {}
    year = data.get("year")
    month = data.get("month")
    category = data.get("category")
    amount = data.get("amount")
    
    if not year or not month or not category or amount is None:
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        amount_val = float(amount)
        if amount_val < 0:
            return jsonify({"error": "Budget cannot be negative"}), 400
    except ValueError:
        return jsonify({"error": "Invalid budget amount"}), 400
        
    database.set_budget(int(year), int(month), category, amount_val)
    return jsonify({"success": True, "message": "Budget saved!"})

@app.route("/api/budgets/<int:budget_id>", methods=["DELETE"])
def remove_budget(budget_id):
    """Deletes a budget."""
    success = database.delete_budget(budget_id)
    if not success:
        return jsonify({"error": "Budget not found"}), 404
    return jsonify({"success": True, "message": "Budget removed."})

@app.route("/api/export", methods=["GET"])
def export_csv():
    """Exports filtered expenses as a downloadable CSV."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    category = request.args.get("category")
    payment_method = request.args.get("payment_method")
    search = request.args.get("search")
    
    csv_data = database.export_csv_string(start_date, end_date, category, payment_method, search)
    filename = f"expenses_{date.today().strftime('%Y%m%d')}.csv"
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route("/api/seed", methods=["POST"])
def seed_data():
    """Seeds sample transactions for testing."""
    database.seed_sample_data()
    return jsonify({"success": True, "message": "Sample transactions & budgets added!"})

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" 🚀 Daily Expense Tracker is running!")
    print(" 🌐 Open your browser at: http://localhost:5000")
    print("="*50 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=True)

