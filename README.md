
# Smart E-commerce AI Pipeline

![Project Banner](https://github.com/user-attachments/assets/f8cf2774-d0ad-4314-9000-2c8eca4bf1c5)

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

## 📸 Application Screenshots

### Dashboard Analytics
![Dashboard](https://github.com/user-attachments/assets/2e8510b3-e980-423f-98c9-e2608027a8d1)
*Interactive filters and data visualizations*

### Product Analysis
![Products](https://github.com/user-attachments/assets/df450a8a-a123-401a-8e6b-700e31360ff0)
*Product performance metrics*

### Best Sellers
![Best Sellers](https://github.com/user-attachments/assets/5db40e82-575e-4eb3-a0be-2f443f02502d)
*Top performing products*

### AI Shopping Assistant
![Chat Bot](https://github.com/user-attachments/assets/a93f477e-6fb5-4f60-8cac-2804c93a4ab3)
*LLM-powered product recommendations*

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

## 👥 Authors
- Mohamed Amine BAHASSOU 
- Hodaifa ECHFFANI

---

**Note:** For production deployments, consider implementing:
- Horizontal Pod Autoscaling
- Persistent volume for data storage
- HTTPS ingress configuration
- Monitoring with Prometheus/Grafana

