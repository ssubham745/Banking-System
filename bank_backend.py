import json
import random
import string
from pathlib import Path
import hashlib
import datetime
import pandas as pd
from sklearn.ensemble import IsolationForest
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


class Bank:
    database = 'data.json'
    data = []

    # -------- LOAD DATA -------- #
    try:
        if Path(database).exists():
            with open(database) as fs:
                data = json.load(fs)
        else:
            print("No database file found. Starting fresh.")
    except Exception as err:
        print(f"Error loading data: {err}")

    # -------- SAVE DATA -------- #
    @classmethod
    def __update(cls):
        with open(cls.database, 'w') as fs:
            json.dump(cls.data, fs, indent=4)

    # -------- HASH PIN -------- #
    @staticmethod
    def hash_pin(pin):
        return hashlib.sha256(pin.encode()).hexdigest()

    # -------- ACCOUNT NUMBER -------- #
    @classmethod
    def generate_account_number(cls):
        alpha = random.choices(string.ascii_letters, k=3)
        num = random.choices(string.digits, k=3)
        spchar = random.choices("!@#$%^&*", k=1)
        acc = alpha + num + spchar
        random.shuffle(acc)
        return "".join(acc)

    # -------- CREATE ACCOUNT -------- #
    def create_account(self, name, age, email, pin):
        if age < 18 or len(pin) != 4:
            return "Invalid age or PIN"

        user = {
            "name": name,
            "age": age,
            "email": email,
            "pin": self.hash_pin(pin),
            "accountNo.": self.generate_account_number(),
            "balance": 0,
            "transactions": []
        }

        Bank.data.append(user)
        Bank.__update()
        return user

    # -------- LOGIN -------- #
    def login(self, acc, pin):
        pin = self.hash_pin(pin)
        return next((i for i in Bank.data if i['accountNo.'] == acc and i['pin'] == pin), None)

    # -------- GET USER -------- #
    def get_user_by_account(self, acc):
        return next((i for i in Bank.data if i['accountNo.'] == acc), None)

    # -------- ML FRAUD DETECTION -------- #
    def ml_fraud_check(self, user, amount):
        tx = user.get("transactions", [])

        if len(tx) < 5:
            return None

        df = pd.DataFrame(tx)

        if 'amount' not in df.columns:
            return None

        X = df[['amount']]

        model = IsolationForest(contamination=0.2, random_state=42)
        model.fit(X)

        pred = model.predict([[amount]])

        if pred[0] == -1:
            return "🚨 Fraud Alert: Suspicious transaction detected"

        return None

    # -------- DEPOSIT -------- #
    def deposit(self, user, amount):
        if amount <= 0:
            return "Invalid amount", None, None

        fraud = self.ml_fraud_check(user, amount)

        user['balance'] += amount
        user['transactions'].append({
            "type": "deposit",
            "amount": amount,
            "time": str(datetime.datetime.now())
        })

        Bank.__update()
        return "Success", user['balance'], fraud

    # -------- WITHDRAW -------- #
    def withdraw(self, user, amount):
        if amount <= 0:
            return "Invalid amount", None, None

        if user['balance'] < amount:
            return "Insufficient balance", None, None

        fraud = self.ml_fraud_check(user, amount)

        user['balance'] -= amount
        user['transactions'].append({
            "type": "withdraw",
            "amount": amount,
            "time": str(datetime.datetime.now())
        })

        Bank.__update()
        return "Success", user['balance'], fraud

    # -------- TRANSFER -------- #
    def transfer(self, sender, receiver_acc, amount):
        if amount <= 0:
            return "Invalid amount", None, None

        if sender['accountNo.'] == receiver_acc:
            return "Cannot transfer to your own account", None, None

        receiver = self.get_user_by_account(receiver_acc)

        if not receiver:
            return "Receiver not found", None, None

        if sender['balance'] < amount:
            return "Insufficient balance", None, None

        fraud = self.ml_fraud_check(sender, amount)

        sender['balance'] -= amount
        receiver['balance'] += amount

        sender['transactions'].append({
            "type": "transfer_sent",
            "amount": amount,
            "to": receiver_acc,
            "time": str(datetime.datetime.now())
        })

        receiver['transactions'].append({
            "type": "transfer_received",
            "amount": amount,
            "from": sender['accountNo.'],
            "time": str(datetime.datetime.now())
        })

        Bank.__update()
        return "Success", sender['balance'], fraud

    # -------- UPDATE DETAILS -------- #
    def update_details(self, user, field, value):
        if field == "name":
            user['name'] = value

        elif field == "email":
            user['email'] = value

        elif field == "pin":
            if len(value) != 4:
                return "Invalid PIN"
            user['pin'] = self.hash_pin(value)

        else:
            return "Invalid field"

        Bank.__update()
        return "Success"

    # -------- DELETE ACCOUNT -------- #
    def delete_account(self, user):
        if user in Bank.data:
            Bank.data.remove(user)
            Bank.__update()
            return "Success"
        return "User not found"

    # -------- TRANSACTIONS -------- #
    def get_transactions(self, user):
        return user.get("transactions", [])
    
    def generate_pdf(self, user):
        filename = f"{user['accountNo.']}_statement.pdf"

        doc = SimpleDocTemplate(filename)
        styles = getSampleStyleSheet()

        elements = []

    # Title
        elements.append(Paragraph("Bank Statement", styles['Title']))
        elements.append(Spacer(1, 10))

    # User Info
        elements.append(Paragraph(f"Name: {user['name']}", styles['Normal']))
        elements.append(Paragraph(f"Account No: {user['accountNo.']}", styles['Normal']))
        elements.append(Paragraph(f"Balance: ₹{user['balance']}", styles['Normal']))
        elements.append(Spacer(1, 10))

    # Transactions
        elements.append(Paragraph("Transaction History:", styles['Heading2']))
        elements.append(Spacer(1, 10))

        if not user['transactions']:
            elements.append(Paragraph("No transactions available", styles['Normal']))
        else:
            for t in user['transactions']:
                line = f"{t['type']} | ₹{t['amount']} | {t['time']}"
                elements.append(Paragraph(line, styles['Normal']))
                elements.append(Spacer(1, 5))

        doc.build(elements)

        return filename
