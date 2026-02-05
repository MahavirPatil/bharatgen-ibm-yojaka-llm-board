

## Prerequisites

Before deploying, ensure you have:

- VPN access to the cluster
- OpenShift access credentials
- `oc` CLI installed and configured
- Required permissions to create:
  - Secrets
  - Deployments
  - Services
  - Routes

---

## Deployment Steps

### Step 1: Login to VPN and OpenShift

**Using CLI:**

```bash
oc login
oc project nextgen
```

**Using UI:**

1. Navigate to the OpenShift Console:
   ```
   https://console-openshift-console.apps.sovereign-ai-stack-cl01.ocp.speedcloud.co.in/
   ```
2. Select the `nextgen` project from the project dropdown

---

### Step 2: Create Secrets for API Keys

Secrets securely store sensitive credentials required by the application.

**Groq API Key Secret:**

```yaml
kind: Secret
metadata:
  name: groq-api-secret
  namespace: nextgen
type: Opaque
stringData:
  GROQ_API_KEY: <your-groq-api-key>
```



**Apply the secrets:**

```bash
oc apply -f secrets.yaml
```

---

### Step 3: Create the Deployment

The Deployment configuration includes:

- **Startup Process:** Downloads application code from GitHub and installs dependencies
- **Environment Variables:** Injected from Secrets
- **Resource Limits:** CPU and memory constraints defined

**Apply the Deployment:**

```bash
oc apply -f deployment.yaml
```

---

### Step 4: Verify Pod Creation

Confirm that the Pods are running successfully:

```bash
oc get pods -n nextgen
```

Expected output:
```
NAME                                              READY   STATUS    RESTARTS   AGE
bharatgen-yojaka-qg-platform-xxxxxxxxx-xxxxx      1/1     Running   0          2m
bharatgen-yojaka-qg-platform-xxxxxxxxx-xxxxx      1/1     Running   0          2m
```

---

### Step 5: Create the Service


**Service Configuration:**
- **Type:** ClusterIP
- **Port:** 8100
- **Target Port:** 8100
- **Selector:** Connects to Deployment Pods via labels

**Apply the Service:**

```bash
oc apply -f service.yaml
```

---

### Step 6: Create the Route for External Access

An OpenShift Route enables external access to the application.

**Route Configuration:**
- **TLS Termination:** Edge
- **Hostname:** Auto-generated
- **Timeout:** 5 minutes (to support long-running LLM inference requests)

**Apply the Route:**

```bash
oc apply -f route.yaml
```

---

### Step 7: Verify Route and Access URL

Verify the Route is created and admitted:

```bash
oc get route bharatgen-yojaka-qg-platform -n nextgen
```

Expected output:
```
NAME                           HOST/PORT                                       PATH   SERVICES                       PORT   TERMINATION   WILDCARD
bharatgen-yojaka-qg-platform   bharatgen-yojaka-qg-platform-nextgen.apps...          bharatgen-yojaka-qg-platform   8100   edge          None
```

Use the `HOST/PORT` value to access the application externally.

---


### Step 8: Restart Deployment After Code Changes

When application code is updated in GitHub, restart the Deployment to pull the latest changes:

```bash
oc rollout restart deployment/bharatgen-yojaka-qg-platform -n nextgen
```

Monitor the rollout status:

```bash
oc rollout status deployment/bharatgen-yojaka-qg-platform -n nextgen
```

---

## UI-Based Deployment (Alternative)

You can also deploy using the OpenShift Console:

1. Click the **"+"** (Import YAML) icon in the top navigation
2. Paste the complete YAML file containing:
   - Secrets
   - Deployment
   - Service
   - Route
3. Click **Create**

This creates all resources in a single operation.

---

## Verification Checklist

Ensure the following before considering the deployment successful:

- [ ] Pods are in `Running` state
- [ ] Service is reachable inside the cluster
- [ ] Route is `Admitted` and accessible externally
- [ ] Application responds to inference requests
- [ ] Environment variables are correctly injected
- [ ] No errors in pod logs

**Check pod logs:**

```bash
oc logs -f <pod-name> -n nextgen
```


---
