import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

@st.cache_data
def load_data():
    df = pd.read_excel("Infiniti Product ID.xlsx", skiprows=2)
    df.dropna(how="all", inplace=True)
    df.fillna("", inplace=True)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.insert(0, 'Product ID', ['PID' + str(i).zfill(5) for i in range(1, len(df) + 1)])
    if 'ID' in df.columns:
        df.drop(columns=['ID'], inplace=True)
    if 'Last Purchase Date' in df.columns:
        df['Last Purchase Date'] = pd.to_datetime(df['Last Purchase Date'], errors='coerce')
        df.loc[df['Product Description'].str.contains("sof remote keypad", case=False, na=False), 'Last Purchase Date'] = pd.to_datetime("2023-04-03")
    return df

df = load_data()

with st.sidebar:
    st.title("📘 Product Reference")
    page_size = 15
    total_pages = len(df) // page_size + (len(df) % page_size > 0)
    page = st.number_input("Page", min_value=1, max_value=total_pages, step=1)
    start = (page - 1) * page_size
    end = start + page_size
    st.dataframe(df[['Product ID', 'Product Description']].iloc[start:end], use_container_width=True)

st.title("🔍 Infiniti Inventory Search & Dashboard")

tab1, tab2 = st.tabs(["🔎 Search Inventory", "📊 Dashboard"])

with tab1:
    st.subheader("🔎 Search Inventory")
    search_by = st.selectbox("Search by", ["Product Description", "Product ID", "Party Name (Company)"])
    query = st.text_input(f"Enter search term for {search_by}:")
    if query:
        query = query.lower()
        if search_by == "Product Description":
            keywords = query.split()
            results = df[df["Product Description"].apply(lambda desc: all(kw in desc.lower() for kw in keywords))]
        elif search_by == "Product ID":
            results = df[df["Product ID"].str.lower().str.contains(query)]
        elif search_by == "Party Name (Company)":
            results = df[df["Party Name"].str.lower().str.contains(query)]
        if not results.empty:
            st.success(f"{len(results)} result(s) found.")
            st.dataframe(results.reset_index(drop=True))
        else:
            st.warning("No matching products found.")
    else:
        st.info("Enter a search term to begin.")

with tab2:
    st.subheader("📦 Inventory Overview")
    total_products = len(df)
    unique_vendors = df['Party Name'].nunique()
    latest_purchase = df['Last Purchase Date'].max()
    latest_purchase_str = latest_purchase.strftime('%d-%b-%Y') if pd.notnull(latest_purchase) else "N/A"
    col1, col2, col3 = st.columns(3)
    col1.metric("🛒 Total Products", total_products)
    col2.metric("🏢 Unique Vendors", unique_vendors)
    col3.metric("📅 Last Purchase", latest_purchase_str)
    st.divider()
    st.subheader("🕒 10 Most Recent Purchases")
    if 'Last Purchase Date' in df.columns:
        recent = df.dropna(subset=['Last Purchase Date']).sort_values(by='Last Purchase Date', ascending=False).head(10)
        st.dataframe(recent[['Product ID', 'Product Description', 'Party Name', 'Price', 'Last Purchase Date']], use_container_width=True)
    st.subheader("🥧 Vendor Product Share")
    vendor_counts = df['Party Name'].value_counts().reset_index()
    vendor_counts.columns = ['Party Name', 'Count']
    pie = alt.Chart(vendor_counts).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field="Count", type="quantitative"),
        color=alt.Color(field="Party Name", type="nominal"),
        tooltip=["Party Name", "Count"]
    ).properties(width=500, height=400)
    st.altair_chart(pie, use_container_width=True)
