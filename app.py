import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1w5iRXmL_VGxKlY5G_XlmtaxRBkw_voR5TZlPUkpmR94"
WORKSHEET_NAME = "Sheet1"

def one_time_product_id_push():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("inventory-app-462520-075277afddb4.json", scopes=scope)
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df.dropna(how="all", inplace=True)
    df.fillna("", inplace=True)

    df = df[df['Product Description'].astype(str).str.strip() != '']

    if 'Product ID' not in df.columns or df['Product ID'].astype(str).str.strip().eq("").all():
        df.insert(0, 'Product ID', ['PID' + str(i).zfill(5) for i in range(1, len(df) + 1)])
        worksheet.clear()
        worksheet.update("A1", [df.columns.tolist()] + df.astype(str).values.tolist())
        return True

    return False

pushed = one_time_product_id_push()
if pushed:
    st.success("✅ Product IDs pushed to Google Sheets (one-time only).")

@st.cache_data
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("inventory-app-462520-075277afddb4.json", scopes=scope)
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

    expected_headers = ['Product Description', 'Party Name', 'Price', 'Last Purchase Date']
    data = worksheet.get_all_records(expected_headers=expected_headers)
    df = pd.DataFrame(data)

    df.dropna(how="all", inplace=True)
    df.fillna("", inplace=True)

    # 🚫 Remove rows where 'Product Description' is empty or just whitespace
    df = df[df['Product Description'].astype(str).str.strip() != '']

    # ✅ Assign Product IDs only to valid rows
    if 'Product ID' not in df.columns:
        product_ids = ['PID' + str(i).zfill(5) for i in range(1, len(df) + 1)]
        df.insert(0, 'Product ID', product_ids)

    # 🗓️ Format purchase date
    if 'Last Purchase Date' in df.columns:
        df['Last Purchase Date'] = pd.to_datetime(df['Last Purchase Date'], errors='coerce')
        df.loc[df['Product Description'].str.contains("sof remote keypad", case=False, na=False), 'Last Purchase Date'] = pd.to_datetime("2023-04-03")

    return df


df = load_data()

# Sidebar
with st.sidebar:
    st.title("📘 Product Reference")
    page_size = 15
    total_pages = len(df) // page_size + (len(df) % page_size > 0)
    page = st.number_input("Page", min_value=1, max_value=total_pages, step=1)
    start = (page - 1) * page_size
    end = start + page_size
    st.dataframe(df[['Product ID', 'Product Description']].iloc[start:end], use_container_width=True)

# Main interface
st.title("🔍 Infiniti Inventory Search & Dashboard")
tab1, tab2 = st.tabs(["🔎 Search Inventory", "📊 Dashboard"])

with tab1:
    st.subheader("🔎 Search Inventory")
    search_by = st.selectbox("Search by", ["Product Description", "Product ID", "Party Name"])
    query = st.text_input(f"Enter search term for {search_by}:")
    if query:
        query = query.lower()
        if search_by == "Product Description":
            keywords = query.split()
            results = df[df["Product Description"].apply(lambda desc: all(kw in desc.lower() for kw in keywords))]
        elif search_by == "Product ID":
            results = df[df["Product ID"].str.lower().str.contains(query)]
        elif search_by == "Party Name":
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
    chart = alt.Chart(vendor_counts).mark_bar().encode(
        x=alt.X('Party Name', sort='-y'),
        y='Count',
        tooltip=['Party Name', 'Count']
    ).properties(height=400, width=700)
    st.altair_chart(chart, use_container_width=True)
