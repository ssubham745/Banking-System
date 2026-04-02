import json
import random
import string
from pathlib import Path
import hashlib
import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


class Bank:
    database = 'data.json'
    data = []

    try:
        if Path(database).exists():
            with open(database) as fs:
                data = json.load(fs)
    except:
        data = []

    @classmethod
    def __update(cls):
        with open(cls.database, 'w') as fs:
            json.dump(cls.data, fs, indent=4)

    @staticmethod
    def hash_pin(pin):
        return hashlib.sha256(pin.encode()).hexdigest()

    @classmethod
    def generate_account_number(cls):
        alpha = random.choices(string.ascii_letters, k=3)
        num = random.choices(string.digits, k=3)
        sp = random.choices("!@#$%", k=1)
        acc = alpha + num + sp
        random.shuffle(acc)
        return "".join(acc)

    def create_account(self, name, age, email, pin):
        if age < 18 or len(pin) != 4:
            return "Invalid details"

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

    def login(self, acc, pin):
        pin = self.hash_pin(pin)
        return next((i for i in Bank.data if i['accountNo.'] == acc and i['pin'] == pin), None)

    def deposit(self, user, amount):
        if amount <= 0:
            return "Invalid amount", None

        user['balance'] += amount
        user['transactions'].append({
            "type": "deposit",
            "amount": amount,
            "time": str(datetime.datetime.now())
        })

        Bank.__update()
        return "Success", user['balance']

    def withdraw(self, user, amount):
        if amount <= 0:
            return "Invalid amount", None

        if user['balance'] < amount:
            return "Insufficient balance", None

        user['balance'] -= amount
        user['transactions'].append({
            "type": "withdraw",
            "amount": amount,
            "time": str(datetime.datetime.now())
        })

        Bank.__update()
        return "Success", user['balance']

    def get_user_by_account(self, acc):
        return next((i for i in Bank.data if i['accountNo.'] == acc), None)

    def transfer(self, sender, receiver_acc, amount):
        if amount <= 0:
            return "Invalid amount", None

        if sender['accountNo.'] == receiver_acc:
            return "Cannot transfer to your own account", None

        receiver = self.get_user_by_account(receiver_acc)

        if not receiver:
            return "Receiver not found", None

        if sender['balance'] < amount:
            return "Insufficient balance", None

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
        return "Success", sender['balance']

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

    def delete_account(self, user):
        Bank.data.remove(user)
        Bank.__update()
        return "Success"

    def get_transactions(self, user):
        return user['transactions']

    def generate_pdf(self, user):
        filename = f"{user['accountNo.']}_statement.pdf"
        doc = SimpleDocTemplate(filename)
        styles = getSampleStyleSheet()

        elements = []
        elements.append(Paragraph("Bank Statement", styles['Title']))
        elements.append(Paragraph(f"Name: {user['name']}", styles['Normal']))
        elements.append(Paragraph(f"Account: {user['accountNo.']}", styles['Normal']))
        elements.append(Paragraph(f"Balance: {user['balance']}", styles['Normal']))

        elements.append(Paragraph("Transactions:", styles['Heading2']))

        for t in user['transactions']:
            elements.append(Paragraph(str(t), styles['Normal']))

        doc.build(elements)
        return filename