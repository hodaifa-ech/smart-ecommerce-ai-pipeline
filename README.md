![image](https://github.com/user-attachments/assets/f8cf2774-d0ad-4314-9000-2c8eca4bf1c5)


# Getting Started 
```
git clone https://github.com/hodaifa-ech/smart-ecommerce-ai-pipeline
cd smart-ecommerce-ai-pipeline
pip install -r requirement.txt 
streamlit run main.py
```

**requirements:**
```
export GROQ_API_KEY="api_key"                                    
```

# Scraping
* selenium
* firefox
* csv

# LLM Model 
* LLAMA 3 70B - groq provider

# FrontEnd | Data visualization
* streamlit

# Features 
* dashboard
* top selling products
* chat BOT (for recommendation)

# Screen Shots
## Dashboard (Data Visualization, Filters )
![image](https://github.com/user-attachments/assets/2e8510b3-e980-423f-98c9-e2608027a8d1)

![image](https://github.com/user-attachments/assets/df450a8a-a123-401a-8e6b-700e31360ff0)

## Products (Filters, best selling)
![image](https://github.com/user-attachments/assets/5db40e82-575e-4eb3-a0be-2f443f02502d)

## Chat BOT
![image](https://github.com/user-attachments/assets/a93f477e-6fb5-4f60-8cac-2804c93a4ab3)

# DevOps Architecture

## Docker Setup
The application is containerized using Docker with the following configuration:
```dockerfile
FROM python:3.9-slim
```
- Base image: Python 3.9-slim
- Includes Firefox for Selenium web scraping
- Exposes port 8501 for Streamlit
- Environment variables for API keys
- Optimized layer caching for faster builds

## Kubernetes Deployment
The application is deployed on Kubernetes with the following components:

### Namespace
- `ecommerce`: Isolated environment for the application

### Deployment
- Name: `ecommerce-app`
- Replicas: 1
- Resources:
  - Requests: 512Mi memory, 250m CPU
  - Limits: 1Gi memory, 500m CPU

### Service
- Name: `ecommerce-service`
- Type: NodePort
- Port: 80
- Target Port: 8501

### Secrets
- `groq-secret`: Stores API keys securely
- Managed through `setup-k8s-secret.sh`

## CI/CD Pipeline (GitHub Actions)
The pipeline is triggered on:
- Push to main branch
- Manual workflow dispatch

### Pipeline Steps
1. **Environment Setup**
   - Checkout code
   - Setup Python 3.10
   - Create virtual environment
   - Install dependencies

2. **Deployment**
   - Clean up old deployments
   - Create namespace and secrets
   - Deploy Streamlit application
   - Create service
   - Verify deployment

3. **Post-Deployment**
   - Display access URL
   - Show deployment status
   - Provide logging instructions

## Utility Scripts

### 1. build_and_push.sh
```bash
# Build and push Docker image
./build_and_push.sh
```
- Builds Docker image
- Logs into Docker Hub
- Pushes image to registry

### 2. view-logs.sh
```bash
# View application logs
./view-logs.sh
```
- Automatically finds the correct pod
- Streams logs in real-time
- Easy to monitor application status

### 3. setup-k8s-secret.sh
```bash
# Setup Kubernetes secrets
./setup-k8s-secret.sh
```
- Creates necessary Kubernetes secrets
- Manages API keys securely

## Accessing the Application

After deployment, the application is accessible at:
- Streamlit Dashboard: `http://<minikube-ip>:<nodeport>`

## Monitoring and Maintenance

### Logs
- Use `view-logs.sh` to monitor application logs
- Logs include:
  - Application startup
  - Scraping operations
  - API calls
  - Error tracking

### Resource Monitoring
- Monitor pod status: `kubectl get pods -n ecommerce`
- Check service status: `kubectl get svc -n ecommerce`
- View resource usage: `kubectl top pods -n ecommerce`

### Troubleshooting
1. Check pod status:
   ```bash
   kubectl describe pod <pod-name> -n ecommerce
   ```
2. View pod logs:
   ```bash
   kubectl logs <pod-name> -n ecommerce
   ```
3. Check service endpoints:
   ```bash
   kubectl get endpoints -n ecommerce
   ```

# Authors 
* Mohamed Amine BAHASSOU
* Hodaifa ECHFFANI
