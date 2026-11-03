import json
import os

DATA_FILE = "expenses.json"

def load_expenses():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return []

def save_expenses(expenses):
    with open(DATA_FILE, "w") as file:
            json.dump(expenses, file, indent=4)

def add_expense(expenses):
    try:
        title = input("Enter expense description (e.g., Groceries): ")
        amount = float(input("Enter amount ($): "))
        category = input("Enter category (e.g., Food, Travel, Bills): ")
        
        expense = {
            "title": title,
            "amount": amount,
            "category": category
        }
        expenses.append(expense)
        save_expenses(expenses)
        print("✅ Expense added successfully!\n")
    except ValueError:
        print("❌ Invalid amount. Please enter a valid number.\n")

def view_expenses(expenses):
    if not expenses:
        print("📁 No expenses recorded yet.\n")
        return
    
    print("\n--- Your Expenses ---")
    total = 0
    for idx, exp in enumerate(expenses, 1):
        print(f"{idx}. {exp['title']} - ${exp['amount']:.2f} [{exp['category']}]")
        total += exp['amount']
    print(f"\nTotal Spending: ${total:.2f}\n")

def main():
    expenses = load_expenses()
    while True:
        print("=== Personal Expense Tracker ===")
        print("1. Add Expense")
        print("2. View Expenses & Total")
        print("3. Exit")
        
        choice = input("Choose an option (1-3): ")
        
        if choice == "1":
            add_expense(expenses)
        elif choice == "2":
            view_expenses(expenses)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please choose between 1 and 3.\n")

if __name__ == "__main__":
    main()