import streamlit as st
import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
# from sklearn.preprocessing import LabelEncoder # Not currently used, can be removed if not planned
import os

# --- Configuration ---
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'aliexpress_multi_page_firefox.csv')
# Heuristic scoring parameters (can be adjusted)
SALES_THRESHOLD_LOW = 500
SALES_THRESHOLD_HIGH = 2000
RATING_THRESHOLD_GOOD = 4.0
RATING_THRESHOLD_EXCELLENT = 4.5
ATTRACTIVENESS_SCORE_THRESHOLD = 3 # Product needs at least this score to be "attractive"

# --- Helper Functions (Updated) ---
def clean_price(price_str):
    # 1. Handle explicit NaNs or "N/A" strings first
    if pd.isna(price_str) or str(price_str).lower() == "n/a":
        return np.nan

    # 2. If it's already a number (int or float that is not NaN)
    if isinstance(price_str, (int, float)):
        return float(price_str)

    # 3. If it's a string, try to parse it
    cleaned_price = re.sub(r'[^\d\.]', '', str(price_str))
    try:
        if cleaned_price: # Ensure there's something to convert
            return float(cleaned_price)
        else:
            return np.nan
    except ValueError:
        return np.nan

def clean_sales_info(sales_str):
    # 1. Handle explicit NaNs or "N/A" strings first
    if pd.isna(sales_str) or str(sales_str).lower() == "n/a":
        return 0  # Default to 0 sales if not specified

    # 2. If it's already an int
    if isinstance(sales_str, int):
        return sales_str
    
    # 3. If it's a float (and not NaN, due to the first check)
    if isinstance(sales_str, float):
        return int(sales_str) # Safe to convert to int

    # 4. If it's a string, try to parse it
    sales_str_cleaned = str(sales_str).lower().replace(' ', '').replace(',', '')
    numbers = re.findall(r'\d+', sales_str_cleaned)
    if numbers:
        num_part = int("".join(numbers))
        if 'k' in sales_str_cleaned: # k is usually for "kilo" / 1000, universal
            num_part *= 1000
        return num_part
    
    # 5. If all else fails (e.g., unparseable string), return 0
    return 0

def clean_rating(rating_val):
    if pd.isna(rating_val) or str(rating_val).lower() == "n/a":
        return np.nan 
    try:
        return float(rating_val) 
    except ValueError:
        return np.nan

def extract_bestseller_badge(badges_str):
    if pd.isna(badges_str):
        return 0
    badges_str_lower = str(badges_str).lower()
    # "Le plus vendu" and "choix d'aliexpress" are already French
    if "le plus vendu" in badges_str_lower or \
       "best seller" in badges_str_lower or \
       "top selling" in badges_str_lower or \
       "choix d'aliexpress" in badges_str_lower or \
       "choice" in badges_str_lower: # "choice" is general, could be part of "AliExpress Choice"
        return 1
    return 0

# --- Data Loading and Caching ---
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        st.error(f"Erreur : Fichier de données non trouvé à {file_path}. Assurez-vous que 'aliexpress_multi_page_firefox.csv' est dans le répertoire parent.") # MODIFIED
        return None
    except Exception as e:
        st.error(f"Erreur lors du chargement du CSV : {e}") # MODIFIED
        return None

@st.cache_data
def preprocess_data_and_create_target(df_raw):
    if df_raw is None:
        return None, None

    df = df_raw.copy()
    
    expected_cols = ['price', 'sales_info', 'rating', 'additional_badges', 'name'] 
    for col in expected_cols:
        if col not in df.columns:
            st.warning(f"Colonne '{col}' non trouvée dans le CSV. Elle sera traitée comme manquante.") # MODIFIED
            df[col] = np.nan 

    df['price_numeric'] = df['price'].apply(clean_price)
    df['sales_numeric'] = df['sales_info'].apply(clean_sales_info)
    df['rating_numeric'] = df['rating'].apply(clean_rating)
    df['has_bestseller_badge'] = df['additional_badges'].apply(extract_bestseller_badge)
    
    df['price_numeric'].fillna(df['price_numeric'].median(), inplace=True)
    df['sales_numeric'].fillna(0, inplace=True) 
    df['rating_numeric'].fillna(df['rating_numeric'].median(), inplace=True) 

    scores = pd.Series(0, index=df.index)
    scores += (df['sales_numeric'] > SALES_THRESHOLD_LOW) * 1
    scores += (df['sales_numeric'] > SALES_THRESHOLD_HIGH) * 1
    scores += (df['rating_numeric'] > RATING_THRESHOLD_GOOD) * 1
    scores += (df['rating_numeric'] > RATING_THRESHOLD_EXCELLENT) * 1
    scores += (df['has_bestseller_badge'] == 1) * 2

    df['attractiveness_score'] = scores
    df['is_attractive'] = (scores >= ATTRACTIVENESS_SCORE_THRESHOLD).astype(int)
    
    features = ['price_numeric', 'sales_numeric', 'rating_numeric', 'has_bestseller_badge']
    
    for feature_col in features:
        if feature_col not in df.columns:
             st.error(f"Colonne de caractéristique critique '{feature_col}' manquante après traitement. Vérifiez le CSV et la logique de nettoyage.") # MODIFIED
             return None, None

    df_processed = df.dropna(subset=features + ['is_attractive']).copy()

    if df_processed.empty:
        st.warning("Aucune donnée restante après le prétraitement. Vérifiez votre CSV et la logique de nettoyage.") # MODIFIED
        return None, None
    
    if df_processed['is_attractive'].nunique() < 2:
        st.warning(f"Une seule classe trouvée pour 'is_attractive' après prétraitement. Compte des cibles : \n{df_processed['is_attractive'].value_counts().to_dict()}. Ajustez ATTRACTIVENESS_SCORE_THRESHOLD ou vérifiez les données.") # MODIFIED
        if df_processed['is_attractive'].nunique() == 1 and len(df_processed) > 1:
            first_index = df_processed.index[0]
            df_processed.loc[first_index, 'is_attractive'] = 1 - df_processed.loc[first_index, 'is_attractive']
            st.info("Une deuxième classe pour 'is_attractive' a été créée artificiellement à des fins de démonstration car une seule a été trouvée.") # MODIFIED
        elif len(df_processed) <=1:
             st.error("Pas assez de points de données pour continuer après le prétraitement.") # MODIFIED
             return None, None

    return df_processed, features

# --- Model Training ---
@st.cache_resource 
def train_classifier(df_processed, features_list):
    if df_processed is None or df_processed.empty:
        st.error("Impossible d'entraîner le modèle : Les données traitées sont vides.") # MODIFIED
        return None, None, None
    if df_processed['is_attractive'].nunique() < 2 :
        st.error("Impossible d'entraîner le modèle : Diversité de classes insuffisante pour 'is_attractive' (au moins 2 requises).") # MODIFIED
        return None, None, None


    X = df_processed[features_list]
    y = df_processed['is_attractive']

    if len(X) < 10: 
        st.warning(f"Très peu d'échantillons ({len(X)}) disponibles pour l'entraînement. La performance du modèle pourrait ne pas être fiable.") # MODIFIED

    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    except ValueError as e:
        st.error(f"Erreur lors du train_test_split (probablement due à un nombre insuffisant d'échantillons pour une classe après la division) : {e}") # MODIFIED
        st.info(f"Distribution des classes dans y avant la division : {y.value_counts().to_dict()}") # MODIFIED
        return None, None, None

    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    
    try:
        model.fit(X_train, y_train)
    except Exception as e:
        st.error(f"Erreur lors de l'ajustement du modèle : {e}") # MODIFIED
        return None, None, None

    if len(X_test) == 0:
        st.warning("L'ensemble de test est vide. Impossible d'évaluer la performance du modèle.") # MODIFIED
        return model, None, None 

    y_pred_test = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred_test)
    
    report = classification_report(y_test, y_pred_test, output_dict=True, zero_division=0)
    
    return model, accuracy, report

# --- Streamlit App ---
st.set_page_config(page_title="Classificateur d'Attractivité de Produit", layout="wide") # MODIFIED

st.title("🛍️ Classificateur d'Attractivité de Produit AliExpress") # MODIFIED
st.markdown(f"""
Cette application utilise les données de `aliexpress_multi_page_firefox.csv` pour entraîner un classificateur.
L'objectif est de prédire si un produit est "attractif" en fonction de caractéristiques telles que le prix, les ventes, l'évaluation et les badges.
Cela correspond à **Étape 2 : Analyse et sélection des Top-K produits** de votre dossier.
""") # MODIFIED

raw_df = load_data(DATA_FILE_PATH)

if raw_df is not None:
    st.sidebar.success("Données chargées avec succès !") # MODIFIED
    st.sidebar.metric("Nombre total de produits dans le CSV", len(raw_df)) # MODIFIED

    processed_df, model_features = preprocess_data_and_create_target(raw_df)

    if processed_df is not None and not processed_df.empty:
        st.sidebar.metric("Produits après Prétraitement", len(processed_df)) # MODIFIED
        st.sidebar.write("Distribution des classes cibles ('is_attractive') :") # MODIFIED
        st.sidebar.json(processed_df['is_attractive'].value_counts().to_dict())

        if st.sidebar.checkbox("Afficher un échantillon des données traitées", False): # MODIFIED
            st.subheader("Échantillon des Données Traitées (avec la cible 'is_attractive')") # MODIFIED
            display_cols = ['price_numeric', 'sales_numeric', 'rating_numeric', 'has_bestseller_badge', 'attractiveness_score', 'is_attractive']
            if 'name' in processed_df.columns:
                display_cols.insert(0, 'name')
            st.dataframe(processed_df[display_cols].head())
            st.caption(f"Le seuil du score d'attractivité pour 'is_attractive'=1 est : {ATTRACTIVENESS_SCORE_THRESHOLD}") # MODIFIED

        model, accuracy, report = train_classifier(processed_df.copy(), model_features) 

        if model:
            st.sidebar.subheader("📊 Performance du Modèle") # MODIFIED
            if accuracy is not None:
                st.sidebar.metric("Précision sur l'Ensemble de Test", f"{accuracy:.2%}") # MODIFIED
            if report:
                if '0' in report and isinstance(report['0'], dict):
                    st.sidebar.text("Classe 0 (Non Attractif) :") # MODIFIED
                    st.sidebar.json({
                        "précision": f"{report['0'].get('precision', 0):.2f}", # MODIFIED
                        "rappel": f"{report['0'].get('recall', 0):.2f}",    # MODIFIED
                        "score-f1": f"{report['0'].get('f1-score', 0):.2f}" # MODIFIED
                    })
                if '1' in report and isinstance(report['1'], dict):
                    st.sidebar.text("Classe 1 (Attractif) :") # MODIFIED
                    st.sidebar.json({
                        "précision": f"{report['1'].get('precision', 0):.2f}", # MODIFIED
                        "rappel": f"{report['1'].get('recall', 0):.2f}",    # MODIFIED
                        "score-f1": f"{report['1'].get('f1-score', 0):.2f}" # MODIFIED
                    })
            
            st.markdown("---")
            st.header("🚀 Prédire l'Attractivité d'un Nouveau Produit") # MODIFIED
            
            col1, col2 = st.columns(2)
            with col1:
                price_input = st.number_input("Prix (ex: 143.97)", min_value=0.0, value=150.0, step=10.0) # MODIFIED
                rating_input = st.slider("Évaluation (1-5)", min_value=1.0, max_value=5.0, value=4.5, step=0.1) # MODIFIED
            with col2:
                sales_input = st.number_input("Nombre de Ventes (ex: 5000)", min_value=0, value=1000, step=100) # MODIFIED
                badge_input_text = st.text_input("Badges Additionnels (ex: 'Le plus vendu')", "Le plus vendu") # MODIFIED (default value already French)

            if st.button("🔮 Prédire l'Attractivité"): # MODIFIED
                input_data_dict = {
                    'price_numeric': float(price_input),
                    'sales_numeric': int(sales_input),
                    'rating_numeric': float(rating_input),
                    'has_bestseller_badge': extract_bestseller_badge(badge_input_text)
                }
                input_df = pd.DataFrame([input_data_dict])
                
                input_df = input_df[model_features] 

                prediction_proba = model.predict_proba(input_df)[0]
                prediction = model.predict(input_df)[0]

                st.subheader("📈 Résultat de la Prédiction :") # MODIFIED
                if prediction == 1:
                    st.success(f"Ce produit est PROBABLEMENT ATTRACTIF (Confiance : {prediction_proba[1]:.2%})") # MODIFIED
                    st.balloons()
                else:
                    st.warning(f"Ce produit est PROBABLEMENT NON ATTRACTIF (Confiance pour 'Attractif' : {prediction_proba[1]:.2%})") # MODIFIED
                
                st.markdown("---")
                st.write("Importances des Caractéristiques du modèle entraîné :") # MODIFIED
                try:
                    feature_importances = pd.Series(model.feature_importances_, index=model_features).sort_values(ascending=False)
                    st.bar_chart(feature_importances)
                except Exception as e:
                    st.error(f"Impossible d'afficher les importances des caractéristiques : {e}") # MODIFIED

                st.write("Données d'entrée utilisées pour la prédiction :") # MODIFIED
                st.dataframe(input_df)
        else:
            st.error("L'entraînement du modèle a échoué ou a été ignoré. Vérifiez les données et les étapes de prétraitement. Voir les avertissements/erreurs ci-dessus ou dans la console.") # MODIFIED
    else:
        st.error("Le prétraitement des données a échoué. Impossible de continuer avec l'entraînement du modèle ou la prédiction.") # MODIFIED
else:
    st.error("Échec du chargement des données. L'application ne peut pas démarrer.") # MODIFIED

st.markdown("---")
st.info("Cette application utilise une heuristique pour définir l'attractivité' pour l'entraînement. Le modèle apprend ensuite à classifier les produits en fonction de cette définition. Ajustez les paramètres heuristiques dans le script pour des résultats différents.") # MODIFIED