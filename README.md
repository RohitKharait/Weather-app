# 🌤️ Maharashtra Live Weather App

> A Flask-based live weather application deployed on Amazon EKS with a complete CI/CD pipeline — from VSCode to browser.

🌐 **Live at:** [weather.rohitkharait.online](http://weather.rohitkharait.online)

---

## 📸 Live App

![Maharashtra Live Weather App](./app-screenshot.png)

![Maharashtra Live Weather App 2](./app-screenshot2.png)

---

## 🔄 CI/CD Pipeline

Every code change pushed to the `main` branch on GitHub automatically triggers a GitHub Actions workflow that builds the Docker image, pushes it to Docker Hub, and deploys the latest version to the EKS cluster — no manual steps needed.

```
👨‍💻 VSCode  →  GitHub (main branch)  →  GitHub Actions
      →  Docker Hub  →  EKS Cluster  →  AWS ELB
      →  Route 53  →  🌐 Browser
```

---

## 🏗️ Architecture

Traffic flows from the user's browser through a Route 53 CNAME record to an AWS Elastic Load Balancer, which distributes requests across 4 Flask app pods running inside the EKS cluster.

```
Browser (HTTPS)
  → weather.rohitkharait.online  (Route 53 CNAME)
  → AWS ELB  (port 443 — SSL terminated here via ACM)
  → EKS Cluster "nana"  (us-west-1)
  → Flask App Pods x4  (port 5000 — plain HTTP internally)
```

---

## 🛠️ Tech Stack

| Layer              | Technology                           |
|--------------------|--------------------------------------|
| IDE                | VSCode                               |
| CLI Environment    | AWS CloudShell                       |
| Source Control     | GitHub                               |
| CI/CD              | GitHub Actions                       |
| Container Registry | Docker Hub                           |
| Container Image    | `krishna112/weather-app:v6`          |
| Cloud Provider     | AWS                                  |
| Kubernetes         | Amazon EKS — cluster `nana`          |
| Region             | us-west-1                            |
| Application        | Flask (Python)                       |
| Replicas           | 4 pods                               |
| Load Balancer      | AWS ELB (internet-facing)            |
| DNS                | AWS Route 53 (CNAME)                 |
| SSL Certificate    | AWS ACM (Amazon Certificate Manager) |
| Security Scanning  | Trivy (image vulnerability scanner)  |
| Domain             | weather.rohitkharait.online          |

---

## ⚙️ GitHub Actions Workflow

The workflow file lives at `.github/workflows/deploy.yml`. It runs on every push to `main` and performs these steps in order:

1. Checks out the latest code from the repository
2. Logs into Docker Hub using stored secrets
3. Builds a fresh Docker image from the latest code
4. **Runs Trivy security scan** on the image — pipeline fails if CRITICAL or HIGH vulnerabilities are found
5. Pushes the image to Docker Hub only if the scan passes
6. Configures AWS credentials for EKS access
7. Updates kubeconfig to connect kubectl to the cluster
8. Applies the Kubernetes manifests to deploy the new version

---

## 🔐 GitHub Secrets

These four secrets must be added to the repository for the workflow to function:

| Secret Name             | Purpose                       |
|-------------------------|-------------------------------|
| `DOCKER_USERNAME`       | Docker Hub login              |
| `DOCKER_PASSWORD`       | Docker Hub password or token  |
| `AWS_ACCESS_KEY_ID`     | AWS IAM access key            |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key            |

> **Where to add:** GitHub Repo → Settings → Secrets and variables → Actions → New repository secret


---

## 🔍 Trivy Image Security Scanning

Trivy is an open-source vulnerability scanner by Aqua Security. It is integrated into the GitHub Actions pipeline to scan the Docker image for known vulnerabilities before it is pushed to Docker Hub or deployed to EKS.

The scan checks for vulnerabilities rated **HIGH** and **CRITICAL** across the OS packages and Python dependencies inside the image. If any are found, the pipeline stops immediately and the image is not deployed — ensuring only clean, safe images reach production.

**How it works in the pipeline:**

- Trivy scans the locally built image before it is pushed anywhere
- Results are displayed in a table format in the GitHub Actions log
- Pipeline fails automatically on HIGH or CRITICAL findings
- Push to Docker Hub and deploy to EKS only happen after a clean scan

---

## 📦 Kubernetes Manifests

Manifests are defined in `deployment.yaml` at the repository root.

**Deployment** — Runs 4 replicas of the Flask weather app. Each pod pulls the latest image from Docker Hub and listens on port 5000.

**Service** — A LoadBalancer type service that tells AWS to provision an internet-facing ELB. It listens on port 80 (HTTP) and port 443 (HTTPS). SSL is terminated at the ELB using the ACM certificate — traffic is then forwarded internally to the Flask app on port 5000 as plain HTTP.

---

## 🚀 One-Time Infrastructure Setup

All setup was done through **AWS CloudShell** — no local installation required. CloudShell is a browser-based terminal inside the AWS Console that comes pre-loaded with the AWS CLI and kubectl.

**1. Connect kubectl to EKS**
Used the AWS CLI to update the local kubeconfig file so kubectl could authenticate and communicate with the `nana` cluster in `us-west-1`.

**2. Grant IAM User Access to EKS**
The IAM user `EKS` was added to the cluster using the EKS Access Entries API and assigned the `AmazonEKSClusterAdminPolicy` at the cluster level. This grants full admin access to manage workloads.

**3. Tag Subnets for the Load Balancer**
The two public subnets in the VPC were tagged so the AWS Load Balancer Controller could discover them automatically when creating the ELB.

**4. Open Security Group Port**
An inbound rule was added to the cluster's security group to allow HTTP traffic on port 80 from the internet.

**5. Request SSL Certificate via ACM**
An SSL certificate was requested through AWS Certificate Manager (ACM) for the domain `weather.rohitkharait.online`. DNS validation was used — ACM provided a CNAME record which was added to Route 53, and within a few minutes the certificate status changed to Issued. The certificate ARN was then added to the Kubernetes Service annotations so the ELB could use it for HTTPS termination.

**6. Create DNS Record**
A CNAME record was manually created in Route 53 pointing `weather.rohitkharait.online` to the ELB DNS name. This allows users to access the app using a clean domain name instead of the raw ELB URL.

---

## ⚠️ Issues Faced & How They Were Fixed

### Issue 1 — kubectl Could Not Authenticate
The IAM user running kubectl was not recognized by the EKS cluster, so every command was rejected with a credentials error. This happened because EKS clusters on version 1.28+ no longer use the old `aws-auth` ConfigMap for access control. Instead they use the new Access Entries API. The fix was to add the IAM user through that API and attach the cluster admin policy.

---

### Issue 2 — aws-auth ConfigMap Was Missing
When trying to manually edit the `aws-auth` ConfigMap to grant access, Kubernetes returned a "not found" error. This confirmed that the cluster was using the newer Access Entries system exclusively, so the ConfigMap approach was abandoned entirely.

---

### Issue 3 — Load Balancer Could Not Find Subnets
After applying the Service manifest, the AWS Load Balancer Controller failed to create the ELB because it could not find any subnets matching the required tags. The public subnets in the VPC were missing the `kubernetes.io/role/elb` and `kubernetes.io/cluster/nana` tags. Once those tags were added, the ELB was provisioned successfully.

---

### Issue 4 — App Was Unreachable Through the ELB
The ELB was created and appeared healthy, but the app returned no response. The cause was a port mismatch — the Service was forwarding traffic to port 80 on the pods, but the Flask app was actually listening on port 5000. Updating `targetPort` to 5000 in the Service manifest resolved it.

---

### Issue 5 — Domain Required a Port Number in the URL
Initially the Service was configured with `port: 5000`, which meant the ELB exposed port 5000 and users had to type `:5000` in the URL. Changing the Service `port` to `80` made the ELB listen on the standard HTTP port, so the app became accessible at just the plain domain name with no port.

---

## ✅ Final Result

| What Was Achieved                         | Status |
|-------------------------------------------|--------|
| CI/CD pipeline via GitHub Actions         | ✅     |
| Trivy security scan on every build        | ✅     |
| Docker image auto-built and pushed        | ✅     |
| EKS cluster running with 4 pods           | ✅     |
| AWS ELB with port 80 and 443              | ✅     |
| SSL certificate via ACM                   | ✅     |
| Route 53 DNS configured                   | ✅     |
| App live at weather.rohitkharait.online   | ✅     |
