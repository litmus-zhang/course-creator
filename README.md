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

### Step 1: Deploy the Application
Deploy the project with the command below:

```bash
bash deploy.sh
```

### Step 2: Push to Artifact Registry
Create a repository in Google Artifact Registry and push your image:

```bash
# Create repository
gcloud artifacts repositories create course-creator-repo \
    --repository-format=docker \
    --location=us-east1 \
    --description="Docker repository for Course Creator Agent"

# Authenticate docker
gcloud auth configure-docker us-east1-docker.pkg.dev

# Push image
docker push us-east1-docker.pkg.dev/deepstack-june-2026/course-creator-repo/course-creator:v1
```

### Step 3: Provision a GKE Autopilot Cluster
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

### Step 4: Configure Centralized Sessions (Database)
By default, the agent runs with in-memory sessions. For multi-replica GKE deployments, you must use a centralized database (like Cloud SQL PostgreSQL) so that any GKE pod can handle requests for any active session.

1. Create a Cloud SQL instance:
   ```bash
   gcloud sql instances create course-creator-db --database-version=POSTGRES_15 --tier=db-custom-1-3840 --region=us-east1
   ```
2. Configure the runner in your application (e.g. `app/fast_api_app.py`) to use `DatabaseSessionService` instead of `InMemorySessionService`, pointing to your database connection string.

---

### Step 5: Kubernetes Manifests

Create a deployment file (`deployment.yaml`) defining the deployment, service, ingress, and horizontal pod autoscaler (HPA):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: course-creator
  labels:
    app: course-creator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: course-creator
  template:
    metadata:
      labels:
        app: course-creator
    spec:
      containers:
      - name: course-creator
        image: us-east1-docker.pkg.dev/<PROJECT_ID>/course-creator-repo/course-creator:v1
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-secrets
              key: api-key
---
apiVersion: v1
kind: Service
metadata:
  name: course-creator-service
spec:
  type: ClusterIP
  selector:
    app: course-creator
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: course-creator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: course-creator
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Apply the secret and deploy to GKE:
```bash
# Create GCP Secret
kubectl create secret generic gemini-secrets --from-literal=api-key=YOUR_GEMINI_API_KEY

# Deploy manifests
kubectl apply -f deployment.yaml
```

### Step 6: Test the Agent in Action
Once the pods are running, you can test the deployment locally by port-forwarding the GKE service:

```bash
# Port-forward the service to localhost:8080
kubectl port-forward svc/course-creator-service 8080:80
```

Now, send a test query in another terminal to trigger the multi-agent pipeline (Researcher -> Judge -> Content Builder) and see the streaming output in real-time:

```bash
curl -N -X POST http://127.0.0.1:8080/run_sse \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "course_creator",
    "user_id": "test-user",
    "session_id": "session-1",
    "new_message": {
      "role": "user",
      "parts": [{"text": "Create a course outline for Introduction to Docker"}]
    },
    "streaming": true
  }'
```

---

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

# 3. Delete the Cloud SQL Database Instance
gcloud sql instances delete course-creator-db \
    --project deepstack-june-2026 \
    --quiet

# 4. Delete the Artifact Registry Repository
gcloud artifacts repositories delete course-creator-repo \
    --location us-east1 \
    --project deepstack-june-2026 \
    --quiet
```
