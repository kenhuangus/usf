# Securing LLM/GenAI Training Pipelines on Google Cloud

This guide provides a step-by-step walkthrough for implementing robust security controls for Generative AI (GenAI) and Large Language Model (LLM) **training pipelines** running on Google Cloud.

> **Reference:** For detailed instructions on how to find or create all required placeholder values, see [placeholder.md](https://github.com/kenhuangus/usf/blob/main/placeholder.md).

## Table of Contents
1.  [Prerequisites](#prerequisites)
2.  [List of Placeholders](#placeholders-to-replace)
3.  [Step 1: Secure the Cloud Infrastructure](#step-1-secure-the-cloud-infrastructure)
4.  [Step 2: Manage Identity and Access (IAM)](#step-2-manage-identity-and-access-iam)
5.  [Step 3: Configure Firewalls](#step-3-configure-firewalls)
6.  [Step 4: Protect the Training Pipeline](#step-4-protect-the-training-pipeline)
7.  [Step 5: Secure Data Ingestion and Storage](#step-5-secure-data-ingestion-and-storage)
8.  [Step 6: Monitor and Audit Training Activity](#step-6-monitor-and-audit-training-activity)

---

## Prerequisites

Before running these commands, you must have the Google Cloud SDK installed and configured on your local machine.

### For Windows Users:
1.  **Install SDK:** Download and run the installer from the [Google Cloud SDK for Windows documentation](https://cloud.google.com/sdk/docs/install).
2.  **Initialize SDK:** Open a Command Prompt or PowerShell and run `gcloud init`.
3.  **Set Project:** 
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

### For macOS/Linux Users:
1.  **Install SDK:** Follow the instructions for your operating system on the [Google Cloud SDK installation page](https://cloud.google.com/sdk/docs/install).
2.  **Initialize SDK:** Run `gcloud init` in your terminal.
3.  **Set Project:**
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

---

## Placeholders to Replace

Replace the following placeholder variables in the commands below with your own environment's values.

> **How do I get these values?**  
> See [placeholder.md](https://github.com/kenhuangus/usf/blob/main/placeholder.md) for step-by-step instructions and sample commands.

| Placeholder | Description | Example |
|---|---|---|
| `ORGANIZATION_ID` | Your numeric Google Cloud Organization ID. | `123456789012` |
| `ACCESS_POLICY_ID` | The numeric ID of your organization's Access Policy. | `123456789` |
| `PROJECT_ID` | Your alphanumeric Project ID. | `my-genai-project` |
| `PROJECT_NUMBER` | Your numeric Project Number. | `987654321098` |
| `your-genai-data-bucket`| A globally unique name for a Cloud Storage bucket. | `genai-pipeline-data-2023`|
| `YOUR_TRUSTED_IP_RANGE`| The IP range for administrative access. | `203.0.113.0/24` |

---

## Step 1: Secure the Cloud Infrastructure

**Isolate training environments:**  
Use VPC Service Controls to restrict network access and prevent data exfiltration.

```bash
gcloud access-context-manager perimeters create llm-training-perimeter \
  --title="LLM Training Perimeter" \
  --policy=ACCESS_POLICY_ID \
  --resources=projects/PROJECT_NUMBER \
  --restricted-services="vertex.googleapis.com,storage.googleapis.com"
```

---

## Step 2: Manage Identity and Access (IAM)

**Create a dedicated service account for training jobs:**

```bash
gcloud iam service-accounts create llm-training-sa \
  --display-name="LLM Training Service Account"
```

**Grant least-privilege roles:**

```bash
SERVICE_ACCOUNT_EMAIL="llm-training-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectAdmin"

# Deny all other service accounts access to sensitive data buckets
gcloud storage buckets update gs://your-genai-data-bucket \
  --remove-member="allUsers"
```

**Restrict dataset access:**

- Store datasets in private buckets.
- Use IAM Conditions to restrict access only to the required service account.

```bash
gcloud storage buckets add-iam-policy-binding gs://your-genai-data-bucket \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectAdmin" \
  --condition="expression=request.auth.principal==serviceAccount:${SERVICE_ACCOUNT_EMAIL},title=AllowTrainingServiceAccount,description=Only allow LLM training SA"
```

---

## Step 3: Configure Firewalls

**Allow only internal communication for training nodes:**

```bash
gcloud compute firewall-rules create allow-training-internal \
  --network=genai-vpc \
  --action=ALLOW \
  --rules=all \
  --source-ranges=10.0.1.0/24 \
  --direction=INGRESS \
  --priority=1000

gcloud compute firewall-rules create deny-all-training-ingress \
  --network=genai-vpc \
  --action=DENY \
  --rules=all \
  --direction=INGRESS \
  --priority=65534
```

---

## Step 4: Protect the Training Pipeline

### 4.1. **Encrypt Training Data and Model Artifacts**

**Use CMEK for Vertex AI training jobs:**

```bash
# Create a KMS key
gcloud kms keyrings create llm-keyring --location=us-central1
gcloud kms keys create llm-training-key \
  --keyring=llm-keyring \
  --location=us-central1 \
  --purpose=encryption

# Pass CMEK to Vertex AI training job
# Example Python code for training with CMEK

from google.cloud import aiplatform

aiplatform.init(
    project="PROJECT_ID",
    location="us-central1",
    encryption_spec_key_name="projects/PROJECT_ID/locations/us-central1/keyRings/llm-keyring/cryptoKeys/llm-training-key"
)

aiplatform.CustomJob(
    display_name="llm-training-job",
    worker_pool_specs=[...],
    # other params...
    encryption_spec_key_name="projects/PROJECT_ID/locations/us-central1/keyRings/llm-keyring/cryptoKeys/llm-training-key"
).run()
```

### 4.2. **Input and Output Validation**

Validate training data before ingestion to prevent prompt injection or poisoned datasets.

```python
from google.cloud import language_v2

def moderate_text(text: str, project_id: str):
    client = language_v2.LanguageServiceClient()
    document = language_v2.Document(
        content=text,
        type_=language_v2.Document.Type.PLAIN_TEXT,
        language_code="en",
    )
    response = client.moderate_text(document=document)
    for category in response.moderation_categories:
        if category.confidence > 0.8:
            raise ValueError(f"Sensitive content detected: {category.name}")
    return response
```

Use this function to validate samples before adding them to the training set.

---

## Step 5: Secure Data Ingestion and Storage

**Prevent public access to buckets:**

```bash
gcloud storage buckets update gs://your-genai-data-bucket --public-access-prevention
```

**Scan for sensitive data using Cloud DLP:**

```bash
gcloud dlp jobs create inspect \
  --location=global \
  --info-types="PERSON_NAME,EMAIL_ADDRESS,PHONE_NUMBER,CREDIT_CARD_NUMBER" \
  --storage-config-cloud-storage-options-file-set-url="gs://your-genai-data-bucket/*"
```

---

## Step 6: Monitor and Audit Training Activity

**Enable audit logging for Vertex AI and Cloud Storage:**

```bash
gcloud projects get-iam-policy PROJECT_ID > policy.yaml
```

Add or merge the following to `policy.yaml`:

```yaml
auditConfigs:
- auditLogConfigs:
  - logType: DATA_READ
  - logType: DATA_WRITE
  service: aiplatform.googleapis.com
- auditLogConfigs:
  - logType: ADMIN_READ
  - logType: DATA_READ
  - logType: DATA_WRITE
  service: storage.googleapis.com
```

Apply the updated policy:

```bash
gcloud projects set-iam-policy PROJECT_ID policy.yaml
```

**Monitor training jobs via Security Command Center:**

- [Enable Security Command Center](https://cloud.google.com/security-command-center/docs/quickstart)
- Set up alerts for unusual data access, unauthorized artifact downloads, or jobs running from unknown service accounts.

---

## Sample Secure Vertex AI Training Job (Python)

```python
from google.cloud import aiplatform

aiplatform.init(
    project="PROJECT_ID",
    location="us-central1",
    encryption_spec_key_name="projects/PROJECT_ID/locations/us-central1/keyRings/llm-keyring/cryptoKeys/llm-training-key"
)

custom_job = aiplatform.CustomJob(
    display_name="secure-llm-training",
    worker_pool_specs=[...],  # Fill in your training specs here
    encryption_spec_key_name="projects/PROJECT_ID/locations/us-central1/keyRings/llm-keyring/cryptoKeys/llm-training-key",
    service_account="llm-training-sa@PROJECT_ID.iam.gserviceaccount.com"
)

custom_job.run(sync=True)
```

---

## References

- [Google Cloud Vertex AI Security](https://cloud.google.com/vertex-ai/docs/security)
- [CMEK for Vertex AI](https://cloud.google.com/vertex-ai/docs/general/encryption)
- [IAM Conditions](https://cloud.google.com/iam/docs/conditions-overview)
- [Cloud DLP Documentation](https://cloud.google.com/dlp/docs/)
- [Security Command Center](https://cloud.google.com/security-command-center/docs/quickstart)

---

**By following these steps, you can ensure your LLM/GenAI training pipeline on Google Cloud is secured against unauthorized access, data exfiltration, and other threats.**