#!/bin/bash

# Build the Docker images
docker build -t hodaifa485/smart-ecommerce-ml:latest .

# Login to Docker Hub (you'll be prompted for credentials)
docker login

# Push the image to Docker Hub
docker push hodaifa485/smart-ecommerce-ml:latest

echo "Image built and pushed successfully!" 