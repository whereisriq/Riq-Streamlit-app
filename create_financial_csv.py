# create_financial_csv.py
import csv
import random
from datetime import datetime, timedelta

print("="*60)
print("CREATING SAMPLE FINANCIAL DATA CSV")
print("="*60)

# Configuration
num_transactions = 100
start_date = datetime(2024, 1, 1)

# Sample data
categories = [
    'Salary', 'Freelance', 'Investment Income', 'Refund', 'Gift',  # Income
    'Rent', 'Utilities', 'Groceries', 'Dining Out', 'Transportation',  # Expenses
    'Entertainment', 'Healthcare', 'Insurance', 'Shopping', 'Education',
    'Subscriptions', 'Travel', 'Savings', 'Debt Payment', 'Miscellaneous'
]

merchants = {
    'Groceries': ['Walmart', 'Target', 'Whole Foods', 'Kroger', 'Trader Joes'],
    'Dining Out': ['McDonalds', 'Chipotle', 'Starbucks', 'Pizza Hut', 'Local Restaurant'],
    'Transportation': ['Shell Gas', 'Uber', 'Lyft', 'Public Transit', 'Car Repair Shop'],
    'Entertainment': ['Netflix', 'Spotify', 'Movie Theater', 'Concert Venue', 'Gaming Store'],
    'Shopping': ['Amazon', 'Best Buy', 'Clothing Store', 'Home Depot', 'Etsy'],
    'Utilities': ['Electric Company', 'Water Utility', 'Internet Provider', 'Gas Company'],
    'Healthcare': ['Pharmacy', 'Doctor Office', 'Dentist', 'Hospital', 'Health Clinic'],
    'Insurance': ['Auto Insurance Co', 'Health Insurance Co', 'Life Insurance Co'],
    'Subscriptions': ['Gym Membership', 'Magazine Subscription', 'Cloud Storage', 'Streaming Service'],
    'Travel': ['Hotel Booking', 'Airline', 'Rental Car', 'Travel Agency'],
    'Education': ['Online Course', 'Bookstore', 'Tuition Payment', 'Training Program'],
    'Salary': ['Employer Inc', 'Company Name LLC', 'Organization XYZ'],
    'Freelance': ['Client A', 'Client B', 'Freelance Platform'],
    'Investment Income': ['Brokerage Account', 'Dividend Payment', 'Interest Payment'],
    'Savings': ['Savings Account', 'Investment Account', 'Emergency Fund'],
    'Debt Payment': ['Credit Card Payment', 'Loan Payment', 'Mortgage Payment']
}

payment_methods = ['Credit Card', 'Debit Card', 'Cash', 'Bank Transfer', 'Mobile Payment']

# Amount ranges by category
amount_ranges = {
    'Salary': (2500, 5000),
    'Freelance': (500, 2000),
    'Investment Income': (50, 500),
    'Refund': (20, 200),
    'Gift': (50, 500),
    'Rent': (1000, 2000),
    'Utilities': (50, 200),
    'Groceries': (30, 150),
    'Dining Out': (15, 80),
    'Transportation': (20, 100),
    'Entertainment': (10, 150),
    'Healthcare': (50, 300),
    'Insurance': (100, 500),
    'Shopping': (25, 250),
    'Education': (50, 500),
    'Subscriptions': (10, 50),
    'Travel': (200, 1500),
    'Savings': (100, 1000),
    'Debt Payment': (100, 500),
    'Miscellaneous': (10, 100)
}

# Income vs Expense
income_categories = ['Salary', 'Freelance', 'Investment Income', 'Refund', 'Gift']

# Generate transactions
transactions = []
current_date = start_date

for i in range(num_transactions):
    # Random date within the year
    days_offset = random.randint(0, 364)
    transaction_date = start_date + timedelta(days=days_offset)
    
    # Select category
    category = random.choice(categories)
    
    # Determine transaction type
    transaction_type = 'Income' if category in income_categories else 'Expense'
    
    # Get amount based on category
    min_amt, max_amt = amount_ranges.get(category, (10, 100))
    amount = round(random.uniform(min_amt, max_amt), 2)
    
    # Get merchant
    merchant_list = merchants.get(category, ['Generic Merchant'])
    merchant = random.choice(merchant_list)
    
    # Payment method
    payment = random.choice(payment_methods)
    
    # Status
    status = random.choices(['Completed', 'Pending', 'Failed'], weights=[90, 8, 2])[0]
    
    # Create transaction
    transaction = {
        'Transaction_ID': f'TXN{100001 + i}',
        'Date': transaction_date.strftime('%Y-%m-%d'),
        'Category': category,
        'Type': transaction_type,
        'Merchant': merchant,
        'Amount': amount if transaction_type == 'Expense' else -amount,  # Income is negative for balance calculation
        'Payment_Method': payment,
        'Status': status,
        'Description': f'{transaction_type} - {category} at {merchant}'
    }
    
    transactions.append(transaction)

# Sort by date
transactions.sort(key=lambda x: x['Date'])

# Recalculate amounts for proper balance (Income positive, Expense negative)
for t in transactions:
    if t['Type'] == 'Income':
        t['Amount'] = abs(t['Amount'])
    else:
        t['Amount'] = -abs(t['Amount'])

# Save to CSV
filename = 'financial_transactions.csv'
fieldnames = ['Transaction_ID', 'Date', 'Category', 'Type', 'Merchant', 
              'Amount', 'Payment_Method', 'Status', 'Description']

with open(filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(transactions)

print(f"\n✅ Created {filename}")
print(f"📊 Generated {len(transactions)} transactions")
print(f"📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {(start_date + timedelta(days=364)).strftime('%Y-%m-%d')}")

# Calculate statistics
total_income = sum(t['Amount'] for t in transactions if t['Type'] == 'Income')
total_expenses = abs(sum(t['Amount'] for t in transactions if t['Type'] == 'Expense'))
net_balance = total_income - total_expenses

income_count = sum(1 for t in transactions if t['Type'] == 'Income')
expense_count = sum(1 for t in transactions if t['Type'] == 'Expense')

print("\n" + "="*60)
print("FINANCIAL SUMMARY")
print("="*60)
print(f"\nTotal Income: ${total_income:,.2f} ({income_count} transactions)")
print(f"Total Expenses: ${total_expenses:,.2f} ({expense_count} transactions)")
print(f"Net Balance: ${net_balance:,.2f}")

# Category breakdown
print("\nTop Expense Categories:")
expense_by_category = {}
for t in transactions:
    if t['Type'] == 'Expense':
        cat = t['Category']
        expense_by_category[cat] = expense_by_category.get(cat, 0) + abs(t['Amount'])

sorted_expenses = sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)
for i, (cat, amt) in enumerate(sorted_expenses[:5], 1):
    print(f"  {i}. {cat}: ${amt:,.2f}")

print("\nIncome Sources:")
income_by_category = {}
for t in transactions:
    if t['Type'] == 'Income':
        cat = t['Category']
        income_by_category[cat] = income_by_category.get(cat, 0) + abs(t['Amount'])

sorted_income = sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)
for i, (cat, amt) in enumerate(sorted_income, 1):
    print(f"  {i}. {cat}: ${amt:,.2f}")

# Monthly breakdown
print("\nMonthly Overview:")
monthly_data = {}
for t in transactions:
    month = t['Date'][:7]  # YYYY-MM
    if month not in monthly_data:
        monthly_data[month] = {'income': 0, 'expenses': 0}
    
    if t['Type'] == 'Income':
        monthly_data[month]['income'] += abs(t['Amount'])
    else:
        monthly_data[month]['expenses'] += abs(t['Amount'])

for month in sorted(monthly_data.keys())[:3]:  # Show first 3 months
    data = monthly_data[month]
    net = data['income'] - data['expenses']
    print(f"  {month}: Income ${data['income']:,.2f} | Expenses ${data['expenses']:,.2f} | Net ${net:,.2f}")

print("\n" + "="*60)
print("SAMPLE TRANSACTIONS (First 5)")
print("="*60)
for i, t in enumerate(transactions[:5], 1):
    print(f"\n{i}. {t['Date']} - {t['Category']}")
    print(f"   {t['Merchant']}: ${abs(t['Amount']):.2f} ({t['Type']})")
    print(f"   Payment: {t['Payment_Method']} | Status: {t['Status']}")

print("\n" + "="*60)
print("✅ FINANCIAL DATA CREATED SUCCESSFULLY!")
print("="*60)
print("\nFile Structure:")
print("  - Transaction_ID: Unique identifier")
print("  - Date: Transaction date (YYYY-MM-DD)")
print("  - Category: Spending/income category")
print("  - Type: Income or Expense")
print("  - Merchant: Where transaction occurred")
print("  - Amount: Positive for income, negative for expenses")
print("  - Payment_Method: How payment was made")
print("  - Status: Transaction status")
print("  - Description: Transaction details")

print("\n" + "="*60)
print("READY TO USE!")
print("="*60)
print("\nYou can now use this CSV file with:")
print("  - Financial analysis agents")
print("  - Budget tracking systems")
print("  - Expense categorization tools")
print("  - Financial reporting scripts")
print("="*60)