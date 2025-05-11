import kfp
from kfp import dsl
from kfp.components import func_to_container_op
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import json

@func_to_container_op
def load_and_preprocess_data():
    """Load and preprocess the scraped data"""
    try:
        # Load the scraped data
        df = pd.read_csv('aliexpress_multi_page_firefox.csv')
        
        # Basic preprocessing
        df = df.dropna()
        df = df.drop_duplicates()
        
        # Save preprocessed data
        df.to_csv('preprocessed_data.csv', index=False)
        return "Data preprocessing completed successfully"
    except Exception as e:
        return f"Error in data preprocessing: {str(e)}"

@func_to_container_op
def feature_engineering():
    """Perform feature engineering on the preprocessed data"""
    try:
        # Load preprocessed data
        df = pd.read_csv('preprocessed_data.csv')
        
        # Feature engineering steps
        # Add your feature engineering logic here
        # Example: Create price categories, calculate price per unit, etc.
        
        # Save engineered features
        df.to_csv('engineered_features.csv', index=False)
        return "Feature engineering completed successfully"
    except Exception as e:
        return f"Error in feature engineering: {str(e)}"

@func_to_container_op
def train_model():
    """Train the ML model"""
    try:
        # Load engineered features
        df = pd.read_csv('engineered_features.csv')
        
        # Prepare features and target
        X = df.drop('target_column', axis=1)  # Replace with your target column
        y = df['target_column']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Save model and scaler
        joblib.dump(model, 'model.joblib')
        joblib.dump(scaler, 'scaler.joblib')
        
        # Save test data for evaluation
        np.save('X_test.npy', X_test_scaled)
        np.save('y_test.npy', y_test)
        
        return "Model training completed successfully"
    except Exception as e:
        return f"Error in model training: {str(e)}"

@func_to_container_op
def evaluate_model():
    """Evaluate the trained model"""
    try:
        # Load model and test data
        model = joblib.load('model.joblib')
        X_test = np.load('X_test.npy')
        y_test = np.load('y_test.npy')
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Save metrics
        metrics = {
            'accuracy': accuracy,
            'classification_report': report
        }
        with open('model_metrics.json', 'w') as f:
            json.dump(metrics, f)
        
        return "Model evaluation completed successfully"
    except Exception as e:
        return f"Error in model evaluation: {str(e)}"

@func_to_container_op
def generate_insights():
    """Generate business insights using LLM"""
    try:
        # Load model metrics
        with open('model_metrics.json', 'r') as f:
            metrics = json.load(f)
        
        # Load engineered features
        df = pd.read_csv('engineered_features.csv')
        
        # Generate insights
        # Add your LLM integration here
        # Example: Use GROQ API to analyze results
        
        # Save insights
        insights = {
            'top_products': df.nlargest(10, 'score').to_dict('records'),
            'model_performance': metrics,
            'recommendations': "Your LLM-generated recommendations here"
        }
        
        with open('business_insights.json', 'w') as f:
            json.dump(insights, f)
        
        return "Insights generation completed successfully"
    except Exception as e:
        return f"Error in insights generation: {str(e)}"

@dsl.pipeline(
    name='Smart E-commerce ML Pipeline',
    description='End-to-end ML pipeline for e-commerce product analysis'
)
def smart_ecommerce_ml_pipeline():
    # Define the pipeline steps
    preprocess_task = load_and_preprocess_data()
    feature_task = feature_engineering().after(preprocess_task)
    train_task = train_model().after(feature_task)
    evaluate_task = evaluate_model().after(train_task)
    insights_task = generate_insights().after(evaluate_task)

if __name__ == '__main__':
    # Compile the pipeline
    kfp.compiler.Compiler().compile(smart_ecommerce_ml_pipeline, 'smart_ecommerce_ml_pipeline.yaml') 