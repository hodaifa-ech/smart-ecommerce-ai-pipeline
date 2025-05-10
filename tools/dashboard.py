import streamlit as st
import pandas as pd
import numpy as np
import re
import plotly.express as px
import os # Added to check for file existence
import utils.ali_express as ali_express



# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Product Analysis Dashboard")




with st.sidebar:
    st.sidebar.markdown("## New Data ?")
    if st.button("Scrap new data"):
        with st.spinner("Scraping top selling items from AliExpress..."):
            ali_express.scrape_aliexpress_top_selling()
        st.success("Scraping completed!")
    st.sidebar.markdown("---")

# --- Helper Functions (same as before) ---
def clean_price(price_str):
    if pd.isna(price_str) or price_str == "N/A":
        return np.nan
    cleaned_price = str(price_str).replace("MAD", "").replace(",", ".").strip()
    try:
        return float(cleaned_price)
    except ValueError:
        return np.nan

def clean_rating(rating_str):
    if pd.isna(rating_str) or rating_str == "N/A":
        return np.nan
    try:
        return float(str(rating_str).replace(",", "."))
    except ValueError:
        return np.nan

def extract_sales(sales_info_str):
    if pd.isna(sales_info_str) or sales_info_str == "N/A":
        return 0
    match = re.search(r'([\d\s,]+)\s*vendus', str(sales_info_str))
    if match:
        try:
            return int(match.group(1).replace(" ", "").replace(",", ""))
        except ValueError:
            return 0
    return 0

def calculate_score(row, weights):
    score = 0
    if pd.notna(row['rating_numeric']) and weights['rating'] > 0:
        score += row['rating_numeric'] * weights['rating']
    if pd.notna(row['sales_numeric']) and weights['sales'] > 0:
        score += np.log1p(row['sales_numeric']) * weights['sales']
    if pd.notna(row['price_numeric']) and weights['price'] > 0:
        score -= (row['price_numeric']/100) * weights['price']
    if pd.notna(row['discount_percentage_numeric']) and weights['discount'] > 0:
        score += row['discount_percentage_numeric'] * weights['discount']
    return score

def clean_discount(discount_str):
    if pd.isna(discount_str) or discount_str == "N/A" or not isinstance(discount_str, str):
        return 0.0
    match = re.search(r'(\d+\.?\d*)', discount_str)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return 0.0
    return 0.0

# --- Main Application ---
st.title("🛍️ Product Analysis Dashboard")

# --- Data Loading Logic ---
DEFAULT_CSV_FILE = "aliexpress_multi_page_firefox.csv"
df = None
data_source_message = ""

# Try to load the default CSV first
if os.path.exists(DEFAULT_CSV_FILE):
    try:
        df = pd.read_csv(DEFAULT_CSV_FILE)
        data_source_message = f"✅ Using default file: `{DEFAULT_CSV_FILE}`. You can upload another CSV to override."
    except Exception as e:
        data_source_message = f"⚠️ Error loading default file `{DEFAULT_CSV_FILE}`: {e}. Please upload a file."
        df = None # Ensure df is None if default load fails

# File uploader in the sidebar
uploaded_file = st.sidebar.file_uploader("Upload your product CSV file (from Étape 1)", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) # User upload overrides default
        st.sidebar.success("File uploaded successfully!")
        data_source_message = f"✅ Using uploaded file: `{uploaded_file.name}`."
    except Exception as e:
        st.sidebar.error(f"Error reading uploaded CSV: {e}")
        st.sidebar.info(f"Reverting to default file if available, or please try uploading again.")
        # Attempt to reload default if upload fails and default was previously loaded
        if os.path.exists(DEFAULT_CSV_FILE) and (df is None or uploaded_file is not None): # Check if df was overwritten by failed upload attempt
            try:
                df = pd.read_csv(DEFAULT_CSV_FILE)
                data_source_message = f"⚠️ Upload failed. Reverted to default: `{DEFAULT_CSV_FILE}`."
            except Exception as e_default_reload:
                data_source_message = f"⚠️ Upload failed AND default file `{DEFAULT_CSV_FILE}` couldn't be reloaded: {e_default_reload}. Please upload a file."
                df = None
        elif df is None: # No default was loaded initially
             data_source_message = f"⚠️ Upload failed. Please upload a valid file."


# Display data source message prominently
if data_source_message:
    st.sidebar.markdown(data_source_message)


if df is not None:
    # --- Data Cleaning and Preprocessing (Implied in Étape 2) ---
    st.subheader("Data Cleaning & Preparation")
    with st.expander("Show Raw Data Sample", expanded=False):
        st.write(df.head())

    df_processed = df.copy()

    if 'price' in df_processed.columns:
        df_processed['price_numeric'] = df_processed['price'].apply(clean_price)
    else:
        st.warning("Column 'price' not found. Price-based analysis will be limited.")
        df_processed['price_numeric'] = np.nan

    if 'rating' in df_processed.columns:
        df_processed['rating_numeric'] = df_processed['rating'].apply(clean_rating)
    else:
        st.warning("Column 'rating' not found. Rating-based analysis will be limited.")
        df_processed['rating_numeric'] = np.nan

    if 'sales_info' in df_processed.columns:
        df_processed['sales_numeric'] = df_processed['sales_info'].apply(extract_sales)
    else:
        st.warning("Column 'sales_info' not found. Sales-based analysis will be limited.")
        df_processed['sales_numeric'] = 0
        
    if 'discount_percentage' in df_processed.columns:
        df_processed['discount_percentage_numeric'] = df_processed['discount_percentage'].apply(clean_discount)
    else:
        if 'original_price' in df_processed.columns and 'price_numeric' in df_processed.columns:
            df_processed['original_price_numeric'] = df_processed['original_price'].apply(clean_price)
            df_processed['discount_percentage_numeric'] = np.where(
                (df_processed['original_price_numeric'] > df_processed['price_numeric']) & (df_processed['original_price_numeric'] > 0),
                ((df_processed['original_price_numeric'] - df_processed['price_numeric']) / df_processed['original_price_numeric']) * 100,
                0
            )
            df_processed['discount_percentage_numeric'] = df_processed['discount_percentage_numeric'].fillna(0)
        else:
            st.warning("Column 'discount_percentage' not found, and original_price/price not available for calculation.")
            df_processed['discount_percentage_numeric'] = 0.0

    with st.expander("Show Processed Data Sample & Info", expanded=False):
        st.write(df_processed[['name', 'price_numeric', 'rating_numeric', 'sales_numeric', 'discount_percentage_numeric']].head())
        st.write(df_processed[['price_numeric', 'rating_numeric', 'sales_numeric', 'discount_percentage_numeric']].describe())

    # --- Étape 2: Analyse et sélection des Top-K produits ---
    st.sidebar.header("⚙️ Product Selection Controls (Étape 2)")

    st.sidebar.subheader("Scoring Weights")
    w_rating = st.sidebar.slider("Rating Weight", 0.0, 5.0, 2.0, 0.1)
    w_sales = st.sidebar.slider("Sales Weight (log scale)", 0.0, 5.0, 1.5, 0.1)
    w_price = st.sidebar.slider("Price Penalty Weight (per 100 MAD)", 0.0, 2.0, 0.5, 0.1)
    w_discount = st.sidebar.slider("Discount Weight", 0.0, 2.0, 1.0, 0.1)

    score_weights = {'rating': w_rating, 'sales': w_sales, 'price': w_price, 'discount': w_discount}
    df_processed['score'] = df_processed.apply(lambda row: calculate_score(row, score_weights), axis=1)

    num_top_k = st.sidebar.slider("Number of Top-K products to display", 1, 100, 10)

    st.sidebar.subheader("Filters")
    min_price_val = float(df_processed['price_numeric'].min()) if df_processed['price_numeric'].notna().any() else 0.0
    max_price_val = float(df_processed['price_numeric'].max()) if df_processed['price_numeric'].notna().any() else 1000.0
    if min_price_val > max_price_val: max_price_val = min_price_val # handle single value case
    price_range = st.sidebar.slider(
        "Price Range (MAD)",
        min_value=min_price_val,
        max_value=max_price_val,
        value=(min_price_val, max_price_val)
    )

    min_rating_val = float(df_processed['rating_numeric'].min(skipna=True) if df_processed['rating_numeric'].notna().any() else 0.0)
    max_rating_val = float(df_processed['rating_numeric'].max(skipna=True) if df_processed['rating_numeric'].notna().any() else 5.0)
    if min_rating_val > max_rating_val : max_rating_val = min_rating_val

    if min_rating_val < max_rating_val :
        rating_threshold = st.sidebar.slider(
            "Minimum Rating",
            min_value=min_rating_val,
            max_value=max_rating_val,
            value=min_rating_val,
            step=0.1
        )
    else:
        st.sidebar.text(f"Rating data range limited. Min Rating: {min_rating_val:.1f}")
        rating_threshold = min_rating_val

    filtered_df = df_processed[
        (df_processed['price_numeric'].fillna(price_range[0]) >= price_range[0]) &
        (df_processed['price_numeric'].fillna(price_range[1]) <= price_range[1]) &
        (df_processed['rating_numeric'].fillna(0) >= rating_threshold)
    ]

    # --- Étape 4: Dashboard de Business Intelligence ---
    st.header("📊 Business Intelligence Dashboard (Étape 4)")

    st.subheader("Key Performance Indicators (KPIs)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products (after filter)", f"{filtered_df.shape[0]}")
    if not filtered_df.empty:
        avg_price_filtered = filtered_df['price_numeric'].mean()
        avg_rating_filtered = filtered_df['rating_numeric'].mean()
        total_sales_filtered = filtered_df['sales_numeric'].sum()
        col2.metric("Avg. Price (filtered)", f"MAD {avg_price_filtered:.2f}" if pd.notna(avg_price_filtered) else "N/A")
        col3.metric("Avg. Rating (filtered)", f"{avg_rating_filtered:.2f} ⭐" if pd.notna(avg_rating_filtered) else "N/A")
        col4.metric("Total Estimated Sales (filtered)", f"{total_sales_filtered:,.0f}")
    else:
        col2.metric("Avg. Price (filtered)", "N/A")
        col3.metric("Avg. Rating (filtered)", "N/A")
        col4.metric("Total Estimated Sales (filtered)", "N/A")

    st.subheader(f"🏆 Top {num_top_k} Products (Based on Calculated Score & Filters)")
    if not filtered_df.empty:
        top_k_products = filtered_df.sort_values(by='score', ascending=False).head(num_top_k)
        
        if not top_k_products.empty:
            for index, row in top_k_products.iterrows():
                st.markdown("---")
                cols_display = st.columns([1, 3])
                with cols_display[0]:
                    if 'image_url' in row and pd.notna(row['image_url']):
                        st.image(row['image_url'], width=150, caption=f"Image for {row.get('name', 'N/A')[:30]}...")
                    else:
                        st.caption("No Image")
                
                with cols_display[1]:
                    st.markdown(f"**{row.get('name', 'N/A')}**")
                    price_display = f"MAD {row['price_numeric']:.2f}" if pd.notna(row['price_numeric']) else "N/A"
                    original_price_display = ""
                    if 'original_price_numeric' in row and pd.notna(row['original_price_numeric']) and row['original_price_numeric'] > row.get('price_numeric',0) :
                        original_price_display = f"~~MAD {row['original_price_numeric']:.2f}~~"
                    discount_display = ""
                    if 'discount_percentage_numeric' in row and pd.notna(row['discount_percentage_numeric']) and row['discount_percentage_numeric'] > 0:
                        discount_display = f" ({row['discount_percentage_numeric']:.0f}% off)"
                    st.markdown(f"**Price:** {price_display} {original_price_display} {discount_display}")
                    rating_display = f"{row['rating_numeric']:.1f} ⭐" if pd.notna(row['rating_numeric']) else "N/A"
                    st.markdown(f"**Rating:** {rating_display}")
                    sales_display = f"{row['sales_numeric']:,}" if pd.notna(row['sales_numeric']) else "N/A"
                    st.markdown(f"**Sales:** ~{sales_display} units")
                    st.markdown(f"**Calculated Score:** {row['score']:.2f}")
                    if 'url' in row and pd.notna(row['url']):
                        st.markdown(f"[View Product on AliExpress]({row['url']})")
                    if 'additional_badges' in row and pd.notna(row['additional_badges']):
                        st.caption(f"Badges: {row['additional_badges']}")
            st.markdown("---")
        else:
            st.warning("No products match the current filter criteria to display in Top-K.")
    else:
        st.warning("No products after filtering. Adjust filters to see results.")

    st.subheader("Data Visualizations (on Filtered Data)")
    if not filtered_df.empty:
        viz_cols = st.columns(2)
        with viz_cols[0]:
            if 'price_numeric' in filtered_df.columns and filtered_df['price_numeric'].notna().any():
                fig_price = px.histogram(filtered_df.dropna(subset=['price_numeric']), x="price_numeric", nbins=30, title="Price Distribution")
                st.plotly_chart(fig_price, use_container_width=True)
            else:
                st.caption("Not enough price data to plot distribution.")

            if 'sales_numeric' in filtered_df.columns and filtered_df['sales_numeric'].notna().any() and filtered_df['sales_numeric'].sum() > 0 :
                top_sales_viz = filtered_df.nlargest(10, 'sales_numeric')
                if not top_sales_viz.empty:
                    fig_sales = px.bar(top_sales_viz, y="name", x="sales_numeric", orientation='h', title="Top 10 Products by Sales Volume", labels={'name':'Product', 'sales_numeric':'Sales Volume'})
                    fig_sales.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_sales, use_container_width=True)
                else:
                    st.caption("Not enough sales data for top products chart.")
            else:
                st.caption("Not enough sales data to plot top products by sales.")

        with viz_cols[1]:
            if 'rating_numeric' in filtered_df.columns and filtered_df['rating_numeric'].notna().any():
                fig_rating = px.histogram(filtered_df.dropna(subset=['rating_numeric']), x="rating_numeric", nbins=10, title="Rating Distribution (0-5 stars)")
                fig_rating.update_xaxes(range=[0,5])
                st.plotly_chart(fig_rating, use_container_width=True)
            else:
                st.caption("Not enough rating data to plot distribution.")

            if ('price_numeric' in filtered_df.columns and 'rating_numeric' in filtered_df.columns and
               filtered_df['price_numeric'].notna().any() and filtered_df['rating_numeric'].notna().any()):
                fig_scatter = px.scatter(filtered_df.dropna(subset=['price_numeric', 'rating_numeric']),
                                         x="price_numeric", y="rating_numeric",
                                         title="Price vs. Rating",
                                         hover_data=['name', 'sales_numeric'],
                                         color="sales_numeric",
                                         size="sales_numeric",
                                         labels={'price_numeric':'Price (MAD)', 'rating_numeric':'Rating', 'sales_numeric':'Sales Volume'})
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.caption("Not enough price/rating data for scatter plot.")
    else:
        st.info("No data to visualize. Please adjust filters or upload a valid dataset.")

    st.sidebar.header("💡 LLM Enrichment (Étape 5 - Future)")
    st.sidebar.info("This section could integrate LLMs for generating product summaries or recommendations.")

else:
    st.info("👈 No data loaded. Please upload a CSV file using the sidebar, or ensure `aliexpress_multi_page_firefox.csv` exists in the script's directory.")

st.markdown("---")
st.caption("Dashboard built with Streamlit.")