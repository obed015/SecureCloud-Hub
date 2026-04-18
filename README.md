# SecureCloud Hub — Zero-Trust Azure Secure File Sharing Platform

SecureCloud Hub is a production-style Azure cloud security project that demonstrates how to build a zero-trust file sharing platform using Microsoft Entra ID, Azure Functions on Flex Consumption, private Blob Storage, Event Grid, managed identity, Terraform, and GitHub Actions with OIDC.

It is designed to showcase practical Azure engineering skills for cloud, infrastructure, DevOps, and security-focused roles.

---

## What this project does

SecureCloud Hub implements a secure file sharing workflow that prevents unsafe files from being accessed and enforces strict identity and access control.

### Core capabilities

- Enforces Microsoft sign-in using Microsoft Entra ID and App Service Easy Auth
- Keeps all Azure Blob Storage private with no public blob access
- Processes uploads through an event-driven malware scanning workflow
- Separates files into trusted and quarantined storage containers
- Issues short-lived read-only SAS URLs only for verified clean files
- Uses managed identity and RBAC instead of storage account keys
- Deploys infrastructure using Terraform
- Uses GitHub Actions with OIDC instead of long-lived client secrets
- Logs runtime activity for audit, monitoring, and troubleshooting
- Supports KQL-based investigation using Log Analytics and Application Insights

---

## Why this project exists

SecureCloud Hub was built to demonstrate real-world Azure engineering practices rather than tutorial-style shortcuts.

It is intended to show:

- secure Azure architecture design
- identity-first zero-trust access control
- event-driven cloud workflows
- Infrastructure as Code with Terraform
- CI/CD using federated authentication
- observability, auditability, and KQL-based investigation
- practical troubleshooting of real Azure platform issues

This mirrors patterns used in:

- Azure enterprise environments
- regulated sectors
- security-sensitive workloads
- zero-trust cloud architectures

---

## What has been built

SecureCloud Hub currently includes:

- Azure Resource Group
- Azure Storage Account with private containers only
- `incoming-raw` container for untrusted uploads
- `safe-files` container for clean files
- `quarantine` container for infected files
- Azure Function App on **Flex Consumption**
- Microsoft Entra ID authentication via Easy Auth
- System-assigned managed identity
- RBAC-based storage access
- Event Grid system topic and subscription
- `scan_function` triggered by BlobCreated events
- `download_function` for secure file access flow
- Application Insights and Log Analytics integration
- GitHub Actions pipeline foundation using OIDC
- Terraform-managed infrastructure
- Working malware pipeline validated with:
  - clean file routing to `safe-files`
  - EICAR test file routing to `quarantine`

---

## High-level architecture

```text
GitHub Actions (OIDC)
        ↓
Terraform IaC
        ↓
┌─────────────────────────────────────────────────────┐
│            rg-securecloud-dev-ukwest                │
│                                                     │
│  User → Entra ID / Easy Auth                        │
│       → Azure Functions (Flex Consumption)          │
│                                                     │
│  Upload → incoming-raw                              │
│         → Event Grid (BlobCreated)                  │
│         → scan_function                             │
│         → safe-files (clean)                        │
│         → quarantine (infected)                     │
│                                                     │
│  Download request → download_function               │
│                   → identity validation             │
│                   → clean-file verification         │
│                   → short-lived read-only SAS       │
│                   → client downloads from Blob      │
└─────────────────────────────────────────────────────┘

## Security Decisions

| Decision | Why |
|---------|-----|
| Private blob containers | Prevents anonymous access |
| Separate containers | Enforces trust boundaries |
| Managed identity + RBAC | Removes connection strings |
| Easy Auth with Entra ID | Blocks unauthenticated access |
| Event Grid filtering | Prevents infinite loops |
| User delegation SAS | Short-lived secure downloads |
| OIDC CI/CD | Removes long-lived secrets |
| Log Analytics + KQL | Enables auditing and investigation |

## Key Workflows

### Upload and Scan

1. File uploaded to `incoming-raw`
2. Event Grid triggers `scan_function`
3. File scanned
4. Clean → `safe-files`
5. Infected → `quarantine`
6. Metadata applied
7. Original deleted

### Secure Download

1. Authenticated user requests file
2. Identity validated via Easy Auth
3. `scanStatus=clean` verified
4. Short-lived SAS issued
5. Client downloads directly

## Validation Completed

The platform was tested using both clean and EICAR test files.

Clean file:
- moved to `safe-files`
- tagged with `scanStatus=clean`

Infected file:
- moved to `quarantine`
- tagged with `scanStatus=infected`

## Troubleshooting Highlights

During development, several real-world issues were resolved:

- Migrated Function App from Linux Consumption to Flex Consumption
- Rebuilt Event Grid subscription after migration
- Fixed delivery failures caused by Easy Auth blocking webhook traffic
- Excluded Event Grid runtime paths from authentication
- Improved logging for scan workflow diagnostics
- Verified delivery using Event Grid metrics and Application Insights