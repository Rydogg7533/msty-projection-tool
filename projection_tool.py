import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="MSTY Projection Tool", layout="wide")
st.title("📈 MSTY Compounding Growth Simulator")

st.sidebar.header("Simulation Inputs")
total_shares = st.sidebar.number_input("Total Share Count", min_value=0, value=10000)
avg_cost = st.sidebar.number_input("Weighted Average Cost Basis ($)", min_value=0.0, value=25.00)
holding_months = st.sidebar.slider("Holding Period (Months)", min_value=1, max_value=240, value=24)
avg_div = st.sidebar.number_input("Average Monthly Dividend per Share ($)", min_value=0.0, value=2.0)

fed_tax = st.sidebar.slider("Federal Tax Rate (%)", 0, 50, 20)
state_tax = st.sidebar.slider("State Tax Rate (%)", 0, 20, 5)
acct_type = st.sidebar.selectbox("Account Type", ["Taxable", "Tax Deferred"])

drip = st.sidebar.checkbox("Reinvest Dividends?")
if drip:
    reinvest_percent = st.sidebar.slider("Percent of Dividends to Reinvest (%)", 0, 100, 100)
else:
    reinvest_percent = 0
    withdrawal = st.sidebar.number_input("Withdraw this Dollar Amount Monthly ($)", min_value=0, value=2000)

reinvest_price = st.sidebar.number_input("Average Reinvestment Share Price ($)", min_value=1.0, value=25.0)
dca = st.sidebar.number_input("Monthly Dollar-Cost Average Investment ($)", min_value=0.0, value=0.0)
frequency = st.sidebar.selectbox("How would you like to view the projection?", ["Monthly", "Yearly", "Total"])

run_sim = st.sidebar.button("Run Simulation")

if run_sim:
    monthly_data = []
    shares = total_shares
    total_dividends = 0
    total_reinvested = 0
    total_dca = 0
    total_tax = 0

    for month in range(1, holding_months + 1):
        gross_div = shares * avg_div
        tax = 0 if acct_type == "Tax Deferred" else gross_div * (fed_tax + state_tax) / 100
        net_div = gross_div - tax
        if drip:
            reinvest_amount = net_div * (reinvest_percent / 100)
        else:
            reinvest_amount = max(0, net_div - withdrawal)
        new_shares = (reinvest_amount + dca) / reinvest_price
        shares += new_shares
        total_dividends += net_div
        total_reinvested += reinvest_amount
        total_tax += tax
        total_dca += dca
        monthly_data.append({
            "Month": month,
            "Year": (month - 1) // 12 + 1,
            "Shares": shares,
            "Net Dividends": net_div,
            "Reinvested": reinvest_amount,
            "DCA Added": dca,
            "Taxes Owed": tax
        })

    df = pd.DataFrame(monthly_data)
    if frequency == "Monthly":
        df_view = df.copy()
        df_view["Period"] = df_view["Month"]
    elif frequency == "Yearly":
        df_view = df.groupby("Year").agg({
            "Shares": "last",
            "Net Dividends": "sum",
            "Reinvested": "sum",
            "DCA Added": "sum",
            "Taxes Owed": "sum"
        }).reset_index().rename(columns={"Year": "Period"})
    else:
        df_view = pd.DataFrame([{
            "Period": "Total",
            "Shares": df["Shares"].iloc[-1],
            "Net Dividends": df["Net Dividends"].sum(),
            "Reinvested": df["Reinvested"].sum(),
            "DCA Added": df["DCA Added"].sum(),
            "Taxes Owed": df["Taxes Owed"].sum()
        }])

    st.success(f"📈 Final Share Count: {shares:,.2f}")
    st.success(f"💸 Total Dividends Collected: ${total_dividends:,.2f}")
    st.success(f"🔁 Total Reinvested: ${total_reinvested:,.2f}")
    st.success(f"📦 Total DCA Added: ${total_dca:,.2f}")
    st.success(f"⚖️ Total Taxes Owed: ${total_tax:,.2f}")

    fig = px.bar(df_view, x="Period", y="Shares", title=f"Share Count View: {frequency}")
    st.plotly_chart(fig)

    st.subheader("📋 Projection Table")
    st.dataframe(df_view.style.format({
        "Shares": "{:,.2f}",
        "Net Dividends": "${:,.2f}",
        "Reinvested": "${:,.2f}",
        "DCA Added": "${:,.2f}",
        "Taxes Owed": "${:,.2f}"
    }))