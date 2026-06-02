# Deployment Guide — Healthcare Risk Intelligence Platform
## AWS EKS Production Deployment

---

## Architecture Overview

```
Internet
    │
    ▼
Route 53 (DNS)
    │
    ▼
CloudFront (CDN) ──── S3 (Frontend static files)
    │
    ▼
Application Load Balancer
    │
    ▼
EKS Cluster (us-east-1)
    ├── Namespace: healthrisk
    │   ├── backend (3–10 pods, HPA)
    │   ├── chromadb (1 pod, PVC 50GB)
    │   └── celery-worker (2 pods)
    │
    ├── AWS RDS PostgreSQL 16 (Multi-AZ)
    ├── ElastiCache Redis (cluster mode)
    └── S3 (model artifacts, PDF documents)
```

---

## Prerequisites

Install these tools on your machine:

```bash
# 1. AWS CLI
winget install Amazon.AWSCLI
aws configure   # enter your Access Key, Secret, region=us-east-1

# 2. kubectl
winget install Kubernetes.kubectl

# 3. eksctl
winget install eksctl

# 4. Helm
winget install Helm.Helm

# 5. Docker Desktop
winget install Docker.DockerDesktop
```

---

## STEP 1 — AWS Account Setup

### 1.1 Create IAM User for deployment

```bash
# Create deployment user
aws iam create-user --user-name healthrisk-deployer

# Attach required policies
aws iam attach-user-policy \
  --user-name healthrisk-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

aws iam attach-user-policy \
  --user-name healthrisk-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

aws iam attach-user-policy \
  --user-name healthrisk-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonRDSFullAccess

# Create access keys
aws iam create-access-key --user-name healthrisk-deployer
# Save the AccessKeyId and SecretAccessKey
```

### 1.2 Create ECR Repositories

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1

# Create repos
aws ecr create-repository --repository-name healthrisk-backend  --region $AWS_REGION
aws ecr create-repository --repository-name healthrisk-frontend --region $AWS_REGION

echo "ECR Registry: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
```

---

## STEP 2 — Build & Push Docker Images

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build backend
cd backend
docker build -t healthrisk-backend:1.0.0 .
docker tag healthrisk-backend:1.0.0 \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/healthrisk-backend:1.0.0
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/healthrisk-backend:1.0.0

# Build frontend
cd ../frontend
docker build -t healthrisk-frontend:1.0.0 .
docker tag healthrisk-frontend:1.0.0 \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/healthrisk-frontend:1.0.0
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/healthrisk-frontend:1.0.0
```

---

## STEP 3 — Create RDS PostgreSQL

```bash
# Create subnet group first (use your VPC subnets)
aws rds create-db-subnet-group \
  --db-subnet-group-name healthrisk-subnet-group \
  --db-subnet-group-description "HealthRisk DB Subnet Group" \
  --subnet-ids subnet-xxxxxxxx subnet-yyyyyyyy

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier healthrisk-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16.1 \
  --master-username healthuser \
  --master-user-password "YourSecurePassword123!" \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --backup-retention-period 7 \
  --multi-az \
  --db-subnet-group-name healthrisk-subnet-group \
  --no-publicly-accessible

# Wait for it to be available (~5 min)
aws rds wait db-instance-available --db-instance-identifier healthrisk-db

# Get the endpoint
aws rds describe-db-instances \
  --db-instance-identifier healthrisk-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

---

## STEP 4 — Create ElastiCache Redis

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id healthrisk-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --cache-subnet-group-name healthrisk-subnet-group
```

---

## STEP 5 — Create EKS Cluster

```bash
# Create cluster (takes ~15 minutes)
eksctl create cluster \
  --name healthrisk-cluster \
  --region $AWS_REGION \
  --version 1.29 \
  --nodegroup-name standard-workers \
  --node-type m5.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed \
  --with-oidc \
  --ssh-access \
  --ssh-public-key ~/.ssh/id_rsa.pub

# Verify cluster
kubectl get nodes
# Should show 3 nodes in Ready state
```

---

## STEP 6 — Install Cluster Add-ons

```bash
# NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer

# cert-manager (automatic TLS certificates)
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Get the Load Balancer external IP/hostname
kubectl get svc -n ingress-nginx ingress-nginx-controller
# Note the EXTERNAL-IP — point your DNS to this
```

---

## STEP 7 — Deploy to Kubernetes

### 7.1 Create namespace and secrets

```bash
kubectl apply -f infrastructure/kubernetes/namespace.yaml

# Create all secrets
kubectl create secret generic healthrisk-secrets \
  --namespace healthrisk \
  --from-literal=database-url="postgresql+asyncpg://healthuser:YourSecurePassword123!@YOUR_RDS_ENDPOINT:5432/healthrisk" \
  --from-literal=jwt-secret-key="$(openssl rand -hex 32)" \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  --from-literal=encryption-key="$(openssl rand -hex 32)" \
  --from-literal=redis-url="redis://YOUR_ELASTICACHE_ENDPOINT:6379/0" \
  --from-literal=postgres-user="healthuser" \
  --from-literal=postgres-password="YourSecurePassword123!"
```

### 7.2 Update image references

```bash
# Replace placeholder image names with your ECR URIs
sed -i "s|your-ecr-registry|$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com|g" \
  infrastructure/kubernetes/backend-deployment.yaml
```

### 7.3 Apply all manifests

```bash
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/postgres-deployment.yaml
kubectl apply -f infrastructure/kubernetes/chromadb-deployment.yaml
kubectl apply -f infrastructure/kubernetes/backend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/ingress.yaml

# Watch pods come up
kubectl get pods -n healthrisk -w
```

### 7.4 Run database migrations

```bash
# Run Alembic migrations via a one-off pod
kubectl run alembic-migrate \
  --image=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/healthrisk-backend:1.0.0 \
  --namespace=healthrisk \
  --restart=Never \
  --env="DATABASE_URL=postgresql+asyncpg://healthuser:pass@YOUR_RDS_ENDPOINT:5432/healthrisk" \
  -- alembic upgrade head

kubectl logs alembic-migrate -n healthrisk
kubectl delete pod alembic-migrate -n healthrisk
```

---

## STEP 8 — DNS & TLS Setup

```bash
# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# In Route 53 — create A records:
# api.yourdomain.com  → EXTERNAL-IP of ingress-nginx LoadBalancer
# app.yourdomain.com  → EXTERNAL-IP of ingress-nginx LoadBalancer

# Update ingress.yaml with your real domain, then:
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

---

## STEP 9 — Deploy Monitoring

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus-stack \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword="YourGrafanaPassword" \
  --set grafana.service.type=LoadBalancer

# Access Grafana
kubectl get svc -n monitoring kube-prometheus-stack-grafana
# Open the EXTERNAL-IP in browser, login: admin / YourGrafanaPassword

# Import custom dashboard
kubectl apply -f infrastructure/monitoring/grafana/dashboards/
```

---

## STEP 10 — CI/CD Setup (GitHub Actions)

Add these secrets to your GitHub repository:
**Settings → Secrets → Actions → New repository secret**

| Secret Name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | Your IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | Your IAM user secret key |
| `AWS_ACCOUNT_ID` | Your 12-digit AWS account ID |

Push to `main` branch — the pipeline runs automatically:
```
test → security scan → build → push ECR → deploy EKS → smoke test
```

---

## STEP 11 — Train & Deploy ML Models

```bash
# Train all models (run locally or on an EC2 instance)
cd backend
python -m app.ml.training.train_models --disease all --tune

# Upload trained models to S3
aws s3 cp models/ s3://healthrisk-models/models/ --recursive

# Models are loaded from S3 at pod startup via the MODEL_ARTIFACTS_DIR env var
```

---

## STEP 12 — Fine-Tune Llama 3 (Optional, needs GPU)

```bash
# Launch a GPU EC2 instance (p3.2xlarge = 1x V100, ~$3/hr)
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type p3.2xlarge \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxx

# SSH in and run fine-tuning
pip install -r requirements.txt
python -m app.ml.llm.finetune_llama \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --output ./models/llama3-healthcare \
  --epochs 3 \
  --hf-token YOUR_HUGGINGFACE_TOKEN

# Upload merged model to S3
aws s3 cp models/llama3-healthcare/merged/ \
  s3://healthrisk-models/llama3-healthcare/merged/ --recursive
```

---

## Verification Checklist

```bash
# 1. All pods running
kubectl get pods -n healthrisk
# Expected: backend (3/3), chromadb (1/1)

# 2. Health check
curl https://api.yourdomain.com/health
# Expected: {"status":"healthy","version":"1.0.0","environment":"production"}

# 3. API docs
open https://api.yourdomain.com/docs

# 4. Frontend
open https://app.yourdomain.com
# Login: admin@healthrisk.ai / Admin@123!

# 5. Metrics
open https://grafana.yourdomain.com
```

---

## Cost Estimate (AWS us-east-1)

| Service | Spec | Monthly Cost |
|---------|------|-------------|
| EKS Cluster | Control plane | $73 |
| EC2 Nodes | 3x m5.xlarge | $432 |
| RDS PostgreSQL | db.t3.medium Multi-AZ | $98 |
| ElastiCache Redis | cache.t3.micro | $25 |
| S3 | 100GB storage | $3 |
| CloudFront | 1TB transfer | $85 |
| Route 53 | 1 hosted zone | $1 |
| **Total** | | **~$717/month** |

> Scale down to t3.small nodes for dev/staging to cut costs by 70%.

---

## Rollback

```bash
# Instant rollback to previous version
kubectl rollout undo deployment/healthrisk-backend -n healthrisk

# Check rollout history
kubectl rollout history deployment/healthrisk-backend -n healthrisk

# Rollback to specific revision
kubectl rollout undo deployment/healthrisk-backend --to-revision=2 -n healthrisk
```

---

## Useful Commands

```bash
# View live logs
kubectl logs -f deployment/healthrisk-backend -n healthrisk

# Scale manually
kubectl scale deployment healthrisk-backend --replicas=5 -n healthrisk

# Open a shell in a pod
kubectl exec -it deployment/healthrisk-backend -n healthrisk -- /bin/bash

# Port-forward for local debugging
kubectl port-forward svc/healthrisk-backend-service 8000:80 -n healthrisk

# View HPA status
kubectl get hpa -n healthrisk
```
