#!/bin/bash

# Create the secret in Kubernetes
kubectl create secret generic groq-secret \
  --namespace ecommerce \
  --from-literal=api-key="$GROQ_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f - 