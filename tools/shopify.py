import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import subprocess # <-- Import subprocess
import sys        # <-- Import sys to get python executable

# --- Page Configuration ---
st.set_page_config(
    page_title="Tableau de Bord d'Analyse des Produits Shopify", # MODIFIED
    page_icon="📊",
    layout="wide" # Use wide layout for more space
)

# --- Constants ---
CSV_FILENAME = "utils/products_data.csv" # Assumes CSV is in the root directory relative to where streamlit is run
# More robust path handling might be needed depending on execution context
# For example, if running from the root project dir:
# CSV_FILENAME = os.path.join(os.path.dirname(__file__), "..", "products_data.csv")
# Or ensure the fetch script always saves to the root. Let's assume root for now.


# --- Helper Functions ---
@st.cache_data # Cache the data loading to improve performance
def load_data(filename):
    """Loads data from the CSV file."""
    absolute_csv_path = os.path.abspath(filename) # Get absolute path for clarity
    if not os.path.exists(absolute_csv_path):
        st.error(f"Erreur : Fichier de données non trouvé à l'emplacement attendu : {absolute_csv_path}. Veuillez d'abord exécuter le scraper.") # MODIFIED
        return None
    try:
        df = pd.read_csv(absolute_csv_path) # Load using absolute path
        # --- Basic Data Cleaning & Type Conversion ---
        # Convert price columns to numeric, coercing errors to NaN
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['compare_at_price'] = pd.to_numeric(df['compare_at_price'], errors='coerce')

        # Convert relevant columns to datetime objects
        for col in ['created_at', 'updated_at', 'published_at', 'variant_created_at', 'variant_updated_at']:
             if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce') # Coerce errors if format is inconsistent

        # Ensure 'available' is boolean (handle potential string representations)
        if 'available' in df.columns:
             df['available'] = df['available'].apply(lambda x: True if str(x).lower() == 'true' else (False if str(x).lower() == 'false' else None))
             df['available'] = df['available'].astype('boolean') # Use pandas nullable boolean type

        # Handle potential missing values in key categorical columns
        for col in ['vendor', 'product_type', 'store_domain']:
            if col in df.columns:
                df[col].fillna('Inconnu', inplace=True) # MODIFIED (Unknown -> Inconnu)

        return df
    except pd.errors.EmptyDataError:
        st.error(f"Erreur : {absolute_csv_path} est vide. Veuillez vous assurer que le script de récupération s'est exécuté avec succès et a généré des données.") # MODIFIED
        return None
    except Exception as e:
        st.error(f"Une erreur s'est produite lors du chargement ou du traitement du CSV ({absolute_csv_path}) : {e}") # MODIFIED
        return None

# --- Function to run the scraper script ---
def run_scraper(script_path):
    """Runs the external Python script using subprocess."""
    absolute_script_path = os.path.abspath(script_path)
    script_dir = os.path.dirname(absolute_script_path) # Get directory of the script

    st.info(f"Tentative d'exécution du scraper : {absolute_script_path}") # MODIFIED
    if not os.path.exists(absolute_script_path):
         st.error(f"Script du scraper non trouvé à : {absolute_script_path}") # MODIFIED
         return False

    try:
        # Run the script using the same Python interpreter that runs Streamlit
        # Run it with the script's directory as the current working directory
        # This helps if the script uses relative paths for its own operations (like logging)
        process = subprocess.run(
            [sys.executable, absolute_script_path],
            capture_output=True,  # Capture stdout and stderr
            text=True,            # Decode output as text
            check=False,          # Don't raise exception on non-zero exit, check manually
            cwd=script_dir        # Set working directory
        )
        st.info("Exécution du script du scraper terminée.") # MODIFIED

        # Display output/errors from the script in expanders for debugging
        with st.expander("Afficher la Sortie du Scraper (stdout)"): # MODIFIED
            st.text(process.stdout if process.stdout else "Pas de sortie standard.") # MODIFIED
        if process.stderr:
             with st.expander("Afficher les Erreurs du Scraper (stderr)", expanded=True): # MODIFIED
                st.text(process.stderr)

        if process.returncode == 0:
            st.success("Récupération des données terminée avec succès !") # MODIFIED
            return True
        else:
            st.error(f"Le script de récupération des données a échoué avec le code de sortie {process.returncode}. Vérifiez les erreurs ci-dessus.") # MODIFIED
            return False
    except Exception as e:
        st.error(f"Une erreur s'est produite lors de la tentative d'exécution du processus du scraper : {e}") # MODIFIED
        return False

# --- Main Application ---
st.title("📊 Tableau de Bord des Données Produits Shopify") # MODIFIED
st.markdown("Analysez les données produits récupérées de diverses boutiques Shopify via leurs points de terminaison `/products.json`.") # MODIFIED


# --- Sidebar ---
st.sidebar.header("Actions") # Actions is fine

# --- Button to trigger scraping ---
# Construct the path to the scraper script relative to *this* dashboard script
# dashboard.py is in tools/, fetch_shopify_product_data.py is in utils/
# So we need to go up one level from tools/ and then down into utils/
dashboard_dir = os.path.dirname(__file__)
scraper_script_path = os.path.join(dashboard_dir, "..", "utils", "fetch_shopify_product_data.py")

if st.sidebar.button("🔄 Récupérer de Nouvelles Données Shopify"): # MODIFIED
    # Use a spinner to indicate activity
    with st.spinner(f"Exécution du scraper de données Shopify... Veuillez patienter. Cela peut prendre un certain temps."): # MODIFIED
        success = run_scraper(scraper_script_path)
        if success:
            # IMPORTANT: Clear the cache so load_data runs again
            st.cache_data.clear()
            st.success("Cache vidé. Redémarrage de l'application pour charger les nouvelles données...") # MODIFIED
            # Rerun the app immediately to reflect the newly scraped data
            st.experimental_rerun()
        else:
            st.warning("Le processus de récupération a échoué ou a rencontré des erreurs. Les données pourraient ne pas être à jour.") # MODIFIED

st.sidebar.markdown("---") # Separator before filters
st.sidebar.header("Filtres") # MODIFIED

# --- Load Data ---
# Load data *after* the button logic, so rerun works correctly
# Use the CSV_FILENAME constant (ensure it points correctly relative to execution dir or use absolute)
# Let's try resolving the path relative to the dashboard script's parent directory (project root)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
absolute_csv_path = os.path.join(project_root, CSV_FILENAME)
data = load_data(absolute_csv_path)


# --- Dashboard Content (Only if data loaded successfully) ---
if data is not None and not data.empty:

    # Filter data based on domain selection (using the already loaded 'data' DataFrame)
    all_domains = ['Tous'] + sorted(data['store_domain'].unique().tolist()) # MODIFIED
    selected_domain = st.sidebar.selectbox("Sélectionner le Domaine de la Boutique", all_domains) # MODIFIED

    if selected_domain != 'Tous': # MODIFIED
        filtered_data = data[data['store_domain'] == selected_domain].copy()
    else:
        filtered_data = data.copy()

    # --- Dynamic Filters based on current selection ---
    if not filtered_data.empty:
        # Filter by Vendor
        all_vendors = ['Tous'] + sorted(filtered_data['vendor'].unique().tolist()) # MODIFIED
        selected_vendor = st.sidebar.selectbox("Sélectionner le Fournisseur", all_vendors) # MODIFIED
        if selected_vendor != 'Tous': # MODIFIED
            filtered_data = filtered_data[filtered_data['vendor'] == selected_vendor].copy()

        # Filter by Product Type
        all_product_types = ['Tous'] + sorted(filtered_data['product_type'].unique().tolist()) # MODIFIED
        selected_product_type = st.sidebar.selectbox("Sélectionner le Type de Produit", all_product_types) # MODIFIED
        if selected_product_type != 'Tous': # MODIFIED
            filtered_data = filtered_data[filtered_data['product_type'] == selected_product_type].copy()

        # Filter by Price Range
        # Ensure price column exists and has valid numbers before calculating min/max
        if 'price' in filtered_data.columns and not filtered_data['price'].isnull().all():
            min_price_val = float(filtered_data['price'].min())
            max_price_val = float(filtered_data['price'].max())
            # Handle case where min and max are the same for the slider
            if min_price_val == max_price_val:
                max_price_val += 1.0
            # Set default range for slider
            default_price_range = (min_price_val, max_price_val)
        else:
             # Default values if price data is missing or invalid
             min_price_val = 0.0
             max_price_val = 1.0
             default_price_range = (0.0, 1.0)
             st.sidebar.warning("Données de prix manquantes ou invalides pour le sélecteur de plage.") # MODIFIED


        price_range = st.sidebar.slider(
            "Sélectionner la Fourchette de Prix ($)", # MODIFIED
            min_value=min_price_val,
            max_value=max_price_val,
            value=default_price_range, # Use calculated default range
            step=0.01
        )
        # Apply price filter only if price column exists
        if 'price' in filtered_data.columns:
            filtered_data = filtered_data[
                (filtered_data['price'] >= price_range[0]) &
                (filtered_data['price'] <= price_range[1])
            ].copy()


         # Filter by Availability
        if 'available' in filtered_data.columns:
            availability_options = {'Tous': None, 'Disponible': True, 'Indisponible': False} # MODIFIED
            selected_availability_str = st.sidebar.radio(
                "Filtrer par Disponibilité", # MODIFIED
                options=list(availability_options.keys()),
                index=0 # Default to 'All'
            )
            selected_availability_bool = availability_options[selected_availability_str]
            if selected_availability_bool is not None:
                filtered_data = filtered_data[filtered_data['available'] == selected_availability_bool].copy()
        else:
            st.sidebar.warning("Colonne de données de disponibilité introuvable.") # MODIFIED

    else:
        st.sidebar.warning("Aucune donnée ne correspond au filtre de domaine actuel.") # MODIFIED


    # --- Main Dashboard Area (Only if filtered_data is not empty) ---
    if not filtered_data.empty:
        st.header("📈 Indicateurs Clés de Performance (KPIs)") # MODIFIED
        st.markdown("Métriques d'aperçu pour les données sélectionnées.") # MODIFIED

        # --- Calculate KPIs (Safely handle potential missing columns/data) ---
        total_unique_products = filtered_data['product_id'].nunique() if 'product_id' in filtered_data else 0
        total_variants = len(filtered_data)

        available_variants = 0
        if 'available' in filtered_data.columns:
            # Ensure we handle potential Pandas <NA> boolean type correctly
             available_variants = filtered_data[filtered_data['available'].eq(True)].shape[0]

        unavailable_variants = total_variants - available_variants

        average_price = filtered_data['price'].mean() if 'price' in filtered_data.columns else None
        median_price = filtered_data['price'].median() if 'price' in filtered_data.columns else None

        num_vendors = filtered_data['vendor'].nunique() if 'vendor' in filtered_data else 0
        num_product_types = filtered_data['product_type'].nunique() if 'product_type' in filtered_data else 0

        # Display KPIs in columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Produits Uniques", f"{total_unique_products:,}") # MODIFIED
            st.metric("Total Variantes", f"{total_variants:,}") # MODIFIED
        with col2:
            st.metric("Variantes Disponibles", f"{available_variants:,}") # MODIFIED
            st.metric("Variantes Indisponibles", f"{unavailable_variants:,}") # MODIFIED
        with col3:
            st.metric("Prix Moyen des Variantes", f"${average_price:,.2f}" if pd.notna(average_price) else "N/D") # MODIFIED
            st.metric("Prix Médian des Variantes", f"${median_price:,.2f}" if pd.notna(median_price) else "N/D") # MODIFIED
        with col4:
            st.metric("Nombre de Fournisseurs", f"{num_vendors:,}") # MODIFIED
            st.metric("Nombre de Types de Produits", f"{num_product_types:,}") # MODIFIED

        st.markdown("---") # Divider

        # --- Data Visualizations ---
        st.header("📊 Visualisations des Données") # MODIFIED
        st.markdown("Graphiques interactifs explorant les données produits.") # MODIFIED

        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            # Price Distribution Histogram
            st.subheader("Distribution des Prix des Variantes") # MODIFIED
            if 'price' in filtered_data.columns and not filtered_data['price'].isnull().all():
                fig_price_hist = px.histogram(
                    filtered_data.dropna(subset=['price']),
                    x="price",
                    nbins=50,
                    title="Distribution des Prix des Variantes", # MODIFIED
                    labels={'price': 'Prix ($)'}, # MODIFIED
                    color_discrete_sequence=px.colors.sequential.Viridis
                )
                fig_price_hist.update_layout(bargap=0.1)
                st.plotly_chart(fig_price_hist, use_container_width=True)
            else:
                st.warning("Aucune donnée de prix valide disponible pour la sélection actuelle pour afficher la distribution.") # MODIFIED

            # Product Count per Vendor Bar Chart
            st.subheader("Nombre de Produits par Fournisseur") # MODIFIED
            if 'vendor' in filtered_data.columns and 'product_id' in filtered_data.columns:
                vendor_product_counts = filtered_data.groupby('vendor')['product_id'].nunique().sort_values(ascending=False).reset_index()
                vendor_product_counts.columns = ['Fournisseur', 'Nombre de Produits Uniques'] # MODIFIED
                if not vendor_product_counts.empty:
                    top_n = 20
                    display_counts = vendor_product_counts.head(top_n)
                    if len(vendor_product_counts) > top_n:
                         st.caption(f"Affichage des {top_n} Principaux Fournisseurs par Nombre de Produits") # MODIFIED

                    fig_vendor_bar = px.bar(
                        display_counts, 
                        x="Fournisseur", # MODIFIED
                        y="Nombre de Produits Uniques", # MODIFIED
                        title="Produits Uniques par Fournisseur", # MODIFIED
                        labels={'Fournisseur': 'Fournisseur', 'Nombre de Produits Uniques': 'Nombre de Produits Uniques'}, # MODIFIED (keys are new column names)
                        color='Fournisseur', # MODIFIED
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_vendor_bar.update_layout(xaxis_tickangle=-45, showlegend=False)
                    st.plotly_chart(fig_vendor_bar, use_container_width=True)
                else:
                    st.warning("Aucune donnée de fournisseur disponible pour la sélection actuelle.") # MODIFIED
            else:
                 st.warning("Données de Fournisseur ou d'ID Produit manquantes pour ce graphique.") # MODIFIED


        with viz_col2:
             # Variant Availability Pie Chart
            st.subheader("Disponibilité des Variantes") # MODIFIED
            if 'available' in filtered_data.columns:
                availability_counts = filtered_data['available'].value_counts().reset_index()
                availability_counts.columns = ['Disponible', 'Nombre'] # MODIFIED
                # Map boolean/None to readable strings safely
                availability_counts['Disponible'] = availability_counts['Disponible'].apply(
                    lambda x: 'Disponible' if x is True else ('Indisponible' if x is False else 'Inconnu') # MODIFIED
                )


                if not availability_counts.empty:
                    fig_avail_pie = px.pie(
                        availability_counts,
                        names='Disponible', # MODIFIED
                        values='Nombre', # MODIFIED
                        title='Statut de Disponibilité des Variantes', # MODIFIED
                        hole=0.3, # Make it a donut chart
                        color_discrete_map={'Disponible':'#2ca02c', 'Indisponible':'#d62728', 'Inconnu':'#7f7f7f'} # MODIFIED
                    )
                    fig_avail_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_avail_pie, use_container_width=True)
                else:
                    st.warning("Aucune donnée de disponibilité disponible pour la sélection actuelle.") # MODIFIED
            else:
                st.warning("Colonne de données de disponibilité introuvable pour le diagramme circulaire.") # MODIFIED

            # Product Count per Type Bar Chart
            st.subheader("Nombre de Produits par Type de Produit") # MODIFIED
            if 'product_type' in filtered_data.columns and 'product_id' in filtered_data.columns:
                type_product_counts = filtered_data.groupby('product_type')['product_id'].nunique().sort_values(ascending=False).reset_index()
                type_product_counts.columns = ['Type de Produit', 'Nombre de Produits Uniques'] # MODIFIED
                if not type_product_counts.empty:
                    top_n_type = 20
                    display_type_counts = type_product_counts.head(top_n_type)
                    if len(type_product_counts) > top_n_type:
                         st.caption(f"Affichage des {top_n_type} Principaux Types de Produits par Nombre de Produits") # MODIFIED

                    fig_type_bar = px.bar(
                        display_type_counts, 
                        x="Type de Produit", # MODIFIED
                        y="Nombre de Produits Uniques", # MODIFIED
                        title="Produits Uniques par Type", # MODIFIED
                        labels={'Type de Produit': 'Type de Produit', 'Nombre de Produits Uniques': 'Nombre de Produits Uniques'}, # MODIFIED
                        color='Type de Produit', # MODIFIED
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_type_bar.update_layout(xaxis_tickangle=-45, showlegend=False)
                    st.plotly_chart(fig_type_bar, use_container_width=True)
                else:
                    st.warning("Aucune donnée de type de produit disponible pour la sélection actuelle.") # MODIFIED
            else:
                 st.warning("Données de Type de Produit ou d'ID Produit manquantes pour ce graphique.") # MODIFIED

        st.markdown("---")

        # --- Data Storytelling & Insights ---
        st.header("🔍 Narration des Données & Perspectives") # MODIFIED

        # Storytelling Example 1: Availability Issues
        if 'available' in filtered_data.columns and unavailable_variants > 0:
            percent_unavailable = (unavailable_variants / total_variants) * 100 if total_variants > 0 else 0
            st.subheader("Préoccupations Concernant la Disponibilité des Stocks") # MODIFIED
            st.markdown(f"""
            Selon la sélection actuelle, **{unavailable_variants:,}** variantes de produits ({percent_unavailable:.1f}%) sont marquées comme **indisponibles**.
            Cela pourrait indiquer des problèmes de stock potentiels ou des articles qui ne sont intentionnellement pas à vendre.
            """) # MODIFIED
            # List some unavailable products/variants
            unavailable_sample_cols = ['title', 'variant_title', 'vendor', 'store_domain']
            # Check if required columns exist before trying to display
            if all(col in filtered_data.columns for col in unavailable_sample_cols):
                 unavailable_sample = filtered_data[filtered_data['available'] == False][unavailable_sample_cols].drop_duplicates().head(10)
                 if not unavailable_sample.empty:
                     with st.expander("Voir un Échantillon des Variantes Indisponibles"): # MODIFIED
                         st.dataframe(unavailable_sample, use_container_width=True)
            else:
                 st.caption("Impossible d'afficher l'échantillon indisponible - une ou plusieurs colonnes requises (title, variant_title, vendor, store_domain) sont manquantes.") # MODIFIED


        # Storytelling Example 2: Price Analysis
        st.subheader("Analyse des Niveaux de Prix") # MODIFIED
        if 'price' in filtered_data.columns and pd.notna(average_price):
            st.markdown(f"""
            Le prix moyen d'une variante dans l'ensemble de données sélectionné est de **${average_price:,.2f}**, avec un prix médian de **${median_price:,.2f}**.
            Le graphique de distribution ci-dessus montre comment les prix sont répartis dans la sélection. Des pics significatifs pourraient indiquer des niveaux de prix courants.
            """) # MODIFIED
            # Highlight most expensive items
            expensive_cols = ['title', 'vendor', 'price', 'store_domain']
            if all(col in filtered_data.columns for col in expensive_cols):
                most_expensive = filtered_data.sort_values('price', ascending=False).drop_duplicates(subset=['product_id']).head(5)
                if not most_expensive.empty:
                     with st.expander("Top 5 des Produits les Plus Chers (basé sur le prix de variante le plus élevé)"): # MODIFIED
                        st.dataframe(most_expensive[expensive_cols], use_container_width=True)
            else:
                 st.caption("Impossible d'afficher les produits les plus chers - des colonnes requises sont manquantes.") # MODIFIED
        else:
             st.markdown("L'analyse des prix est limitée en raison de données de prix manquantes ou invalides dans la sélection actuelle.") # MODIFIED

        # Storytelling Example 3: Vendor Dominance (if applicable)
        if 'vendor' in filtered_data.columns and 'product_id' in filtered_data.columns and num_vendors > 1:
             vendor_counts = filtered_data.groupby('vendor')['product_id'].nunique().sort_values(ascending=False)
             if not vendor_counts.empty:
                top_vendor = vendor_counts.index[0]
                top_vendor_count = vendor_counts.iloc[0]
                total_prods_for_vendors = vendor_counts.sum()
                top_vendor_share = (top_vendor_count / total_prods_for_vendors) * 100 if total_prods_for_vendors > 0 else 0

                if top_vendor_share > 40: # Only highlight if one vendor is somewhat dominant
                    st.subheader("Focus sur le Fournisseur") # MODIFIED
                    st.markdown(f"""
                    Le fournisseur **'{top_vendor}'** représente **{top_vendor_count:,}** produits uniques, soit environ **{top_vendor_share:.1f}%** des produits des fournisseurs connus dans la sélection actuelle. 
                    Cela suggère une présence significative ou un catalogue important de ce fournisseur par rapport aux autres dans les données filtrées.
                    """) # MODIFIED


        st.markdown("---")

        # --- Raw Data Exploration ---
        st.header("Données Brutes") # MODIFIED
        st.markdown("Explorez les données filtrées utilisées pour l'analyse ci-dessus.") # MODIFIED
        with st.expander("Afficher le Tableau des Données Filtrées"): # MODIFIED
            # Show a limited number of columns by default for better readability
            default_columns_to_show = ['store_domain', 'vendor', 'title', 'product_type', 'variant_title', 'price', 'available', 'updated_at']
            # Filter to only columns that actually exist in the dataframe
            columns_to_show = [col for col in default_columns_to_show if col in filtered_data.columns]
            if columns_to_show:
                display_df = filtered_data[columns_to_show].copy()
                st.dataframe(display_df, use_container_width=True)
                st.caption(f"Affichage de {len(filtered_data)} lignes correspondant aux filtres actuels. Colonnes sélectionnées affichées.") # MODIFIED
            else:
                st.warning("Aucune colonne disponible à afficher dans le tableau des données brutes.") # MODIFIED


    elif data is not None: # Original data was loaded, but filtered result is empty
        st.warning("Aucune donnée ne correspond aux filtres sélectionnés. Essayez d'ajuster les critères de filtre dans la barre latérale.") # MODIFIED
    # else: Handled by the initial load_data check


else:
    # This message is shown if load_data returned None or empty DataFrame initially
    st.warning("Impossible de charger ou de traiter les données produits. Veuillez vous assurer que le fichier de données existe et contient des données valides, ou utilisez le bouton 'Récupérer de Nouvelles Données Shopify'.") # MODIFIED

# Add footer or additional info if needed
st.sidebar.markdown("---")
st.sidebar.info("Tableau de bord développé pour analyser les données produits Shopify.") # MODIFIED