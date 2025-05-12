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

# DevOps & Deployment

This project is designed for robust, scalable deployment using modern DevOps practices:

- **Dockerization:**
  - The application is containerized using Docker. Use `build_and_push.sh` to build and push the image to Docker Hub.

- **Kubernetes Deployment:**
  - The app is deployed on Kubernetes using the manifests in the `k8s/` directory. The deployment exposes the Streamlit app via a LoadBalancer service.
  - Secrets (such as the `GROQ_API_KEY`) are managed securely in Kubernetes using `setup-k8s-secret.sh`.

- **Log Monitoring:**
  - Use `view-logs.sh` to easily stream logs from the running Kubernetes pod for debugging and monitoring.

- **CI/CD Automation:**
  - GitHub Actions workflows (`.github/workflows/`) automate building, pushing, and deploying the Docker image to a local Minikube cluster on every push to `main`.
  - The workflow handles namespace creation, secret management, cleanup of old deployments, and service exposure.

These practices ensure the application is easy to deploy, update, and monitor in both development and production environments.

# Authors 
* Mohamed Amine BAHASSOU
* Hodaifa ECHFFANI
