import streamlit as st
import pandas as pd
from bank_backend import Bank

bank = Bank()

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

    # Sidebar balance
    st.sidebar.metric("💰 Balance", user['balance'])

    menu = st.sidebar.selectbox("Menu", [
        "Dashboard", "Deposit", "Withdraw",
        "Transfer", "Transactions", "Logout"
    ])

    # ================= DASHBOARD ================= #
    if menu == "Dashboard":
        st.header("📊 Account Dashboard")

        # ---- USER INFO ---- #
        col1, col2 = st.columns(2)

        col1.write(f"👤 Name: {user['name']}")
        col1.write(f"📧 Email: {user['email']}")

        col2.write(f"🏦 Account No: {user['accountNo.']}")
        col2.metric("💰 Balance", user['balance'])

        # ---- TRANSACTION SUMMARY ---- #
        transactions = user.get("transactions", [])

        total_deposit = sum(t['amount'] for t in transactions if t['type'] == 'deposit')
        total_withdraw = sum(t['amount'] for t in transactions if t['type'] == 'withdraw')

        col3, col4 = st.columns(2)
        col3.metric("📥 Total Deposited", total_deposit)
        col4.metric("📤 Total Withdrawn", total_withdraw)

        # ---- MINI STATEMENT ---- #
        st.subheader("📜 Recent Transactions")

        if not transactions:
            st.info("No transactions yet")
        else:
            last_5 = transactions[-5:][::-1]

            for t in last_5:
                if t['type'] == "deposit":
                    st.success(f"➕ Deposited ₹{t['amount']} on {t['time']}")
                elif t['type'] == "withdraw":
                    st.error(f"➖ Withdrawn ₹{t['amount']} on {t['time']}")
                else:
                    st.warning(f"🔄 Transfer ₹{t['amount']} on {t['time']}")

    # ================= DEPOSIT ================= #
    elif menu == "Deposit":
        amt = st.number_input("Amount", min_value=1)

        if st.button("Deposit"):
            res, balance = bank.deposit(user, amt)

            if res == "Success":
                st.success("Deposit successful ✅")
                st.metric("Updated Balance", balance)
            else:
                st.error(res)

    # ================= WITHDRAW ================= #
    elif menu == "Withdraw":
        st.header("💸 Withdraw Money")

        amt = st.number_input("Enter amount", min_value=1)

        if st.button("Withdraw"):
            res, balance = bank.withdraw(user, amt)   # ✅ unpack

            if res == "Success":
                st.success("Withdrawal successful ✅")
                st.metric("Updated Balance", balance)
            else:
                st.error(res)

    # ================= TRANSFER ================= #
    elif menu == "Transfer":
        st.info(f"Current Balance: {user['balance']}")

        recv = st.text_input("Receiver Account Number")

        # Receiver preview
        if recv:
            r = bank.get_user_by_account(recv)
            if r:
                st.success(f"Receiver: {r['name']}")
            else:
                st.error("Receiver not found")

        amt = st.number_input("Amount", min_value=1)

        if st.button("Transfer"):
            res, balance = bank.transfer(user, recv, amt)

            if res == "Success":
                st.success("Transfer successful ✅")
                st.metric("Updated Balance", balance)
            else:
                st.error(res)

    # ================= TRANSACTIONS ================= #
    elif menu == "Transactions":
        st.header("📜 Transaction History")

        tx = bank.get_transactions(user)

        if not tx:
            st.info("No transactions yet")
        else:
            st.write(tx)

        # 📊 Graph
            import pandas as pd
            df = pd.DataFrame(tx)

            if 'amount' in df.columns:
                st.subheader("📈 Transaction Graph")
                st.line_chart(df['amount'])

    # -------- PDF DOWNLOAD -------- #
        st.subheader("📄 Download Statement")

        if st.button("Generate PDF"):
            file = bank.generate_pdf(user)
            st.success("PDF Generated ✅")

            with open(file, "rb") as f:
                st.download_button(
                label="⬇️ Download PDF",
                data=f,
                file_name=file,
                mime="application/pdf"
                )

    # ================= LOGOUT ================= #
    elif menu == "Logout":
        st.session_state['user'] = None
        st.rerun()