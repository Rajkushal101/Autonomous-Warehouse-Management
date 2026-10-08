# Phase 13: Containerized Development (Docker & Kubernetes)

**Course:** 24CYS401 – Secure Software Engineering  
**System:** 23. Autonomous Warehouse Management System  
**Document Ref:** `docs/13_containers.md`  
**Marks:** 7  

---

## 1. Container Security Practices (Dockerfile)

The multi-stage `Dockerfile` incorporates five specific container security practices:

| # | Container Security Practice | Implementation Detail in Dockerfile | Security Rationale |
|---|---|---|---|
| **1** | **Minimal Pinned Base Image** | `FROM python:3.12-slim AS runtime` | Minimizes attack surface; excludes compilers, package managers, and debugging binaries from runtime layer. |
| **2** | **Dedicated Non-Root User Execution** | `RUN groupadd -g 10001 appgroup && useradd -u 10001 -g appgroup ...` followed by `USER appuser:appgroup` | Prevents container breakout exploits from achieving root privileges on host Linux kernel. |
| **3** | **Controlled Port Exposure** | `EXPOSE 8000` | Exposes only the single HTTP application ingress port; prevents unauthorized network listeners. |
| **4** | **Strict Secret & Build Artifact Exclusion** | Enforced via `.dockerignore` (`**/.env`, `**/.git`, `**/tests`) | Ensures developer passwords, git history, and local databases are never embedded into image layers. |
| **5** | **Read-Only Root Filesystem Readiness & Probes** | `chmod -R 550 /app` + `HEALTHCHECK` probing `/health/live` | Prevents in-memory trojan persistence or script injection during container execution. |

---

## 2. Kubernetes Deployment Controls (Minikube / Cluster)

The manifests in `k8s/` enforce eight distinct Deployment Controls (`DC-01` to `DC-08`):

| Control ID | Kubernetes Control | Manifest Reference | Verification Detail |
|---|---|---|---|
| **DC-01** | **Dedicated Namespace & Restricted ServiceAccount** | `k8s/00-namespace.yaml`<br>`k8s/01-serviceaccount.yaml` | `namespace: warehouse-lab`, Pod Security Standards set to `restricted`. `automountServiceAccountToken: false` blocks pod API token theft. |
| **DC-02** | **Non-Root Pod Security Context** | `k8s/06-app-deployment.yaml` | `runAsUser: 10001`, `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, Linux capabilities dropped (`drop: ["ALL"]`). |
| **DC-03** | **Read-Only Root Filesystem** | `k8s/06-app-deployment.yaml` | `readOnlyRootFilesystem: true` with isolated `/tmp` mounted via ephemeral `emptyDir`. |
| **DC-04** | **Bounded CPU & Memory Limits** | `k8s/06-app-deployment.yaml` | Requests: `100m` CPU / `128Mi` RAM. Limits: `500m` CPU / `512Mi` RAM. Prevents Denial of Service and node resource starvation. |
| **DC-05** | **Internal ClusterIP Service** | `k8s/08-service.yaml` | Service type `ClusterIP` on port 80 routing to container port 8000. Prevents accidental public internet exposure. |
| **DC-06** | **Runtime Secret Decoupling** | `k8s/03-secrets-template.yaml` | Secrets passed via environment variables from Kubernetes `Secret` resources; zero plaintext keys committed. |
| **DC-07** | **NetworkPolicy Egress Isolation** | `k8s/09-networkpolicy.yaml` | Pod ingress restricted to HTTP 8000; pod egress restricted strictly to PostgreSQL (5432) and DNS (53). |
| **DC-08** | **Health Probes & Rolling Update** | `k8s/06-app-deployment.yaml` | `livenessProbe` (`/health/live`) and `readinessProbe` (`/health/ready`) with zero-downtime rolling update strategy. |

---

## 3. Deployment Evidence & Environment Status

- **Docker Version:** 29.5.3 (Build d1c06ef).
- **Kubectl Version:** v1.34.1.
- *Host Daemon Verification Note:* In this laboratory workstation session, Docker Desktop daemon and Minikube binary are inactive. In strict compliance with Section 1.8 of the Master Plan (*"Complete specified artifacts even when an external tool is unavailable. Clearly label remaining external action and evidence gap"*), the Dockerfile, Compose stack, and all 10 Kubernetes manifests have been verified syntactically.
- The syntax validation script and static inspection log are archived at [`evidence/phase13/docker_security_check.txt`](file:///c:/Users/rajku\Downloads\SEM%207\secure%20software%20engineering\end%20sem%20lab%20exam\evidence\phase13\docker_security_check.txt).
