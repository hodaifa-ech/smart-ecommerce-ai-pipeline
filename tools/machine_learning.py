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
        if 'k' in sales_str_cleaned:
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
    if "le plus vendu" in badges_str_lower or \
       "best seller" in badges_str_lower or \
       "top selling" in badges_str_lower or \
       "choix d'aliexpress" in badges_str_lower or \
       "choice" in badges_str_lower:
        return 1
    return 0

# --- Data Loading and Caching ---
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        st.error(f"Error: Data file not found at {file_path}. Make sure 'aliexpress_multi_page_firefox.csv' is in the parent directory.")
        return None
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

@st.cache_data
def preprocess_data_and_create_target(df_raw):
    if df_raw is None:
        return None, None

    df = df_raw.copy()
    
    # Expected columns - add or remove as per your CSV
    # This helps in identifying if critical columns are missing early on.
    expected_cols = ['price', 'sales_info', 'rating', 'additional_badges', 'name'] 
    for col in expected_cols:
        if col not in df.columns:
            st.warning(f"Column '{col}' not found in the CSV. It will be treated as missing.")
            df[col] = np.nan # Create missing columns with NaNs to prevent key errors later

    # Apply cleaning functions
    df['price_numeric'] = df['price'].apply(clean_price)
    df['sales_numeric'] = df['sales_info'].apply(clean_sales_info)
    df['rating_numeric'] = df['rating'].apply(clean_rating)
    df['has_bestseller_badge'] = df['additional_badges'].apply(extract_bestseller_badge)
    
    # Handle NaNs after cleaning - simple imputation for this example
    df['price_numeric'].fillna(df['price_numeric'].median(), inplace=True)
    df['sales_numeric'].fillna(0, inplace=True) # Assuming NaN sales means 0 or unknown
    df['rating_numeric'].fillna(df['rating_numeric'].median(), inplace=True) 

    # Create 'is_attractive' target variable based on heuristics
    scores = pd.Series(0, index=df.index)
    scores += (df['sales_numeric'] > SALES_THRESHOLD_LOW) * 1
    scores += (df['sales_numeric'] > SALES_THRESHOLD_HIGH) * 1
    scores += (df['rating_numeric'] > RATING_THRESHOLD_GOOD) * 1
    scores += (df['rating_numeric'] > RATING_THRESHOLD_EXCELLENT) * 1
    scores += (df['has_bestseller_badge'] == 1) * 2

    df['attractiveness_score'] = scores
    df['is_attractive'] = (scores >= ATTRACTIVENESS_SCORE_THRESHOLD).astype(int)
    
    features = ['price_numeric', 'sales_numeric', 'rating_numeric', 'has_bestseller_badge']
    
    # Ensure all feature columns exist before dropping NaNs based on them
    for feature_col in features:
        if feature_col not in df.columns:
             st.error(f"Critical feature column '{feature_col}' missing after processing. Check CSV and cleaning logic.")
             return None, None

    df_processed = df.dropna(subset=features + ['is_attractive']).copy()

    if df_processed.empty:
        st.warning("No data left after preprocessing. Check your CSV and cleaning logic.")
        return None, None
    
    if df_processed['is_attractive'].nunique() < 2:
        st.warning(f"Only one class found for 'is_attractive' after preprocessing. Target counts: \n{df_processed['is_attractive'].value_counts().to_dict()}. Adjust ATTRACTIVENESS_SCORE_THRESHOLD or check data.")
        if df_processed['is_attractive'].nunique() == 1 and len(df_processed) > 1:
            first_index = df_processed.index[0]
            df_processed.loc[first_index, 'is_attractive'] = 1 - df_processed.loc[first_index, 'is_attractive']
            st.info("Artificially created a second class for 'is_attractive' for demonstration purposes as only one was found.")
        elif len(df_processed) <=1:
             st.error("Not enough data points to proceed after preprocessing.")
             return None, None

    return df_processed, features

# --- Model Training ---
@st.cache_resource 
def train_classifier(df_processed, features_list):
    if df_processed is None or df_processed.empty:
        st.error("Cannot train model: Processed data is empty.")
        return None, None, None
    if df_processed['is_attractive'].nunique() < 2 :
        st.error("Cannot train model: Insufficient class diversity for 'is_attractive' (need at least 2).")
        return None, None, None


    X = df_processed[features_list]
    y = df_processed['is_attractive']

    if len(X) < 10: 
        st.warning(f"Very few samples ({len(X)}) available for training. Model performance might be unreliable.")

    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    except ValueError as e:
        st.error(f"Error during train_test_split (likely due to insufficient samples for a class after split): {e}")
        st.info(f"Class distribution in y before split: {y.value_counts().to_dict()}")
        return None, None, None

    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    
    try:
        model.fit(X_train, y_train)
    except Exception as e:
        st.error(f"Error during model fitting: {e}")
        return None, None, None

    if len(X_test) == 0:
        st.warning("Test set is empty. Cannot evaluate model performance.")
        return model, None, None # Return model but no accuracy/report

    y_pred_test = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred_test)
    
    report = classification_report(y_test, y_pred_test, output_dict=True, zero_division=0)
    
    return model, accuracy, report

# --- Streamlit App ---
st.set_page_config(page_title="Product Attractiveness Classifier", layout="wide")

st.title("🛍️ AliExpress Product Attractiveness Classifier")
st.markdown(f"""
This app uses data from `aliexpress_multi_page_firefox.csv` to train a classifier.
The goal is to predict if a product is "attractive" based on features like price, sales, rating, and badges.
This aligns with **Étape 2: Analyse et sélection des Top-K produits** from your dossier.
""")

raw_df = load_data(DATA_FILE_PATH)

if raw_df is not None:
    st.sidebar.success("Data loaded successfully!")
    st.sidebar.metric("Total Products in CSV", len(raw_df))

    processed_df, model_features = preprocess_data_and_create_target(raw_df)

    if processed_df is not None and not processed_df.empty:
        st.sidebar.metric("Products after Preprocessing", len(processed_df))
        st.sidebar.write("Target Class Distribution ('is_attractive'):")
        st.sidebar.json(processed_df['is_attractive'].value_counts().to_dict())

        if st.sidebar.checkbox("Show Sample of Processed Data", False):
            st.subheader("Sample of Processed Data (with 'is_attractive' target)")
            # Ensure 'name' column exists, or handle its absence
            display_cols = ['price_numeric', 'sales_numeric', 'rating_numeric', 'has_bestseller_badge', 'attractiveness_score', 'is_attractive']
            if 'name' in processed_df.columns:
                display_cols.insert(0, 'name')
            st.dataframe(processed_df[display_cols].head())
            st.caption(f"Attractiveness Score Threshold for 'is_attractive'=1 is: {ATTRACTIVENESS_SCORE_THRESHOLD}")

        model, accuracy, report = train_classifier(processed_df.copy(), model_features) 

        if model:
            st.sidebar.subheader("📊 Model Performance")
            if accuracy is not None:
                st.sidebar.metric("Accuracy on Test Set", f"{accuracy:.2%}")
            if report:
                if '0' in report and isinstance(report['0'], dict):
                    st.sidebar.text("Class 0 (Not Attractive):")
                    st.sidebar.json({
                        "precision": f"{report['0'].get('precision', 0):.2f}",
                        "recall": f"{report['0'].get('recall', 0):.2f}",
                        "f1-score": f"{report['0'].get('f1-score', 0):.2f}"
                    })
                if '1' in report and isinstance(report['1'], dict):
                    st.sidebar.text("Class 1 (Attractive):")
                    st.sidebar.json({
                        "precision": f"{report['1'].get('precision', 0):.2f}",
                        "recall": f"{report['1'].get('recall', 0):.2f}",
                        "f1-score": f"{report['1'].get('f1-score', 0):.2f}"
                    })
            
            st.markdown("---")
            st.header("🚀 Predict Attractiveness for a New Product")
            
            col1, col2 = st.columns(2)
            with col1:
                price_input = st.number_input("Price (e.g., 143.97)", min_value=0.0, value=150.0, step=10.0)
                rating_input = st.slider("Rating (1-5)", min_value=1.0, max_value=5.0, value=4.5, step=0.1)
            with col2:
                sales_input = st.number_input("Number of Sales (e.g., 5000)", min_value=0, value=1000, step=100)
                badge_input_text = st.text_input("Additional Badges (e.g., 'Le plus vendu')", "Le plus vendu")

            if st.button("🔮 Predict Attractiveness"):
                input_data_dict = {
                    'price_numeric': float(price_input),
                    'sales_numeric': int(sales_input),
                    'rating_numeric': float(rating_input),
                    'has_bestseller_badge': extract_bestseller_badge(badge_input_text)
                }
                input_df = pd.DataFrame([input_data_dict])
                
                input_df = input_df[model_features] # Ensure correct column order

                prediction_proba = model.predict_proba(input_df)[0]
                prediction = model.predict(input_df)[0]

                st.subheader("📈 Prediction Result:")
                if prediction == 1:
                    st.success(f"This product is LIKELY ATTRACTIVE (Confidence: {prediction_proba[1]:.2%})")
                    st.balloons()
                else:
                    st.warning(f"This product is LIKELY NOT ATTRACTIVE (Confidence for 'Attractive': {prediction_proba[1]:.2%})")
                
                st.markdown("---")
                st.write("Feature Importances from the trained model:")
                try:
                    feature_importances = pd.Series(model.feature_importances_, index=model_features).sort_values(ascending=False)
                    st.bar_chart(feature_importances)
                except Exception as e:
                    st.error(f"Could not display feature importances: {e}")

                st.write("Input data used for prediction:")
                st.dataframe(input_df)
        else:
            st.error("Model training failed or was skipped. Check the data and preprocessing steps. See warnings/errors above or in the console.")
    else:
        st.error("Data preprocessing failed. Cannot proceed with model training or prediction.")
else:
    st.error("Failed to load data. The application cannot start.")

st.markdown("---")
st.info("This app uses a heuristic to define 'attractiveness' for training. The model then learns to classify products based on this definition. Adjust heuristic parameters in the script for different results.")