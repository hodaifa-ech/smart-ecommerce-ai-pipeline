import kfp
from kfp import dsl
from kfp.components import func_to_container_op
import os

# Define the preprocessing component
@func_to_container_op
def preprocess_data(
    input_data: str,
    output_data: str
):
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import StandardScaler
    
    # Load data
    df = pd.read_csv(input_data)
    
    # Clean and preprocess data
    df['price_numeric'] = df['price'].apply(lambda x: float(str(x).replace('$', '').strip()) if pd.notnull(x) else np.nan)
    df['sales_numeric'] = df['sales_info'].apply(lambda x: int(str(x).replace('+', '').replace(',', '')) if pd.notnull(x) else 0)
    df['rating_numeric'] = df['rating'].apply(lambda x: float(x) if pd.notnull(x) else np.nan)
    
    # Handle missing values
    df['price_numeric'].fillna(df['price_numeric'].median(), inplace=True)
    df['rating_numeric'].fillna(df['rating_numeric'].median(), inplace=True)
    
    # Save processed data
    df.to_csv(output_data, index=False)

# Define the training component
@func_to_container_op
def train_model(
    input_data: str,
    model_output: str
):
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    import joblib
    
    # Load processed data
    df = pd.read_csv(input_data)
    
    # Prepare features and target
    X = df[['price_numeric', 'sales_numeric', 'rating_numeric']]
    y = df['is_attractive']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Save model
    joblib.dump(model, model_output)

# Define the evaluation component
@func_to_container_op
def evaluate_model(
    input_data: str,
    model_path: str,
    metrics_output: str
):
    import pandas as pd
    from sklearn.metrics import accuracy_score, classification_report
    import joblib
    import json
    
    # Load data and model
    df = pd.read_csv(input_data)
    model = joblib.load(model_path)
    
    # Prepare test data
    X_test = df[['price_numeric', 'sales_numeric', 'rating_numeric']]
    y_test = df['is_attractive']
    
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
    with open(metrics_output, 'w') as f:
        json.dump(metrics, f)

# Define the pipeline
@dsl.pipeline(
    name='product-attractiveness-pipeline',
    description='Pipeline for product attractiveness classification'
)
def product_attractiveness_pipeline():
    # Define the pipeline steps
    preprocess_task = preprocess_data(
        input_data='/app/data/aliexpress_multi_page_firefox.csv',
        output_data='/app/data/processed_data.csv'
    )
    
    train_task = train_model(
        input_data=preprocess_task.output,
        model_output='/app/models/model.joblib'
    )
    
    evaluate_task = evaluate_model(
        input_data=preprocess_task.output,
        model_path=train_task.output,
        metrics_output='/app/metrics/metrics.json'
    )

# Compile the pipeline
if __name__ == '__main__':
    kfp.compiler.Compiler().compile(
        product_attractiveness_pipeline,
        'product-attractiveness-pipeline.yaml'
    ) 