
<div>
  <img src="https://github.com/user-attachments/assets/bb4920ab-6ee6-4b5a-b928-401df4c94993" width="200px"/>
</div>

# Smart E-commerce AI Pipeline

Advanced e-commerce analytics platform combining web scraping, LLM-powered recommendations, and real-time dashboards.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Firefox browser
- [Groq API key](https://console.groq.com/)

### Installation
```bash
# Clone repository
git clone https://github.com/hodaifa-ech/smart-ecommerce-ai-pipeline
cd smart-ecommerce-ai-pipeline

# Install dependencies
pip install -r requirements.txt

# Set API key (Linux/macOS)
export GROQ_API_KEY="your_api_key_here"

# For Windows:
# set GROQ_API_KEY="your_api_key_here"

# Launch application
streamlit run main.py
```

## ✨ Key Features
| Feature | Description |
|---------|-------------|
| 📊 **Interactive Dashboard** | Real-time sales analytics with filters |
| 🚀 **Top Selling Products** | Identify best-performing items |
| 💬 **AI Recommendation Bot** | LLM-powered shopping assistant |
| ⚙️ **Automated Scraping** | Product data extraction pipeline |

## 🛠️ Tech Stack
- **Data Extraction**: Selenium, Firefox
- **AI Engine**: Llama 3 70B (via Groq)
- **Frontend**: Streamlit
- **Data Processing**: CSV, Pandas
- **Infrastructure**: Docker, Kubernetes

## Data Scrapping 
|Shop|Method|Technologies|
|---|---|---|
| <img src="https://github.com/user-attachments/assets/0e03c7f7-1ac4-4fd4-b593-9809bde4223f" width="100px" /> |![image](https://github.com/user-attachments/assets/f3759752-98b3-4a05-9598-8bde9dfaa474) <br/> <img src="https://github.com/user-attachments/assets/90e4a3e3-6ca1-4c59-b3d9-995ed48d5c91" width="60%" /> | <img src="https://github.com/user-attachments/assets/a8e831ac-1f69-4a78-8c1a-da317ed617b1" width="100px" /> <br/> <img src="https://github.com/user-attachments/assets/046f73e3-9978-4117-afe3-e78c9b5fed49" width="100px" />   |
| <img src="https://github.com/user-attachments/assets/23a748ba-49f2-4201-a97f-eeccc2e7dfe1" width="100px"/> | ![image](https://github.com/user-attachments/assets/22d7e7ed-62f9-4538-a2a8-2d1f34752b61) |API `/products.json`|



## 📸 Application Screenshots

### Dashboard Analytics
|Ali-Express|Shopify|
|---|---|
| ![image](https://github.com/user-attachments/assets/943dddb4-7776-4193-bcc0-da2432c77b5c) | ![image](https://github.com/user-attachments/assets/0ed78370-1cae-418a-aa94-2b14aa74e69a) |
|![image](https://github.com/user-attachments/assets/3412ef85-354c-46f5-9db0-102878fdac14)|![image](https://github.com/user-attachments/assets/943376ff-006e-4c3a-b307-73639be3a98d) |

*Interactive filters and data visualizations*

### Product Analysis

 | ![image](https://github.com/user-attachments/assets/14ac6f46-b36b-4ce4-aef7-4c09f2f4f332) | ![image](https://github.com/user-attachments/assets/5f026509-c9a7-4510-85af-8487222d8dd9) |
|--------|---------|

*Product performance metrics*

### Top k Products

| ![image](https://github.com/user-attachments/assets/78af8183-61f8-4964-9302-ff5ad4b83d7e) |
|----|

*Top performing products*

### AI Shopping Assistant

| ![image](https://github.com/user-attachments/assets/aff8833f-6f04-4b7c-a4b8-625b0e9652c2) 
|---|


<img src="https://github.com/user-attachments/assets/a92eb3b7-6223-42cc-b6fc-580a8dbccb47" height="100px"/>
<img src="https://github.com/user-attachments/assets/9f66876b-bf5f-4650-ae2d-f315eddd184b" height="100px"/>
<img src="https://github.com/user-attachments/assets/a75050ad-9958-4dab-979f-024c315bb942" height="100px"/>



*LLM-powered product recommendations*

### Classifier attractiveness 
| ![image](https://github.com/user-attachments/assets/998a2911-923c-4002-974d-e8c6cffd4cbc) | ![image](https://github.com/user-attachments/assets/c1df96a0-4216-4a9b-a867-8ce8e551838c) |![image](https://github.com/user-attachments/assets/7442acdf-dd7d-4ead-a174-1d6679541b28) |
|----|---|---|

## 🐳 DevOps Architecture

### Docker Setup
```dockerfile
FROM python:3.9-slim
# ... (rest of Dockerfile) ...
```

### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-app
  namespace: ecommerce
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ecommerce
  template:
    metadata:
      labels:
        app: ecommerce
    spec:
      containers:
      - name: main-app
        image: your-registry/ecommerce-app:latest
        ports:
        - containerPort: 8501
        resources:
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### CI/CD Pipeline (GitHub Actions)
```yaml
name: Deploy to Kubernetes

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Deploy to cluster
        run: |
          kubectl apply -f k8s/deployment.yaml
          kubectl apply -f k8s/service.yaml
```

### Deployment Scripts
```bash
# Build and push Docker image
./build_and_push.sh

# Setup Kubernetes secrets
./setup-k8s-secret.sh

# Monitor application logs
./view-logs.sh
```

## ☁️ Cloud Deployment
```bash
# Start Minikube environment
minikube start

# Deploy application
kubectl apply -f k8s/

# Access application
minikube service ecommerce-service -n ecommerce
```

## 🔄 Kubeflow Pipeline Orchestration

To automate the entire data and model lifecycle, this project implements a Kubeflow Pipeline. This pipeline orchestrates the scraping, data processing, and model training steps in a reproducible and scalable workflow running on top of Kubernetes.

The pipeline defines a Directed Acyclic Graph (DAG) to manage dependencies between tasks:

```mermaid
graph TD
    A[Scrape AliExpress Data] --> B[Train Attractiveness Classifier];
    B --> C{"Model Artifact (.pkl)"};
    B --> D{"Performance Metrics"};
```

### Pipeline Components

Each step in the pipeline is a self-contained, containerized component. Here's an example of the scraper component definition:

```python
# kfp/components/scrape_aliexpress_component.py
from kfp.dsl import component, Output, Dataset

@component(
    base_image="python:3.9",
    packages_to_install=[
        "pandas", "selenium", "webdriver-manager", "beautifulsoup4"
    ],)
def scrape_aliexpress_component(
    max_pages: int,
    output_data: Output[Dataset],):
    """A Kubeflow component to scrape products from AliExpress."""
    # ... (Selenium scraping logic)
    # The final DataFrame is saved to the path provided by Kubeflow
    df.to_csv(output_data.path, index=False)
```

### Pipeline Definition

The components are assembled into a pipeline that defines the execution flow and data handoff.

```python
# kfp/pipeline.py
from kfp import dsl
from components import scrape_aliexpress_component, train_classifier_component

@dsl.pipeline(
    name="E-commerce AI Pipeline",
    description="Scrapes product data and trains an attractiveness model.",
    pipeline_root="gs://your-artifact-store/ecommerce-pipeline" # e.g., GCS or MinIO bucket)
def ecommerce_ai_pipeline(max_pages: int = 5):
    """Defines the workflow of the e-commerce AI pipeline."""

    # Step 1: Scrape data
    scrape_task = scrape_aliexpress_component(
        max_pages=max_pages
    )

    # Step 2: Train model using the output from the scraping task
    train_task = train_classifier_component(
        input_dataset=scrape_task.outputs['output_data']
    )
```

### Compiling and Running

The pipeline is compiled to YAML and can be uploaded directly to the Kubeflow UI to create new runs.

```bash
# Compile the pipeline definition
kfp dsl compile --python-function ecommerce_ai_pipeline pipeline.py --output ecommerce_pipeline.yaml

# Upload the generated .yaml file in the Kubeflow Pipelines dashboard.
```

## 🛠️ Troubleshooting
**Common Issues:**
1. **Missing API Key:**
   ```bash
   export GROQ_API_KEY="valid_key"  # Add to ~/.bashrc for persistence
   ```
2. **Selenium Errors:**
   - Ensure Firefox is installed
   - Update geckodriver
3. **Kubernetes Deployment:**
   ```bash
   kubectl get pods -n ecommerce  # Check pod status
   kubectl describe pod [POD_NAME]  # Inspect errors
   ```



**Note:** For production deployments, consider implementing:
- Horizontal Pod Autoscaling
- Persistent volume for data storage
- HTTPS ingress configuration
- Monitoring with Prometheus/Grafana

## 👥 Authors
- Mohamed Amine BAHASSOU 
- Hodaifa ECHFFANI
