#!/bin/bash

echo "Getting pod name..."
POD_NAME=$(kubectl get pods -n ecommerce -l app=ecommerce-app -o jsonpath='{.items[0].metadata.name}')

if [ -z "$POD_NAME" ]; then
    echo "No pod found with label app=ecommerce-app"
    exit 1
fi

echo "Found pod: $POD_NAME"
echo "Showing logs (press Ctrl+C to exit)..."
echo "----------------------------------------"
kubectl logs -f -n ecommerce $POD_NAME 