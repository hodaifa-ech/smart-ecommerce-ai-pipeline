pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'smart-ecommerce-ai-pipeline'
        DOCKER_TAG = "${BUILD_NUMBER}"
        MINIKUBE_IP = 'minikube'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Test') {
            steps {
                sh 'python -m pytest tests/'
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
            }
        }
        
        stage('Push to Minikube') {
            steps {
                sh """
                    eval \$(minikube docker-env)
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                """
            }
        }
        
        stage('Deploy to Kubeflow') {
            steps {
                sh """
                    kubectl apply -f kubeflow_pipelines/pipeline.yaml
                    kubectl apply -f kubeflow_pipelines/deployment.yaml
                """
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
} 