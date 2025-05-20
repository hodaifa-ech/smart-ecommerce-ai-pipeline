import streamlit as st
import pandas as pd
import numpy as np
import re
import plotly.express as px
import os # Added to check for file existence
import utils.ali_express as ali_express



# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Tableau de Bord d'Analyse de Produits") # MODIFIED




with st.sidebar:
    st.sidebar.markdown("## Nouvelles Données ?") # MODIFIED
    if st.button("Lancer un nouveau scraping"): # MODIFIED
        with st.spinner("Scraping des articles les plus vendus sur AliExpress..."): # MODIFIED
            ali_express.scrape_aliexpress_top_selling()
        st.success("Scraping terminé !") # MODIFIED
    st.sidebar.markdown("---")

# --- Helper Functions (same as before) ---
def clean_price(price_str):
    if pd.isna(price_str) or price_str == "N/A": # N/A can be kept as is for data, or use specific NaN markers
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
    match = re.search(r'([\d\s,]+)\s*vendus', str(sales_info_str)) # "vendus" is already French
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
st.title("🛍️ Tableau de Bord d'Analyse de Produits") # MODIFIED

# --- Data Loading Logic ---
DEFAULT_CSV_FILE = "aliexpress_multi_page_firefox.csv"
df = None
data_source_message = ""

# Try to load the default CSV first
if os.path.exists(DEFAULT_CSV_FILE):
    try:
        df = pd.read_csv(DEFAULT_CSV_FILE)
        data_source_message = f"✅ Fichier par défaut utilisé : `{DEFAULT_CSV_FILE}`. Vous pouvez téléverser un autre CSV pour le remplacer." # MODIFIED
    except Exception as e:
        data_source_message = f"⚠️ Erreur lors du chargement du fichier par défaut `{DEFAULT_CSV_FILE}` : {e}. Veuillez téléverser un fichier." # MODIFIED
        df = None # Ensure df is None if default load fails

# File uploader in the sidebar
uploaded_file = st.sidebar.file_uploader("Téléversez votre fichier CSV de produits (de l'Étape 1)", type=["csv"]) # MODIFIED

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) # User upload overrides default
        st.sidebar.success("Fichier téléversé avec succès !") # MODIFIED
        data_source_message = f"✅ Fichier téléversé utilisé : `{uploaded_file.name}`." # MODIFIED
    except Exception as e:
        st.sidebar.error(f"Erreur lors de la lecture du CSV téléversé : {e}") # MODIFIED
        st.sidebar.info(f"Retour au fichier par défaut si disponible, ou veuillez réessayer de téléverser.") # MODIFIED
        # Attempt to reload default if upload fails and default was previously loaded
        if os.path.exists(DEFAULT_CSV_FILE) and (df is None or uploaded_file is not None): # Check if df was overwritten by failed upload attempt
            try:
                df = pd.read_csv(DEFAULT_CSV_FILE)
                data_source_message = f"⚠️ Échec du téléversement. Retour au fichier par défaut : `{DEFAULT_CSV_FILE}`." # MODIFIED
            except Exception as e_default_reload:
                data_source_message = f"⚠️ Échec du téléversement ET le fichier par défaut `{DEFAULT_CSV_FILE}` n'a pas pu être rechargé : {e_default_reload}. Veuillez téléverser un fichier." # MODIFIED
                df = None
        elif df is None: # No default was loaded initially
             data_source_message = f"⚠️ Échec du téléversement. Veuillez téléverser un fichier valide." # MODIFIED


# Display data source message prominently
if data_source_message:
    st.sidebar.markdown(data_source_message)


if df is not None:
    # --- Data Cleaning and Preprocessing (Implied in Étape 2) ---
    st.subheader("Nettoyage & Préparation des Données") # MODIFIED
    with st.expander("Afficher un Échantillon des Données Brutes", expanded=False): # MODIFIED
        st.write(df.head())

    df_processed = df.copy()

    if 'price' in df_processed.columns:
        df_processed['price_numeric'] = df_processed['price'].apply(clean_price)
    else:
        st.warning("Colonne 'price' introuvable. L'analyse basée sur les prix sera limitée.") # MODIFIED
        df_processed['price_numeric'] = np.nan

    if 'rating' in df_processed.columns:
        df_processed['rating_numeric'] = df_processed['rating'].apply(clean_rating)
    else:
        st.warning("Colonne 'rating' introuvable. L'analyse basée sur les évaluations sera limitée.") # MODIFIED
        df_processed['rating_numeric'] = np.nan

    if 'sales_info' in df_processed.columns:
        df_processed['sales_numeric'] = df_processed['sales_info'].apply(extract_sales)
    else:
        st.warning("Colonne 'sales_info' introuvable. L'analyse basée sur les ventes sera limitée.") # MODIFIED
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
            st.warning("Colonne 'discount_percentage' introuvable, et original_price/price non disponibles pour le calcul.") # MODIFIED
            df_processed['discount_percentage_numeric'] = 0.0

    with st.expander("Afficher un Échantillon des Données Traitées & Infos", expanded=False): # MODIFIED
        st.write(df_processed[['name', 'price_numeric', 'rating_numeric', 'sales_numeric', 'discount_percentage_numeric']].head())
        st.write(df_processed[['price_numeric', 'rating_numeric', 'sales_numeric', 'discount_percentage_numeric']].describe())

    # --- Étape 2: Analyse et sélection des Top-K produits ---
    st.sidebar.header("⚙️ Contrôles de Sélection de Produits (Étape 2)") # MODIFIED

    st.sidebar.subheader("Pondérations du Score") # MODIFIED
    w_rating = st.sidebar.slider("Poids de l'Évaluation", 0.0, 5.0, 2.0, 0.1) # MODIFIED
    w_sales = st.sidebar.slider("Poids des Ventes (échelle log)", 0.0, 5.0, 1.5, 0.1) # MODIFIED
    w_price = st.sidebar.slider("Poids de Pénalité du Prix (par 100 MAD)", 0.0, 2.0, 0.5, 0.1) # MODIFIED
    w_discount = st.sidebar.slider("Poids de la Réduction", 0.0, 2.0, 1.0, 0.1) # MODIFIED

    score_weights = {'rating': w_rating, 'sales': w_sales, 'price': w_price, 'discount': w_discount}
    df_processed['score'] = df_processed.apply(lambda row: calculate_score(row, score_weights), axis=1)

    num_top_k = st.sidebar.slider("Nombre de Top-K produits à afficher", 1, 100, 10) # MODIFIED

    st.sidebar.subheader("Filtres") # MODIFIED
    min_price_val = float(df_processed['price_numeric'].min()) if df_processed['price_numeric'].notna().any() else 0.0
    max_price_val = float(df_processed['price_numeric'].max()) if df_processed['price_numeric'].notna().any() else 1000.0
    if min_price_val > max_price_val: max_price_val = min_price_val # handle single value case
    price_range = st.sidebar.slider(
        "Fourchette de Prix (MAD)", # MODIFIED
        min_value=min_price_val,
        max_value=max_price_val,
        value=(min_price_val, max_price_val)
    )

    min_rating_val = float(df_processed['rating_numeric'].min(skipna=True) if df_processed['rating_numeric'].notna().any() else 0.0)
    max_rating_val = float(df_processed['rating_numeric'].max(skipna=True) if df_processed['rating_numeric'].notna().any() else 5.0)
    if min_rating_val > max_rating_val : max_rating_val = min_rating_val

    if min_rating_val < max_rating_val :
        rating_threshold = st.sidebar.slider(
            "Évaluation Minimale", # MODIFIED
            min_value=min_rating_val,
            max_value=max_rating_val,
            value=min_rating_val,
            step=0.1
        )
    else:
        st.sidebar.text(f"Plage de données d'évaluation limitée. Éval. Min : {min_rating_val:.1f}") # MODIFIED
        rating_threshold = min_rating_val

    filtered_df = df_processed[
        (df_processed['price_numeric'].fillna(price_range[0]) >= price_range[0]) &
        (df_processed['price_numeric'].fillna(price_range[1]) <= price_range[1]) &
        (df_processed['rating_numeric'].fillna(0) >= rating_threshold)
    ]

    # --- Étape 4: Dashboard de Business Intelligence ---
    st.header("📊 Tableau de Bord Business Intelligence (Étape 4)") # MODIFIED

    st.subheader("Indicateurs Clés de Performance (KPIs)") # MODIFIED
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Produits (après filtre)", f"{filtered_df.shape[0]}") # MODIFIED
    if not filtered_df.empty:
        avg_price_filtered = filtered_df['price_numeric'].mean()
        avg_rating_filtered = filtered_df['rating_numeric'].mean()
        total_sales_filtered = filtered_df['sales_numeric'].sum()
        col2.metric("Prix Moyen (filtré)", f"MAD {avg_price_filtered:.2f}" if pd.notna(avg_price_filtered) else "N/D") # MODIFIED ("N/D")
        col3.metric("Éval. Moyenne (filtrée)", f"{avg_rating_filtered:.2f} ⭐" if pd.notna(avg_rating_filtered) else "N/D") # MODIFIED ("N/D")
        col4.metric("Ventes Estimées Totales (filtrées)", f"{total_sales_filtered:,.0f}") # MODIFIED
    else:
        col2.metric("Prix Moyen (filtré)", "N/D") # MODIFIED ("N/D")
        col3.metric("Éval. Moyenne (filtrée)", "N/D") # MODIFIED ("N/D")
        col4.metric("Ventes Estimées Totales (filtrées)", "N/D") # MODIFIED ("N/D")


    st.subheader("Visualisations des Données (sur Données Filtrées)") # MODIFIED
    if not filtered_df.empty:
        viz_cols = st.columns(2)
        with viz_cols[0]:
            if 'price_numeric' in filtered_df.columns and filtered_df['price_numeric'].notna().any():
                fig_price = px.histogram(filtered_df.dropna(subset=['price_numeric']), x="price_numeric", nbins=30, title="Distribution des Prix") # MODIFIED
                st.plotly_chart(fig_price, use_container_width=True)
            else:
                st.caption("Pas assez de données de prix pour tracer la distribution.") # MODIFIED

            if 'sales_numeric' in filtered_df.columns and filtered_df['sales_numeric'].notna().any() and filtered_df['sales_numeric'].sum() > 0 :
                top_sales_viz = filtered_df.nlargest(10, 'sales_numeric')
                if not top_sales_viz.empty:
                    fig_sales = px.bar(top_sales_viz, y="name", x="sales_numeric", orientation='h', 
                                       title="Top 10 Produits par Volume de Ventes", # MODIFIED
                                       labels={'name':'Produit', 'sales_numeric':'Volume des Ventes'}) # MODIFIED
                    fig_sales.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_sales, use_container_width=True)
                else:
                    st.caption("Pas assez de données de ventes pour le graphique des meilleurs produits.") # MODIFIED
            else:
                st.caption("Pas assez de données de ventes pour tracer les meilleurs produits par ventes.") # MODIFIED

        with viz_cols[1]:
            if 'rating_numeric' in filtered_df.columns and filtered_df['rating_numeric'].notna().any():
                fig_rating = px.histogram(filtered_df.dropna(subset=['rating_numeric']), x="rating_numeric", nbins=10, title="Distribution des Évaluations (0-5 étoiles)") # MODIFIED
                fig_rating.update_xaxes(range=[0,5])
                st.plotly_chart(fig_rating, use_container_width=True)
            else:
                st.caption("Pas assez de données d'évaluation pour tracer la distribution.") # MODIFIED

            if ('price_numeric' in filtered_df.columns and 'rating_numeric' in filtered_df.columns and
               filtered_df['price_numeric'].notna().any() and filtered_df['rating_numeric'].notna().any()):
                fig_scatter = px.scatter(filtered_df.dropna(subset=['price_numeric', 'rating_numeric']),
                                         x="price_numeric", y="rating_numeric",
                                         title="Prix vs. Évaluation", # MODIFIED
                                         hover_data=['name', 'sales_numeric'],
                                         color="sales_numeric",
                                         size="sales_numeric",
                                         labels={'price_numeric':'Prix (MAD)', 'rating_numeric':'Évaluation', 'sales_numeric':'Volume des Ventes'}) # MODIFIED
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.caption("Pas assez de données de prix/évaluation pour le nuage de points.") # MODIFIED
    else:
        st.info("Aucune donnée à visualiser. Veuillez ajuster les filtres ou téléverser un jeu de données valide.") # MODIFIED

    st.sidebar.header("💡 Enrichissement LLM (Étape 5 - Futur)") # MODIFIED
    st.sidebar.info("Cette section pourrait intégrer des LLMs pour générer des résumés de produits ou des recommandations.") # MODIFIED

    
    st.subheader(f"🏆 Top {num_top_k} Produits (Basé sur le Score Calculé & Filtres)") # MODIFIED
    if not filtered_df.empty:
        top_k_products = filtered_df.sort_values(by='score', ascending=False).head(num_top_k)
        
        if not top_k_products.empty:
            for index, row in top_k_products.iterrows():
                st.markdown("---")
                cols_display = st.columns([1, 3])
                with cols_display[0]:
                    if 'image_url' in row and pd.notna(row['image_url']):
                        st.image(row['image_url'], width=150, caption=f"Image pour {row.get('name', 'N/D')[:30]}...") # MODIFIED ("Image pour", "N/D")
                    else:
                        st.caption("Pas d'image") # MODIFIED
                
                with cols_display[1]:
                    st.markdown(f"**{row.get('name', 'N/D')}**") # MODIFIED ("N/D")
                    price_display = f"MAD {row['price_numeric']:.2f}" if pd.notna(row['price_numeric']) else "N/D" # MODIFIED ("N/D")
                    original_price_display = ""
                    if 'original_price_numeric' in row and pd.notna(row['original_price_numeric']) and row['original_price_numeric'] > row.get('price_numeric',0) :
                        original_price_display = f"~~MAD {row['original_price_numeric']:.2f}~~"
                    discount_display = ""
                    if 'discount_percentage_numeric' in row and pd.notna(row['discount_percentage_numeric']) and row['discount_percentage_numeric'] > 0:
                        discount_display = f" ({row['discount_percentage_numeric']:.0f}% de réduction)" # MODIFIED
                    st.markdown(f"**Prix :** {price_display} {original_price_display} {discount_display}") # MODIFIED
                    rating_display = f"{row['rating_numeric']:.1f} ⭐" if pd.notna(row['rating_numeric']) else "N/D" # MODIFIED ("N/D")
                    st.markdown(f"**Évaluation :** {rating_display}") # MODIFIED
                    sales_display = f"{row['sales_numeric']:,}" if pd.notna(row['sales_numeric']) else "N/D" # MODIFIED ("N/D")
                    st.markdown(f"**Ventes :** ~{sales_display} unités") # MODIFIED
                    st.markdown(f"**Score Calculé :** {row['score']:.2f}") # MODIFIED
                    if 'url' in row and pd.notna(row['url']):
                        st.markdown(f"[Voir le Produit sur AliExpress]({row['url']})") # MODIFIED
                    if 'additional_badges' in row and pd.notna(row['additional_badges']):
                        st.caption(f"Badges : {row['additional_badges']}") # MODIFIED
            st.markdown("---")
        else:
            st.warning("Aucun produit ne correspond aux critères de filtre actuels pour l'affichage dans le Top-K.") # MODIFIED
    else:
        st.warning("Aucun produit après filtrage. Ajustez les filtres pour voir les résultats.") # MODIFIED

    
else:
    st.info("👈 Aucune donnée chargée. Veuillez téléverser un fichier CSV via la barre latérale, ou assurez-vous que `aliexpress_multi_page_firefox.csv` existe dans le répertoire du script.") # MODIFIED

