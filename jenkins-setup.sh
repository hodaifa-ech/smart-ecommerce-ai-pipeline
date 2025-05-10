#!/bin/bash

# Install required tools in Jenkins container
docker exec jenkins bash -c '
apt-get update && \
apt-get install -y python3-pip && \
pip3 install pytest && \
pip3 install streamlit && \
pip3 install -r /var/jenkins_home/workspace/smart-ecommerce-pipeline/requirements.txt
'

# Configure Minikube environment
docker exec jenkins bash -c '
eval $(minikube docker-env) && \
kubectl config use-context minikube
'

# Create Kubernetes secret for GROQ API key
docker exec jenkins bash -c '
kubectl create secret generic groq-secret \
  --from-literal=api-key="$GROQ_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -
' 