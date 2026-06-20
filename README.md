# course-creator

[![Fork Repository](https://img.shields.io/badge/Fork-Repository-blue?style=for-the-badge&logo=github)](https://github.com/litmus-zhang/course-creator/fork)

Agent generated with `agents-cli` version `0.5.0`

Scan QR Code below to follow along:

![QR Code](./QR-Code.png)

## Project Structure

```
course-creator/
├── app/         # Core agent code
│   ├── agent.py               # Main agent logic
│   └── app_utils/             # App utilities and helpers
├── tests/                     # Unit, integration, and load tests
├── GEMINI.md                  # AI-assisted development guide
└── pyproject.toml             # Project dependencies
```

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **Kubectl** [Install](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- **gke-gcloud-auth-plugin** [Install](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl#install_plugin)


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `agent.py` and test with `agents-cli playground` - it auto-reloads on save.



## Deployment to Google Kubernetes Engine (GKE)

This guide walks you through building, configuring, and deploying this ADK-based multi-agent system to a production GKE cluster, optimized for high scalability.

### Prerequisites
1. **Google Cloud SDK** installed and authenticated: `gcloud auth login`
2. **Docker** or a compatible container builder installed locally.
3. A GCP Project with billing enabled.
4. **Enable APIs and IAM Permissions**: Run the following single command to enable required APIs and grant roles (Kubernetes Developer, Storage Object Viewer, Artifact Registry Create on Push Writer, Logs Writer) to your Compute Engine default service account:


---

### Step 0: Connect to your Google Cloud project
Before you deploy your ADK project, you must connect to Google Cloud and your project. After logging into your Google Cloud account, you should verify that your deployment target project is visible from your account and that it is configured as your current project.

To connect to Google Cloud and list your project:

In a terminal window of your development environment, login to your Google Cloud account:

`gcloud auth application-default login`

Create a new project:

`gcloud projects create deepstack-june-2026 --name="deepstack-june-2026"`

Set your target project using the Google Cloud Project ID:

```bash
gcloud auth application-default set-quota-project deepstack-june-2026

gcloud config set project deepstack-june-2026

```

Verify your Google Cloud target project is set:

```bash
gcloud config get-value project
```

Ensure billing is enabled for your project by listing your billing accounts and linking your project to the active billing account:

```bash
# List billing accounts to get the BILLING_ACCOUNT_ID
gcloud billing accounts list

# Link the project to the billing account
gcloud billing projects link deepstack-june-2026 --billing-account=YOUR_BILLING_ACCOUNT_ID
```

Enable the required APIs and configure IAM permissions:

```bash
gcloud services enable container.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com && \
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)") && \
for role in roles/container.developer roles/storage.objectViewer roles/artifactregistry.createOnPushWriter roles/logging.logWriter; do \
  gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="${role}"; \
done
```


Once you have successfully connected to Google Cloud and set your Cloud Project ID, you are ready to deploy your ADK project files to GKE.

### Step 1: Provision a GKE Autopilot Cluster
GKE Autopilot is recommended for most workloads as it manages pod provisioning, node scaling, and security defaults automatically:

```bash

gcloud container clusters create-auto course-creator-cluster \
    --region us-east1 \
    --project deepstack-june-2026
```
Get credentials for your new cluster:
```bash
gcloud container clusters get-credentials course-creator-cluster --region us-east1
```

### Step : Deploy the Application 
Deploy the project with the command below:

```bash
bash deploy.sh
```

### Verifying Your Deployment¶
Since we used `adk deploy gke`, we will verify the deployment using `kubectl`:

Check the Pods: Ensure your agent's pods are in the Running state.

```bash
kubectl get pods
```
You should see output like `adk-default-service-name-xxxx-xxxx ... 1/1 Running in the default namespace.`.

Find the External IP: Get the public IP address for your agent's service.

```bash
kubectl get service
```
NAME                       TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
adk-default-service-name   LoadBalancer   34.118.228.70   34.63.153.253   80:32581/TCP   5d20h

We can navigate to the external IP `http://YOUR_EXTERNAL_IP` and interact with the agent via UI.

## 📈 Scaling to 10,000 Users: What Breaks First?

If this AI system suddenly serves **10,000 concurrent users tomorrow**, here is what breaks first and how we mitigate it on GKE:

### 1. LLM API Rate Limits (The Immediate Bottleneck)
*   **What breaks**: Gemini API standard pay-as-you-go/free tier limits (RPM/TPM) will instantly trigger `429 RESOURCE_EXHAUSTED` errors. Because this is a multi-agent system, a single user request invokes the LLM multiple times (Researcher search -> Judge critique -> Content Builder layout).
*   **Mitigation**:
    *   **Vertex AI Provisioned Throughput**: Transition from pay-as-you-go to Vertex AI with provisioned throughput to guarantee dedicated QPS.
    *   **Context Caching**: Enable ADK's built-in `ContextCacheConfig` in `App` to cache the system instructions and schemas, reducing duplicate prompt token usage by up to 90%.
    *   **Exponential Backoff**: ADK uses `tenacity` for retries, but we should configure an asynchronous message queue (e.g. Google Cloud Tasks or RabbitMQ on GKE) in front of the API endpoints to buffer traffic bursts.

### 2. In-Memory Session Storage (Data Loss)
*   **What breaks**: The default `InMemorySessionService` stores active session states and history in the RAM of the specific pod that received the request. With multiple pods running behind a GKE Load Balancer, subsequent user requests will hit different pods and throw "Session Not Found" errors. Furthermore, 10,000 sessions will cause pods to exceed memory limits and trigger OOM-Kills.
*   **Mitigation**:
    *   Switch to `DatabaseSessionService` using a high-performance **Cloud SQL PostgreSQL** database with connection pooling (e.g., PgBouncer) to persist session history and state globally.

### 3. Container Startup Latency (Scaling Lag)
*   **What breaks**: When the GKE Horizontal Pod Autoscaler (HPA) triggers scaling due to CPU load, Python container cold starts can take 15+ seconds (loading package runtimes like PyArrow, gRPC, and Google SDKs). During this time, incoming requests pile up, causing gateway timeouts.
*   **Mitigation**:
    *   Set GKE `minReplicas` to a safe baseline (e.g., 5-10 pods) based on traffic patterns.
    *   Enable GKE **Container Image Streaming** to pull container layers on-demand, reducing cold starts to under 3 seconds.

### 4. Database Connection Pool Exhaustion
*   **What breaks**: With up to 20 GKE pods scaling out, each holding database connections for session lookups, the PostgreSQL instance will run out of connection slots, crashing the backend.
*   **Mitigation**:
    *   Utilize **Cloud SQL Auth Proxy** sidecars in your GKE pods and place **PgBouncer** in front of Cloud SQL to handle thousands of transient client connections efficiently.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.

---

## 🧹 Teardown & Clean Up

To avoid ongoing charges for your cluster and cloud resources, tear down the environment by running the following commands:

```bash
# 1. Delete Kubernetes resources (Deployment, Service, HPA, Secrets)
kubectl delete -f deployment.yaml
kubectl delete secret gemini-secrets

# 2. Delete the GKE Autopilot Cluster
gcloud container clusters delete course-creator-cluster \
    --region us-east1 \
    --project deepstack-june-2026 \
    --quiet
```
