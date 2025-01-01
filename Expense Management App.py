import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import csv
import os

# Set database path to user's home directory
app_folder = os.path.join(os.path.expanduser("~"), "ExpenseManagementApp")
os.makedirs(app_folder, exist_ok=True)
db_path = os.path.join(app_folder, "expenses.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    amount REAL,
    category TEXT,
    description TEXT,
    date TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY,
    amount REAL
)
""")
conn.commit()

# Functions
def set_income():
    income = income_entry.get()
    if not income:
        messagebox.showwarning("Input Error", "Please enter a valid income amount.")
        return
    try:
        income = float(income)
        if income <= 0:
            raise ValueError("Income must be a positive number.")
        cursor.execute("DELETE FROM income")
        cursor.execute("INSERT INTO income (amount) VALUES (?)", (income,))
        conn.commit()
        refresh_summary()
        income_frame.pack_forget()
        messagebox.showinfo("Success", "Income has been set successfully.")
    except ValueError:
        messagebox.showerror("Input Error", "Income must be a positive number.")

def add_expense():
    amount = amount_entry.get()
    category = category_var.get()
    description = description_entry.get()
    date = datetime.now().strftime("%Y-%m-%d")

    if not amount or not category:
        messagebox.showwarning("Input Error", "Please fill all required fields.")
        return

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be a positive number.")

        # Consolidate expenses under a single category
        cursor.execute("SELECT id, amount FROM expenses WHERE category = ?", (category,))
        existing = cursor.fetchone()
        if existing:
            updated_amount = existing[1] + amount
            cursor.execute("UPDATE expenses SET amount = ? WHERE id = ?", (updated_amount, existing[0]))
        else:
            cursor.execute("INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
                           (amount, category, description, date))
        conn.commit()
        refresh_expenses()
        refresh_summary()
        clear_fields()
        messagebox.showinfo("Success", "Expense has been added successfully.")
    except ValueError:
        messagebox.showerror("Input Error", "Amount must be a positive number.")

def refresh_expenses():
    for row in tree.get_children():
        tree.delete(row)
    cursor.execute("SELECT * FROM expenses")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)

def refresh_summary():
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_spending = cursor.fetchone()[0] or 0
    cursor.execute("SELECT amount FROM income")
    row = cursor.fetchone()
    income = row[0] if row else 0
    potential_savings = income - total_spending
    income_label.config(text=f"Monthly Income: ₹{income:.2f}")
    spending_label.config(text=f"Total Spending: ₹{total_spending:.2f}")
    savings_label.config(text=f"Potential Savings: ₹{potential_savings:.2f}")

def clear_fields():
    amount_entry.delete(0, tk.END)
    category_var.set("")
    description_entry.delete(0, tk.END)

def show_chart():
    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    data = cursor.fetchall()
    if not data:
        messagebox.showinfo("No Data", "No expenses to display.")
        return
    categories, amounts = zip(*data)
    plt.figure(figsize=(6, 6))
    plt.pie(amounts, labels=categories, autopct=lambda p: f'{p:.1f}%\n(₹{p * sum(amounts) / 100:.2f})', startangle=140)
    plt.title("Expenses Distribution")
    plt.show()

def reset_data():
    confirm = messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all data?")
    if confirm:
        cursor.execute("DELETE FROM expenses")
        cursor.execute("DELETE FROM income")
        conn.commit()
        refresh_expenses()
        refresh_summary()
        income_frame.pack(pady=10, fill="x", padx=20)
        income_label.config(text="Monthly Income: ₹0.0")
        messagebox.showinfo("Data Reset", "All data has been reset. Please enter your income.")

def download_report():
    cursor.execute("SELECT * FROM expenses")
    data = cursor.fetchall()
    if not data:
        messagebox.showinfo("No Data", "No expenses to download.")
        return
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv", 
        filetypes=[("CSV files", "*.csv")],
        title="Save Report As"
    )
    if file_path:
        with open(file_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Amount", "Category", "Description", "Date"])
            writer.writerows(data)
        messagebox.showinfo("Report Downloaded", f"Expenses report downloaded to '{file_path}'.")

# GUI setup
root = tk.Tk()
root.title("Expense Management App")
root.geometry("800x600")
root.configure(bg="#f5f5f5")

# Styles
style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background="#f5f5f5")
style.configure("TButton", background="#4CAF50", foreground="white", font=("Arial", 10, "bold"), padding=5)
style.map("TButton", background=[("active", "#45a049")])
style.configure("TLabel", background="#f5f5f5", font=("Arial", 10))
style.configure("Treeview", font=("Arial", 10))
style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

# Income Section
income_frame = ttk.Frame(root)
cursor.execute("SELECT amount FROM income")
if cursor.fetchone() is None:
    income_frame.pack(pady=10, fill="x", padx=20)

income_label = ttk.Label(income_frame, text="Enter Monthly Income: ", font=("Arial", 12))
income_label.grid(row=0, column=0, padx=5)

income_entry = ttk.Entry(income_frame, font=("Arial", 10))
income_entry.grid(row=0, column=1, padx=5)

ttk.Button(income_frame, text="Set Income", command=set_income).grid(row=0, column=2, padx=5)

# Input Frame
input_frame = ttk.LabelFrame(root, text="Add Expense", padding=(10, 5))
input_frame.pack(pady=10, fill="x", padx=20)

ttk.Label(input_frame, text="Amount:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
amount_entry = ttk.Entry(input_frame)
amount_entry.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
category_var = tk.StringVar()
category_menu = ttk.Combobox(input_frame, textvariable=category_var, values=[
    "Food", "Travel", "Entertainment", "Shopping", "Stocks", "Other"
])
category_menu.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(input_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
description_entry = ttk.Entry(input_frame)
description_entry.grid(row=2, column=1, padx=5, pady=5)

ttk.Button(input_frame, text="Add Expense", command=add_expense).grid(row=3, columnspan=2, pady=10)

# Expense Table
tree_frame = ttk.LabelFrame(root, text="Expense Details", padding=(10, 5))
tree_frame.pack(pady=10, fill="both", padx=20, expand=True)

tree = ttk.Treeview(tree_frame, columns=("ID", "Amount", "Category", "Description", "Date"), show="headings")
tree.heading("ID", text="ID")
tree.heading("Amount", text="Amount")
tree.heading("Category", text="Category")
tree.heading("Description", text="Description")
tree.heading("Date", text="Date")
tree.pack(fill="both", expand=True)

# Summary Section
summary_frame = ttk.LabelFrame(root, text="Summary", padding=(10, 5))
summary_frame.pack(pady=10, fill="x", padx=20)

spending_label = ttk.Label(summary_frame, text="Total Spending: ₹0.0", font=("Arial", 12))
spending_label.grid(row=0, column=0, padx=5, pady=5)

savings_label = ttk.Label(summary_frame, text="Potential Savings: ₹0.0", font=("Arial", 12))
savings_label.grid(row=0, column=1, padx=5, pady=5)

# Action Buttons
button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

ttk.Button(button_frame, text="Show Pie Chart", command=show_chart).grid(row=0, column=0, padx=10)
ttk.Button(button_frame, text="Reset Data", command=reset_data).grid(row=0, column=1, padx=10)
ttk.Button(button_frame, text="Download Report", command=download_report).grid(row=0, column=2, padx=10)

# Initial Data Load
refresh_expenses()
refresh_summary()

# Start Application
root.mainloop()
