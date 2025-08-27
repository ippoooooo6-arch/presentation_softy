import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime

def init_db():
    conn = sqlite3.connect('expense_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (
                     id       INTEGER PRIMARY KEY AUTOINCREMENT,
                     amount   REAL,
                     category TEXT,
                     date     TEXT
                 )''')
    conn.commit()
    return conn, c
conn, c = init_db()
def add_expense():
    st.subheader("Add New Expense")
    with st.form("expense_form"):
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        category = st.text_input("Category (Food, Transport, etc.)")
        date_input = st.date_input("Date", datetime.now())
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than 0")
                return
            if not category.strip():
                st.error("Category cannot be empty")
                return

            c.execute("""
                      INSERT INTO expenses (amount, category, date)
                      VALUES (?, ?, ?)
                      """, (amount, category.strip(), date_input.strftime("%Y-%m-%d")))
            conn.commit()
            new_id = c.lastrowid
            st.success(f"Expense added with ID: {new_id}")

def list_expenses():
    st.subheader("All Expenses")
    c.execute('SELECT * FROM expenses ORDER BY id DESC')
    rows = c.fetchall()

    if not rows:
        st.info("No expenses found.")
        return
    st.table(rows)

def monthly_expense():
    st.subheader("Monthly Expenses Summary")

    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Year", min_value=2000, max_value=2100, value=datetime.now().year)
    with col2:
        month = st.selectbox("Month", list(range(1, 13)), format_func=lambda x: datetime(2000, x, 1).strftime('%B'))

    if st.button("Calculate Monthly Total"):
        ym = f"{year}-{month:02d}"
        c.execute("""
                  SELECT COALESCE(SUM(amount), 0)
                  FROM expenses
                  WHERE strftime('%Y-%m', date) = ?
                  """, (ym,))
        result = c.fetchone()
        total = result[0]
        if total == 0 :
            st.warning("There are no expenses for that month.")
        else:
            st.success(f"Total expenses for {year}-{month:02d}: ${total:.2f}")

def delete_expense():
    st.subheader("Delete Expenses")
    option = st.radio("Delete by:", ["ID", "Category", "Date", "Amount"])
    if option == "ID":
        expense_id = st.number_input("Enter expense ID", min_value=1)
        if st.button("Select Expense"):
            c.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            row = c.fetchone()
            if row:
                st.session_state["row_to_delete"] = row
            else:
                st.error("No expense found with that ID.")
        if "row_to_delete" in st.session_state:
            st.warning(f"Expense to delete: {st.session_state['row_to_delete']}")
            with st.form("confirm_delete_form_id"):
                submitted = st.form_submit_button("Confirm Deletion")
                if submitted:
                    c.execute("DELETE FROM expenses WHERE id = ?", (st.session_state['row_to_delete'][0],))
                    conn.commit()
                    st.success(f"Expense {st.session_state['row_to_delete'][0]} deleted.")
                    del st.session_state["row_to_delete"]

    elif option == "Category":
        category = st.text_input("Enter category").strip()
        if st.button("Select Category"):
            c.execute("SELECT * FROM expenses WHERE category = ?", (category,))
            rows = c.fetchall()
            if rows:
                st.session_state["rows_to_delete"] = rows
                st.warning(f"Found {len(rows)} expense(s) in category '{category}'")
            else:
                st.error("No expenses found in this category.")

        if "rows_to_delete" in st.session_state:
            with st.form("confirm_delete_form_category"):
                submitted = st.form_submit_button("Confirm Deletion")
                if submitted:
                    c.execute("DELETE FROM expenses WHERE category = ?", (category,))
                    conn.commit()
                    st.success(f"All expenses in category '{category}' deleted.")
                    del st.session_state["rows_to_delete"]
    elif option == "Date":
        date = st.date_input("Enter date")
        if st.button("Select Date"):
            date_str = date.strftime("%Y-%m-%d")
            c.execute("SELECT * FROM expenses WHERE date = ?", (date_str,))
            rows = c.fetchall()
            if rows:
                st.session_state["rows_to_delete"] = rows
                st.warning(f"Found {len(rows)} expense(s) on {date_str}")
            else:
                st.error("No expenses found on this date.")

        if "rows_to_delete" in st.session_state:
            with st.form("confirm_delete_form_date"):
                submitted = st.form_submit_button("Confirm Deletion")
                if submitted:
                    c.execute("DELETE FROM expenses WHERE date = ?", (date_str,))
                    conn.commit()
                    st.success(f"All expenses on {date_str} deleted.")
                    del st.session_state["rows_to_delete"]
    elif option == "Amount":
        amount = st.number_input("Enter amount", min_value=0.0, format="%.2f")
        if st.button("Select Amount"):
            c.execute("SELECT * FROM expenses WHERE amount = ?", (amount,))
            rows = c.fetchall()
            if rows:
                st.session_state["rows_to_delete"] = rows
                st.warning(f"Found {len(rows)} expense(s) with amount ${amount:.2f}")
            else:
                st.error("No expenses found with that amount.")

        if "rows_to_delete" in st.session_state:
            with st.form("confirm_delete_form_amount"):
                submitted = st.form_submit_button("Confirm Deletion")
                if submitted:
                    c.execute("DELETE FROM expenses WHERE amount = ?", (amount,))
                    conn.commit()
                    st.success(f"All expenses with amount ${amount:.2f} deleted.")
                    del st.session_state["rows_to_delete"]
def category_chart():
    st.subheader("Expenses by Category")
    c.execute("""
              SELECT category, SUM(amount) as total
              FROM expenses
              GROUP BY category
              ORDER BY total DESC
              """)
    data = c.fetchall()

    if not data:
        st.info("No expense data available for chart.")
        return

    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]
    fig, ax = plt.subplots()
    ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    st.pyplot(fig)

    fig2, ax2 = plt.subplots()
    ax2.bar(categories, amounts)
    ax2.set_ylabel('Amount ($)')
    ax2.set_title('Expenses by Category')
    plt.tight_layout()

    st.pyplot(fig2)

def main():
    st.title("💰 Expense Tracker")

    menu = ["Add Expense", "View Expenses", "Delete Expenses", "Monthly Summary", "Category Charts", "About"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Add Expense":
        add_expense()
    elif choice == "View Expenses":
        list_expenses()
    elif choice == "Delete Expenses":
        delete_expense()
    elif choice == "Monthly Summary":
        monthly_expense()
    elif choice == "Category Charts":
        category_chart()
    elif choice == "About":
        st.info("A simple expense tracker app built with Streamlit")
        st.info("Features: Add expenses, view history, delete records, and visualize spending by category")

main()