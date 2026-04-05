# Smart Expense Tracker
This app has been built using Streamlit and deployed with Streamlit Community Cloud.

https://khra0005-smart-expense-tracker.streamlit.app/

This application is built to help users track expenses, manage budgets, and gain insights into their spending habits.

## Overview
The Smart Expense Tracker allows users to:
*   Record daily transactions
*   Automatically categorize expenses
*   Set and monitor budgets
*   Receive alerts when overspending
*   Analyze spending patterns through dashboards
*   Manage and edit historical transactions

## Features
### Expense Management
*   Add transactions
*   Auto-category suggestion
*   Custom categories & keyword rules
*   Edit and delete transactions

### Dashboard & Analytics
*   Daily, weekly, monthly views
*   Charts and forecasting
*   Predictive analytics

### Budget Alerts
*   Monthly and category budgets
*   Alerts for overspending
*   Budget progress tracking

### Customization
*   Custom categories
*   Keyword rules
*   Case-insensitive matching

### Data Handling
*   SQLite storage
*   CSV export
*   Auto data folder creation

## Project Structure
app/
├── core/
│   ├── analytics.py
│   ├── budget_logic.py
│   ├── categories.py
│   ├── config.py
│   ├── database.py
│   └── helpers.py
│
├── tabs/
│   ├── add_expense.py
│   ├── budget_alerts.py
│   ├── dashboard.py
│   ├── export.py
│   ├── manage.py
│   └── powerbi_dashboard.py
│
├── ui/
│   └── components.py
│
├── data/
│   ├── budget_settings.json
│   ├── custom_categories.json
│   ├── custom_keywords.json
│   ├── Expenses.csv
│   └── Expenses.db
│
├── main.py
├── README.md
└── requirements.txt

## Technologies Used
*   Streamlit
*   Pandas
*   Matplotlib
*   SQLite
*   Python

## How to Run the Project
### 1. Install dependencies
`pip install -r requirements.txt`

### 2. Run the pipeline
`python main.py`

### 3. Run the Streamlit app
`python -m streamlit run streamlit.py`

## Output
*   ➕ Add Expense 
*   🚨 Budget Alerts
*   📊 Dashboard
*   📈 Power BI Dashboard
*   🛠️ Manage
*   📁 Export