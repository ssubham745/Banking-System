import streamlit as st
import pandas as pd
from bank_backend import Bank

bank = Bank()

st.set_page_config(page_title="Smart Bank", layout="wide")

st.title("🏦 Smart Banking System")

# -------- SESSION -------- #
if 'user' not in st.session_state:
    st.session_state['user'] = None

# -------- LOGIN / CREATE -------- #
if st.session_state['user'] is None:
    option = st.selectbox("Choose", ["Login", "Create Account"])

    if option == "Login":
        acc = st.text_input("Account Number")
        pin = st.text_input("PIN", type="password")

        if st.button("Login"):
            user = bank.login(acc, pin)
            if user:
                st.session_state['user'] = user
                st.rerun()
            else:
                st.error("Invalid credentials")

    else:
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=0)
        email = st.text_input("Email")
        pin = st.text_input("PIN", type="password")

        if st.button("Create"):
            res = bank.create_account(name, age, email, pin)
            if isinstance(res, dict):
                st.success("Account created")
                st.write("Account No:", res['accountNo.'])
            else:
                st.error(res)

# -------- MAIN APP -------- #
else:
    user = st.session_state['user']

    # Sidebar
    st.sidebar.title("🏦 Smart Bank")
    st.sidebar.metric("💰 Balance", user['balance'])
    st.sidebar.write(f"👤 {user['name']}")

    menu = st.sidebar.selectbox("Menu", [
        "Dashboard", "Deposit", "Withdraw",
        "Transfer", "Transactions",
        "Update Profile", "Delete Account",
        "Logout"
    ])

    # ================= DASHBOARD ================= #
    if menu == "Dashboard":
        st.header("📊 Dashboard")

        col1, col2 = st.columns(2)

        col1.write(f"👤 Name: {user['name']}")
        col1.write(f"📧 Email: {user['email']}")

        col2.write(f"🏦 Account: {user['accountNo.']}")
        col2.metric("💰 Balance", user['balance'])

    # ================= DEPOSIT ================= #
    elif menu == "Deposit":
        amt = st.number_input("Amount", min_value=1)

        if st.button("Deposit"):
            res, bal, fraud = bank.deposit(user, amt)

            if res == "Success":
                st.success("Deposit successful ✅")
                st.metric("Updated Balance", bal)

                if fraud:
                    st.warning(fraud)
            else:
                st.error(res)

    # ================= WITHDRAW ================= #
    elif menu == "Withdraw":
        amt = st.number_input("Amount", min_value=1)

        if st.button("Withdraw"):
            res, bal, fraud = bank.withdraw(user, amt)

            if res == "Success":
                st.success("Withdraw successful ✅")
                st.metric("Updated Balance", bal)

                if fraud:
                    st.warning(fraud)
            else:
                st.error(res)

    # ================= TRANSFER ================= #
    elif menu == "Transfer":
        st.info(f"Balance: {user['balance']}")

        recv = st.text_input("Receiver Account")

        # Receiver preview
        if recv:
            r = bank.get_user_by_account(recv)
            if r:
                st.success(f"Receiver: {r['name']}")
            else:
                st.error("Receiver not found")

        amt = st.number_input("Amount", min_value=1)

        if st.button("Transfer"):
            res, bal, fraud = bank.transfer(user, recv, amt)

            if res == "Success":
                st.success("Transfer successful ✅")
                st.metric("Updated Balance", bal)

                if fraud:
                    st.warning(fraud)
            else:
                st.error(res)

    # ================= TRANSACTIONS ================= #
    elif menu == "Transactions":
        st.header("📜 Transactions")

        tx = bank.get_transactions(user)

        if tx:
            df = pd.DataFrame(tx)

            st.line_chart(df['amount'])

            for t in reversed(tx):
                st.info(f"{t['type']} | ₹{t['amount']} | {t['time']}")
        else:
            st.info("No transactions")

        # PDF
        if st.button("📄 Generate Statement"):
            file = bank.generate_pdf(user)

            with open(file, "rb") as f:
                st.download_button("Download PDF", f, file)

    # ================= UPDATE PROFILE ================= #
    elif menu == "Update Profile":
        st.header("✏️ Update Profile")

        field = st.selectbox("Field", ["name", "email", "pin"])
        value = st.text_input("New value")

        if st.button("Update"):
            res = bank.update_details(user, field, value)

            if res == "Success":
                st.success("Profile updated ✅")
                st.rerun()
            else:
                st.error(res)

    # ================= DELETE ACCOUNT ================= #
    elif menu == "Delete Account":
        st.header("⚠️ Delete Account")

        confirm = st.text_input("Type DELETE to confirm")

        if st.button("Delete"):
            if confirm == "DELETE":
                bank.delete_account(user)
                st.session_state['user'] = None
                st.success("Account deleted")
                st.rerun()
            else:
                st.error("Type DELETE correctly")

    # ================= LOGOUT ================= #
    elif menu == "Logout":
        st.session_state['user'] = None
        st.rerun()
