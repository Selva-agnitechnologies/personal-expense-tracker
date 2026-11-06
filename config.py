import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "expenses.db"

# Default Categories
CATEGORIES = [
    "🍔 Food & Dining",
    "🛒 Groceries",
    "🚗 Transportation",
    "💡 Bills & Utilities",
    "🎬 Entertainment",
    "🛍️ Shopping",
    "🏥 Health & Medical",
    "📚 Education",
    "✈️ Travel",
    "💼 Work & Business",
    "📦 Subscriptions",
    "✨ Miscellaneous"
]

# Payment Methods
PAYMENT_METHODS = [
    "📱 UPI / Digital Wallet",
    "💵 Cash",
    "💳 Credit Card",
    "💳 Debit Card",
    "🏦 Net Banking",
    "🔄 Other"
]

# Supported Currencies
CURRENCIES = {
    "₹ INR (Indian Rupee)": "₹",
    "$ USD (US Dollar)": "$",
    "€ EUR (Euro)": "€",
    "£ GBP (British Pound)": "£",
    "C$ CAD (Canadian Dollar)": "C$",
    "A$ AUD (Australian Dollar)": "A$",
    "S$ SGD (Singapore Dollar)": "S$",
    "د.إ AED (UAE Dirham)": "AED "
}

DEFAULT_CURRENCY = "₹ INR (Indian Rupee)"

