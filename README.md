# URL Shortener - Microservices Application

[![CI](https://github.com/Ali15401/nexskill-devops-b5-final-project/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Ali15401/nexskill-devops-b5-final-project/actions/workflows/ci.yml?query=branch%3Amain)

## Overview

This project is a **production-ready microservices-based URL Shortener** deployed on **AWS** using **Terraform, ECS (EC2 launch type), ALB, RDS, CI/CD,  and Observability with Grafana**.

The system is fully automated: **a simple `git push` triggers build, test, image creation, and zero-downtime deployment**. New versions typically go live within **3–4 minutes**.

---

EC2 Instance: 3 x t3.small
AWS DataBase
AWS Clouwatch used for grafana
Total Resources Terraform Create: 57+

All creditentials are safe in repository secrets

## Architecture

### Microservices

| Service           | Port | Responsibility             |
| ----------------- | ---- | -------------------------- |
| Frontend          | 80   | UI for shortening URLs     |
| Link Service      | 3000 | URL creation & redirection |
| Analytics Service | 4000 | Click tracking & metrics   |
| PostgreSQL (RDS)  | 5432 | Persistent storage         |
| Grafana           | 5000 | Analytics visualization    |

### High-Level Flow

1. User accesses the app via **Application Load Balancer (ALB)**
2. ALB routes traffic using **path-based routing**
3. ECS services process requests
4. Click events are tracked asynchronously
5. Metrics are visualized in **Grafana**

---

## Load Balancer – Path-Based Routing

| Path               | Target Service    |
| ------------------ | ----------------- |
| `/`                | Frontend          |
| `/grafana`         | Grafana           |
| `/api/shorten`     | Link Service      |
| `/api/links/*`     | Link Service      |
| `/api/analytics/*` | Analytics Service |

This allows **multiple services behind a single ALB** without extra DNS or ports.

---

## Networking & Security

* Custom **VPC** with public & private subnets
* **ALB** in public subnets
* **ECS tasks** isolated via security groups
* **RDS PostgreSQL** protected by ECS-only access
* Containers use **awsvpc network mode** (each task gets its own ENI)

---

## Infrastructure as Code (Terraform)

Terraform provisions:

* VPC, subnets, route tables, NAT & IGW
* Application Load Balancer & listener rules
* ECS Cluster (EC2)
* Launch Template & Auto Scaling Group
* ECS Task Definitions & Services
* IAM roles (execution, task, EC2)
* CloudWatch Log Groups

All infrastructure is **fully reproducible** using:

```bash
terraform init
terraform fmt
terraform plan
terraform apply
```

---

## CI/CD Pipeline (GitHub Actions)

### Continuous Integration (CI)

Triggered on **every git push**:

* Build Docker images for all services
* Tag images using commit ci number
* Push images to Docker Hub

### Continuous Deployment (CD – Blue/Green)

* ECS service deploys **new task revision** alongside old one
* ALB gradually routes traffic to new containers
* Old containers are terminated after success
* **Zero downtime deployment**

**Deployment time:** ~3–4 minutes from push to live

---

## 🟦🟩 Blue–Green Deployment

**Why Blue–Green?**

* No service interruption
* Safe rollback
* Production-grade deployment strategy

**Flow:**

1. New image is built & pushed
2. ECS creates new tasks (Green)
3. ALB health checks pass
4. Traffic shifts automatically
5. Old tasks (Blue) are removed

---

## Observability – Grafana

Grafana is integrated with the **Analytics Service**:

* Tracks click counts per short URL
* Real-time metrics
* Used for validating system behavior

This proves the system is **observable, not a black box**.

---

## Debugging & Lessons Learned

Key real-world issues solved:

* ALB path mismatch causing 404s
* Incorrect analytics endpoint routing
* Container-to-container networking misunderstandings
* ECS awsvpc ENI behavior
* Security group port alignment

These were fixed by:

* Correct ALB listener rules
* Centralized service routing via ALB
* Proper environment variable configuration

---

## Future Improvements

* HTTPS with ACM
* WAF for rate limiting
* Autoscaling policies for ECS services
* Prometheus integration
* Canary deployments

---

## Key DevOps Skills Demonstrated

✅ AWS (VPC, ECS, ALB, RDS, IAM)
✅ Terraform (IaC)
✅ Docker & Containers
✅ CI/CD with GitHub Actions
✅ Blue–Green Deployment
✅ Observability (Grafana)
✅ Debugging production issues
