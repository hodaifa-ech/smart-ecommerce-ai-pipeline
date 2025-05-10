import streamlit as st
import pandas as pd
import utils.ali_express as ali_express

with st.sidebar:
    st.sidebar.markdown("## New Data ?")
    if st.button("Scrap new data"):
        with st.spinner("Scraping top selling items from AliExpress..."):
            ali_express.scrape_aliexpress_top_selling()
        st.success("Scraping completed!")
    st.sidebar.markdown("---")


# Load CSV
df = pd.read_csv("./aliexpress_multi_page_firefox.csv", header=None)

# Rename columns for clarity
df.columns = [
    "Index", "URL", "Title", "Price_MAD", "Unknown1", "Unknown2",
    "Rating", "Sales", "Image_URL", "Highlight"
]

# Clean and convert
df["Price_MAD"] = pd.to_numeric(df["Price_MAD"].str.replace("MAD", "").str.replace(",", ".").str.strip(), errors="coerce")
df["Rating"] = pd.to_numeric(df["Rating"], errors='coerce')
df["Sales_Num"] = df["Sales"].str.extract(r'([\d\s]+)').replace(" ", "", regex=True).astype(float)

# Sidebar filters
st.sidebar.title("📊 Filters")
keyword = st.sidebar.text_input("Search in title:")
min_price = st.sidebar.number_input("Min Price (MAD)", min_value=0.0, value=0.0)
max_price = st.sidebar.number_input("Max Price (MAD)", min_value=0.0, value=1000.0)
min_rating = st.sidebar.slider("Minimum Rating", 0.0, 5.0, 0.0, 0.1)

# Apply filters
filtered = df[
    df["Title"].str.contains(keyword, case=False, na=False) &
    (df["Price_MAD"] >= min_price) &
    (df["Price_MAD"] <= max_price) &
    ((df["Rating"].isna()) | (df["Rating"] >= min_rating))
]

# Dashboard title
st.title("🛒 AliExpress Top Selling Products ")

# Show product cards
for _, row in filtered.iterrows():
    with st.container():
        cols = st.columns([1, 2])
        with cols[0]:
            st.image(row["Image_URL"], width=150)
        with cols[1]:
            st.markdown(f"### [{row['Title']}]({row['URL']})")
            st.markdown(f"💰 **Price**: {row['Price_MAD']} MAD")
            if not pd.isna(row['Rating']):
                st.markdown(f"⭐ **Rating**: {row['Rating']}")
            if not pd.isna(row['Sales_Num']):
                st.markdown(f"📦 **Sales**: {int(row['Sales_Num'])}")
            if isinstance(row['Highlight'], str):
                st.markdown(f"🔖 {row['Highlight']}")

# Stats section
st.header("📈 Statistics")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Price Distribution")
    st.bar_chart(filtered["Price_MAD"])

with col2:
    st.subheader("Rating Distribution")
    st.bar_chart(filtered["Rating"].dropna())

st.caption("Source: ./aliexpress_multi_page_firefox.csv")
