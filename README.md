# 🌤️ Maharashtra Live Weather App — Full CI/CD on EKS

A Flask-based live weather application with a complete CI/CD pipeline from VSCode to browser, deployed on Amazon EKS, accessible at **[weather.rohitkharait.online](http://weather.rohitkharait.online)**.

---

## 🔄 Full CI/CD Pipeline

```
👨‍💻 Developer (VSCode)
     ↓  git push
GitHub Repository (main branch)
     ↓  triggers automatically
GitHub Actions Workflow
     ├── 1. Checkout code
     ├── 2. Build Docker image
     ├── 3. Push image → Docker Hub (krishna112/weather-app)
     ├── 4. Configure AWS credentials
     ├── 5. aws eks update-kubeconfig
     └── 6. kubectl apply -f deployment.yaml
               ↓
     EKS Cluster "nana" (us-west-1)
               ↓
     AWS ELB (internet-facing, port 80)
               ↓
     Route 53 CNAME → weather.rohitkharait.online
               ↓
     🌐 Browser
```

---

## 🏗️ Architecture Stack

```
User Browser
     ↓
weather.rohitkharait.online   (Route 53 CNAME)
     ↓
AWS ELB (port 80)             (AWS Load Balancer Controller)
     ↓
EKS Cluster "nana"            (us-west-1)
     ↓
weather-app pods x4           (Flask on port 5000)
```

---

## 🛠️ Tech Stack

| Component          | Detail                               |
|--------------------|--------------------------------------|
| IDE                | VSCode                               |
| CLI Environment    | AWS CloudShell                       |
| Source Control     | GitHub                               |
| CI/CD              | GitHub Actions                       |
| Container Registry | Docker Hub (`krishna112/weather-app`)|
| Cloud Provider     | AWS                                  |
| Kubernetes         | Amazon EKS (cluster: `nana`)         |
| Region             | `us-west-1`                          |
| App                | Flask (Python) Weather App           |
| Container Image    | `krishna112/weather-app:v6`          |
| Replicas           | 4 pods                               |
| Service Type       | LoadBalancer (AWS ELB)               |
| DNS                | Route 53 (CNAME)                     |
| Domain             | `weather.rohitkharait.online`        |

---

## ⚙️ GitHub Actions Workflow

Workflow file located at `.github/workflows/deploy.yml` in the repository.

---

## 🔐 GitHub Secrets Required

| Secret Name             | Description                   |
|-------------------------|-------------------------------|
| `DOCKER_USERNAME`       | Docker Hub username           |
| `DOCKER_PASSWORD`       | Docker Hub password/token     |
| `AWS_ACCESS_KEY_ID`     | AWS IAM user access key       |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM user secret key       |

> Add at: **GitHub Repo → Settings → Secrets and variables → Actions → New repository secret**

---

## 📦 Kubernetes Manifests

### Deployment

See `deployment.yaml` in the repository.

### Service (LoadBalancer)

See `deployment.yaml` in the repository.

---

## 🚀 One-Time Infrastructure Setup

> All commands below were run in **AWS CloudShell** (no local setup required). Open it at: **AWS Console → CloudShell icon (top navbar)**

### 1. Configure EKS Access
```bash
aws eks update-kubeconfig --region us-west-1 --name nana
```

### 2. Add IAM User to EKS Access Entries
```bash
aws eks create-access-entry \
  --cluster-name nana \
  --principal-arn arn:aws:iam::<account-id>:user/<username> \
  --region us-west-1

aws eks associate-access-policy \
  --cluster-name nana \
  --principal-arn arn:aws:iam::<account-id>:user/<username> \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster \
  --region us-west-1
```

### 3. Tag Subnets for Load Balancer
```bash
VPC_ID=$(aws eks describe-cluster --name nana \
  --region us-west-1 \
  --query "cluster.resourcesVpcConfig.vpcId" \
  --output text)

aws ec2 create-tags \
  --resources <subnet-id-1> <subnet-id-2> \
  --tags \
    Key=kubernetes.io/role/elb,Value=1 \
    Key=kubernetes.io/cluster/nana,Value=shared \
  --region us-west-1
```

### 4. Allow Traffic in Security Group
```bash
SG_ID=$(aws eks describe-cluster --name nana \
  --region us-west-1 \
  --query "cluster.resourcesVpcConfig.clusterSecurityGroupId" \
  --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region us-west-1
```

### 5. Create Route 53 DNS Record

Done manually via **AWS Console → Route 53 → Hosted Zones → Create Record**
- Type: `CNAME`
- Name: `weather.rohitkharait.online`
- Value: ELB DNS name

---

## ⚠️ Issues & Troubleshooting

> 💡 **Tip:** All infrastructure commands were run using **AWS CloudShell** — no local CLI setup needed. CloudShell comes pre-configured with AWS credentials, `kubectl`, and `aws` CLI out of the box.

---

### Issue 1: kubectl Authentication Error
**Error:**
```
couldn't get current server API group list: the server has asked for the client to provide credentials
```
**Cause:** IAM user was not authorized in the EKS cluster.

**Fix:** Add IAM user via EKS Access Entries API (cluster used `API_AND_CONFIG_MAP` auth mode).
```bash
aws eks create-access-entry --cluster-name nana \
  --principal-arn arn:aws:iam::<account-id>:user/EKS \
  --region us-west-1

aws eks associate-access-policy --cluster-name nana \
  --principal-arn arn:aws:iam::<account-id>:user/EKS \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster --region us-west-1
```

---

### Issue 2: `aws-auth` ConfigMap Not Found
**Error:**
```
Error from server (NotFound): configmaps "aws-auth" not found
```
**Cause:** EKS cluster (v1.28+) uses the new **Access Entries API** instead of the legacy `aws-auth` ConfigMap.

**Fix:** Use `aws eks create-access-entry` and `aws eks associate-access-policy` commands instead.

---

### Issue 3: Load Balancer Failed to Build Model
**Error:**
```
Failed build model due to unable to resolve at least one subnet
(0 match VPC and tags: [kubernetes.io/role/internal-elb])
```
**Cause:** Subnets were not tagged for the AWS Load Balancer Controller.

**Fix:** Tag public subnets with:
```bash
aws ec2 create-tags \
  --resources <subnet-id-1> <subnet-id-2> \
  --tags \
    Key=kubernetes.io/role/elb,Value=1 \
    Key=kubernetes.io/cluster/nana,Value=shared
```

---

### Issue 4: ELB Created but App Not Reachable
**Cause:** Service `targetPort` was set to `80` but Flask app runs on port `5000`.

**Fix:** Update service to forward correctly:
```yaml
ports:
  - port: 80          # ELB listens on 80
    targetPort: 5000  # Flask app port
```

Also open Security Group inbound rules for port `80` and NodePort range `30000-32767`.

---

### Issue 5: URL Requires Port Number
**Cause:** Service `port` was set to `5000` so ELB exposed port `5000`, requiring `http://dns:5000`.

**Fix:** Set `port: 80` in the Service so the app is accessible at just `http://dns` without a port.

---

## 🔧 Useful Commands

```bash
# Check pods
kubectl get pods -o wide

# Watch logs
kubectl logs -f deployment/weather-app

# Scale replicas
kubectl scale deployment weather-app --replicas=2

# Check service & ELB
kubectl get svc weather-app

# Check endpoints
kubectl get endpoints weather-app

# Delete everything
kubectl delete -f deployment.yaml
```

---

## 📸 Live App Screenshot

![Maharashtra Live Weather App](./app-screenshot.png)

![Maharashtra Live Weather App 2](./app-screenshot2.png)

> App running live at **weather.rohitkharait.online** showing real-time weather for 9 Maharashtra cities — deployed automatically via GitHub Actions CI/CD pipeline.

---

## ✅ Final Result

| Check                                     | Status |
|-------------------------------------------|--------|
| GitHub Actions CI/CD Pipeline             | ✅     |
| Docker Image pushed to Docker Hub         | ✅     |
| EKS Cluster Running                       | ✅     |
| 4 Pods Running                            | ✅     |
| ELB Provisioned                           | ✅     |
| Route 53 DNS Configured                   | ✅     |
| App Live at `weather.rohitkharait.online` | ✅     |