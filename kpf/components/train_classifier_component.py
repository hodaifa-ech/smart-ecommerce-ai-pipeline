from kfp.dsl import component, Input, Output, Dataset, Model, Metrics

@component(
    base_image="python:3.9",
    packages_to_install=[
        "pandas==2.2.2",
        "scikit-learn==1.4.2",
        "numpy==1.26.4",
    ],
)
def train_classifier_component(
    input_dataset: Input[Dataset],
    output_model: Output[Model],
    output_metrics: Output[Metrics],
):
    """
    Trains a product attractiveness classifier based on the scraped data.
    """
    import pandas as pd
    import numpy as np
    import re
    import joblib # For saving the model
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report

    # --- Your data cleaning and feature engineering logic from tools/machine_learning.py ---
    # (Include helper functions: clean_price, clean_sales_info, etc.)
    # ...

    # ** KEY CHANGE: Load data from the input artifact's path **
    df_raw = pd.read_csv(input_dataset.path)

    # (Your full preprocessing logic from preprocess_data_and_create_target goes here)
    # ...
    # Let's assume this results in a DataFrame called `df_processed`
    # and a list of `features`.
    
    df_processed, features = ..., ... # Result of your preprocessing

    if df_processed is None or df_processed.empty:
        print("Data processing resulted in an empty dataframe. Aborting training.")
        return

    X = df_processed[features]
    y = df_processed['is_attractive']

    if y.nunique() < 2:
        print("Not enough class diversity to train. Aborting.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)

    # ** KEY CHANGE: Save the model to the output artifact's path **
    joblib.dump(model, output_model.path)
    print(f"Model saved to: {output_model.path}")

    # Evaluate and log metrics
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    # ** KEY CHANGE: Log metrics to the metrics artifact **
    output_metrics.log_metric("accuracy", round(accuracy, 4))
    output_metrics.log_metric("precision_class_1", round(report['1']['precision'], 4))
    output_metrics.log_metric("recall_class_1", round(report['1']['recall'], 4))
    output_metrics.log_metric("f1_score_class_1", round(report['1']['f1-score'], 4))
    
    print(f"Accuracy: {accuracy}")
    print("Classification Report logged to Kubeflow Metrics.")