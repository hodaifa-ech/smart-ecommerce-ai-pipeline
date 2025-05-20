import streamlit as st
import pandas as pd
import utils.ali_express as ali_express # Assuming this module exists and works
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    page_title="AliExpress Top Sellers",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
CSV_FILE_PATH = Path("./aliexpress_multi_page_firefox.csv")

# --- Data Loading and Caching ---
@st.cache_data # Cache the data loading and processing
def load_and_clean_data(file_path: Path) -> pd.DataFrame:
    """Loads, cleans, and prepares the AliExpress data."""
    if not file_path.exists():
        st.error(f"Le fichier de données '{file_path}' n'a pas été trouvé. Veuillez d'abord lancer un scraping.")
        return pd.DataFrame() # Return empty DataFrame

    try:
        df = pd.read_csv(file_path, header=None)
        df.columns = [
            "Index", "URL", "Title", "Price_MAD", "Unknown1", "Unknown2",
            "Rating", "Sales", "Image_URL", "Highlight"
        ]

        # Clean and convert
        df["Price_MAD"] = pd.to_numeric(df["Price_MAD"].astype(str).str.replace("MAD", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce")
        df["Rating"] = pd.to_numeric(df["Rating"], errors='coerce')
        
        # Improved Sales_Num extraction: handles "100+ vendu(s)", "1000 vendu(s)" etc.
        df["Sales_Num"] = df["Sales"].astype(str).str.extract(r'([\d\s\+]+)')[0] # Extract numbers, spaces, and '+'
        df["Sales_Num"] = df["Sales_Num"].str.replace(r'[^\d]', '', regex=True) # Remove non-digits (spaces, '+', 'vendu(s)')
        df["Sales_Num"] = pd.to_numeric(df["Sales_Num"], errors='coerce')

        # Ensure Image_URL is a string, handle potential NaNs if images are sometimes missing
        df["Image_URL"] = df["Image_URL"].astype(str).fillna("")
        df["Title"] = df["Title"].astype(str).fillna("Titre non disponible")

        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement ou du traitement des données : {e}")
        return pd.DataFrame()

# --- Sidebar ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/AliExpress_logo.svg/2560px-AliExpress_logo.svg.png", width=150) # Placeholder logo
    st.markdown("## ⚙️ Actions")
    if st.button("🔄 Lancer un nouveau scraping", type="primary", use_container_width=True):
        try:
            with st.spinner("Scraping des articles les plus vendus sur AliExpress..."):
                ali_express.scrape_aliexpress_top_selling() # Ensure this function creates/updates CSV_FILE_PATH
            st.success("Scraping terminé ! Rechargement des données...")
            st.cache_data.clear() # Clear cache to reload new data
            # st.experimental_rerun() # Force rerun is often good after data changes
        except Exception as e:
            st.error(f"Erreur pendant le scraping: {e}")
    
    st.markdown("---")
    st.markdown("## 📊 Filtres")

    df_original = load_and_clean_data(CSV_FILE_PATH)

    if not df_original.empty:
        keyword = st.text_input("Rechercher dans le titre :", placeholder="Ex: smartphone, robe...")
        
        min_price_val = 0.0
        max_price_val = float(df_original["Price_MAD"].max()) if not df_original["Price_MAD"].empty and pd.notna(df_original["Price_MAD"].max()) else 1000.0
        
        price_range = st.slider(
            "Fourchette de Prix (MAD)",
            min_value=min_price_val,
            max_value=max_price_val,
            value=(min_price_val, max_price_val),
            step=10.0 if max_price_val > 100 else 1.0
        )
        min_price, max_price = price_range

        min_rating = st.slider("⭐ Évaluation Minimale", 0.0, 5.0, 0.0, 0.1, help="Produits avec cette évaluation ou plus.")

        sort_options = {
            "Pertinence": "Index", # Assuming original order is relevance
            "Prix (croissant)": "Price_MAD_asc",
            "Prix (décroissant)": "Price_MAD_desc",
            "Évaluation (décroissant)": "Rating_desc",
            "Ventes (décroissant)": "Sales_Num_desc"
        }
        sort_by = st.selectbox("Trier par :", options=list(sort_options.keys()))

    else:
        st.warning("Aucune donnée à filtrer. Veuillez lancer un scraping.")
        # Provide dummy values so the rest of the app doesn't break
        keyword, min_price, max_price, min_rating, sort_by = "", 0.0, 1000.0, 0.0, "Pertinence"


# --- Main Page ---
st.title("🛍️ AliExpress - Top Produits Vendus")
st.markdown("Explorez les articles les plus populaires sur AliExpress.")

if df_original.empty:
    st.info("Les données sont en cours de chargement ou le fichier est vide. Si vous venez de lancer un scraping, les données apparaîtront bientôt.")
    st.stop() # Stop execution if no data

# Apply filters
filtered_df = df_original.copy() # Start with a copy

if keyword:
    filtered_df = filtered_df[filtered_df["Title"].str.contains(keyword, case=False, na=False)]
filtered_df = filtered_df[
    (filtered_df["Price_MAD"] >= min_price) &
    (filtered_df["Price_MAD"] <= max_price) &
    ((filtered_df["Rating"].isna()) | (filtered_df["Rating"] >= min_rating)) # Keep NaNs or if rating meets criteria
]

# Apply sorting
if sort_by == "Prix (croissant)":
    filtered_df = filtered_df.sort_values(by="Price_MAD", ascending=True)
elif sort_by == "Prix (décroissant)":
    filtered_df = filtered_df.sort_values(by="Price_MAD", ascending=False)
elif sort_by == "Évaluation (décroissant)":
    filtered_df = filtered_df.sort_values(by="Rating", ascending=False, na_position='last')
elif sort_by == "Ventes (décroissant)":
    filtered_df = filtered_df.sort_values(by="Sales_Num", ascending=False, na_position='last')
# "Pertinence" (Index) is the default, no action needed if df_original was already sorted that way


# --- Stats Section ---
if not filtered_df.empty:
    st.header("📈 Statistiques Détaillées", divider="rainbow")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribution des Prix")
        # Use a histogram for better distribution view
        # Filter out NaN prices for charting
        prices_for_chart = filtered_df["Price_MAD"].dropna()
        if not prices_for_chart.empty:
            st.bar_chart(prices_for_chart.value_counts().sort_index(), height=300)
            # Or for histogram:
            # import altair as alt
            # chart = alt.Chart(prices_for_chart.reset_index()).mark_bar().encode(
            #     alt.X("Price_MAD", bin=alt.Bin(maxbins=20), title="Fourchette de Prix (MAD)"),
            #     alt.Y('count()', title="Nombre de Produits")
            # ).properties(height=300)
            # st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("Aucune donnée de prix à afficher.")


    with col2:
        st.subheader("Distribution des Évaluations")
        ratings_for_chart = filtered_df["Rating"].dropna()
        if not ratings_for_chart.empty:
            st.bar_chart(ratings_for_chart.value_counts().sort_index(), height=300)
        else:
            st.caption("Aucune donnée d'évaluation à afficher.")
    
    if st.checkbox("Afficher les données brutes filtrées"):
        st.dataframe(filtered_df)



# --- Display Metrics ---
st.header("💡 Aperçu Rapide", divider="rainbow")
if not filtered_df.empty:
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Produits Affichés", f"{filtered_df.shape[0]}")
    avg_price = filtered_df['Price_MAD'].mean()
    col_m2.metric("Prix Moyen", f"{avg_price:.2f} MAD" if pd.notna(avg_price) else "N/A")
    avg_rating = filtered_df['Rating'].mean()
    col_m3.metric("Évaluation Moyenne", f"{avg_rating:.1f} ⭐" if pd.notna(avg_rating) else "N/A")
    total_sales = filtered_df['Sales_Num'].sum()
    col_m4.metric("Total Ventes (Estimées)", f"{int(total_sales):,} ".replace(",", " ") if pd.notna(total_sales) and total_sales > 0 else "N/A")
else:
    st.info("Aucun produit ne correspond à vos critères de filtre.")

# --- Display Product Cards ---
if not filtered_df.empty:
    st.subheader(f"✨ {filtered_df.shape[0]} Produits Correspondants")
    
    # Dynamic columns based on screen width (approximation)
    # This is a simple way, for true responsiveness, CSS and components are better.
    # Streamlit's native columns are fixed at creation.
    # We'll just use a fixed number for simplicity here, e.g., 3 or 4.
    
    num_cols = 3 # Number of columns for product display
    product_cols = st.columns(num_cols)
    
    for index, row in enumerate(filtered_df.iterrows()):
        row_data = row[1] # Get the Series from the tuple
        col_index = index % num_cols
        with product_cols[col_index]:
            with st.container(border=True):
                # Image with a fallback
                if row_data["Image_URL"] and pd.notna(row_data["Image_URL"]) and row_data["Image_URL"].startswith("http"):
                    st.image(row_data["Image_URL"])
                else:
                    st.image("https://via.placeholder.com/150?text=Image+N/A") # Placeholder

                st.markdown(f"##### [{row_data['Title']}]({row_data['URL']})")
                
                price_color = "green" if row_data['Price_MAD'] < avg_price else "orange" if pd.notna(avg_price) else "blue"
                st.markdown(f"💰 **Prix**: :{price_color}[{row_data['Price_MAD']:.2f} MAD]")

                if not pd.isna(row_data['Rating']):
                    st.markdown(f"⭐ **Évaluation**: {row_data['Rating']:.1f}/5.0")
                else:
                    st.markdown("⭐ **Évaluation**: N/A")

                if not pd.isna(row_data['Sales_Num']):
                    sales_display = f"{int(row_data['Sales_Num']):,}".replace(",", " ") # Format with space as thousands separator
                    st.markdown(f"📦 **Ventes**: {sales_display}")
                else:
                    st.markdown("📦 **Ventes**: N/A")

                if isinstance(row_data['Highlight'], str) and row_data['Highlight'].strip():
                    st.markdown(f"🔥 <span style='color: #ff4b4b;'>**{row_data['Highlight']}**</span>", unsafe_allow_html=True) # Make highlight stand out
                
                st.link_button("Voir sur AliExpress ↦", row_data['URL'], use_container_width=True)
            st.markdown("---") # Visual separator between cards in the same column


st.sidebar.markdown("---")
st.sidebar.caption(f"Source des données : `{CSV_FILE_PATH.name}`")
st.sidebar.caption(f"Dernière modification du fichier : {pd.Timestamp(CSV_FILE_PATH.stat().st_mtime, unit='s').strftime('%Y-%m-%d %H:%M:%S') if CSV_FILE_PATH.exists() else 'N/A'}")