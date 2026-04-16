# SecureCloud Hub — Zero-Trust Azure Secure File Sharing Platform

SecureCloud Hub is a production-style Azure security and cloud engineering project that demonstrates how to build a zero-trust file sharing platform using modern Azure services, identity enforcement, and Infrastructure as Code.

This project is designed to showcase real-world Azure engineering practices suitable for cloud, infrastructure, DevOps, and security roles.

---

# What this project does

SecureCloud Hub implements a secure file sharing workflow that prevents unsafe files from being accessed and ensures strict identity and access control.

Core capabilities:

- Enforces Microsoft sign-in using Microsoft Entra ID and Easy Auth
- Keeps all Azure Blob Storage private (no public blob access)
- Processes uploads through an event-driven malware scanning workflow
- Separates files into trusted and quarantined storage containers
- Issues short-lived read-only SAS URLs only for verified clean files
- Uses managed identity and RBAC instead of storage account keys
- Deploys infrastructure using Terraform
- Uses GitHub Actions with OIDC instead of long-lived secrets
- Logs all operations for audit and security analysis

---

# Why this project exists

SecureCloud Hub is built to demonstrate:

- Secure Azure architecture design
- Identity-first zero-trust security models
- Event-driven cloud workflows
- Infrastructure as Code (Terraform)
- CI/CD with federated authentication
- Real-world audit logging and monitoring

This mirrors patterns used in:

- Azure enterprise environments
- Government and regulated sectors
- Healthcare and finance systems
- Zero-trust cloud architectures

---

# Target Architecture (High-Level)

The platform includes:

- Azure Resource Group
- Azure Storage Account (private only)
- Azure Function App (Python)
- Microsoft Entra ID authentication
- Managed identity with RBAC
- Event Grid-based scanning workflow
- Secure download endpoint
- Key Vault for secrets
- Application Insights and Log Analytics
- GitHub Actions CI/CD pipeline

Detailed diagrams will be added in later phases.

---

# Technology Stack

Infrastructure:

- Terraform
- Azure Resource Manager
- Azure Storage
- Azure Functions
- Azure Event Grid
- Azure Key Vault
- Azure Monitor

Security:

- Microsoft Entra ID
- Managed Identity
- Role-Based Access Control (RBAC)
- User Delegation SAS
- Zero-Trust Design Principles

Development:

- Python
- Azure Functions Runtime
- GitHub Actions
- OpenID Connect (OIDC)

---

# Repository Structure

infra/ → Terraform infrastructure code  
functions/ → Azure Functions application code  
docs/ → Architecture, testing, and troubleshooting documentation  
.github/workflows/ → CI/CD pipelines  

---

# Current Progress

Phase 1 — Project Foundation  
✔ Repository scaffold created  
✔ Terraform baseline defined  
✔ Naming conventions established  
✔ README initialized  

Next:

Phase 2 — Secure Storage Foundation

---

# Design Principles

SecureCloud Hub follows these security-first principles:

- Identity before access
- Least privilege permissions
- Private-by-default storage
- Short-lived credentials
- Full auditability
- Infrastructure as Code
- Zero-trust architecture

---

# Future Enhancements

Later phases will add:

- Private storage containers
- Event-driven malware scanning
- Secure download API
- GitHub Actions CI/CD
- Monitoring dashboards
- KQL security queries
- Production-grade documentation

---

# Portfolio Value

This project demonstrates practical experience in:

- Azure infrastructure design
- Cloud security engineering
- Event-driven architecture
- Terraform-based deployments
- Secure application integration
- Observability and audit logging

It is designed to reflect production-style engineering practices expected in modern Azure environments.

