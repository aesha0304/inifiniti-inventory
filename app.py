import streamlit as st
import pandas as pd
st.write("✅ App loaded and running...")
#@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel("Infiniti Product ID.xlsx", skiprows=2)
    df.dropna(how="all", inplace=True)
    df.fillna("", inplace=True)
    
    # Drop all 'Unnamed' columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Add Product ID
    df.insert(0, 'Product ID', ['PID' + str(i).zfill(5) for i in range(1, len(df) + 1)])

    # Drop 'ID' column completely if present
    if 'ID' in df.columns:
        df.drop(columns=['ID'], inplace=True)

    return df

df = load_data()

st.title("🔍 Infiniti Inventory Search")
st.write("Choose a field to search from and enter relevant keywords.")

# Dropdown to choose search category
search_by = st.selectbox("Search by", ["Product Description", "Product ID", "Party Name (Company)"])

# Search box
query = st.text_input(f"Enter search term for {search_by}:")

# Define search logic
if query:
    query = query.lower()
    
    if search_by == "Product Description":
        keywords = query.split()
        results = df[df["Product Description"].apply(lambda desc: all(kw in desc.lower() for kw in keywords))]

    elif search_by == "Product ID":
        results = df[df["Product ID"].str.lower().str.contains(query)]

    elif search_by == "Party Name (Company)":
        results = df[df["Party Name"].str.lower().str.contains(query)]
    
    # Display results
    if not results.empty:
        st.success(f"{len(results)} result(s) found.")
        st.dataframe(results.reset_index(drop=True))
    else:
        st.warning("No matching products found.")
else:
    st.info("Enter a search term to begin.")
