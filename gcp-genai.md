# Securing LLM/GenAI Pipelines on Google Cloud

This guide provides a step-by-step walkthrough for implementing robust security controls for Generative AI (GenAI) and Large Language Model (LLM) pipelines running on Google Cloud. The instructions use `gcloud` CLI commands that can be run from a local terminal.

## Table of Contents
1.  [Prerequisites](#prerequisites)
2.  [List of Placeholders](#placeholders-to-replace)
3.  [Step 1: Secure the Cloud Infrastructure](#step-1-secure-the-cloud-infrastructure)
4.  [Step 2: Manage Identity and Access (IAM)](#step-2-manage-identity-and-access-iam)
5.  [Step 3: Configure Firewalls](#step-3-configure-firewalls)
6.  [Step 4: Address Pipeline-Specific Risks](#step-4-address-pipeline-specific-risks)

---

## Prerequisites

Before running these commands, you must have the Google Cloud SDK installed and configured on your local machine.

### For Windows Users:
1.  **Install SDK:** Download and run the installer from the [Google Cloud SDK for Windows documentation](https://cloud.google.com/sdk/docs/install-windows).
2.  **Initialize SDK:** Open a Command Prompt or PowerShell and run `gcloud init`. This will guide you through authentication and project setup.
3.  **Set Project:** Ensure you are targeting the correct project by running:
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

### For macOS/Linux Users:
1.  **Install SDK:** Follow the instructions for your operating system on the [Google Cloud SDK installation page](https://cloud.google.com/sdk/docs/install).
2.  **Initialize SDK:** Run `gcloud init` in your terminal.
3.  **Set Project:** Run `gcloud config set project YOUR_PROJECT_ID`.

---

## Placeholders to Replace
You must replace these placeholder variables in the commands below with your own environment's values.

| Placeholder | Description | Example |
|---|---|---|
| `ORGANIZATION_ID` | Your numeric Google Cloud Organization ID. | `123456789012` |
| `ACCESS_POLICY_ID` | The numeric ID of your organization's Access Policy. | `123456789` |
| `PROJECT_ID` | Your alphanumeric Project ID. | `my-genai-project` |
| `PROJECT_NUMBER` | Your numeric Project Number. | `987654321098` |
| `your-genai-data-bucket`| A globally unique name for a Cloud Storage bucket. | `genai-pipeline-data-2023`|
| `YOUR_TRUSTED_IP_RANGE`| The IP range for administrative access (e.g., your office network). | `203.0.113.0/24` |

*You can find your `PROJECT_ID` and `PROJECT_NUMBER` by running `gcloud projects describe $(gcloud config get-value project)`.*

---

## Step 1: Secure the Cloud Infrastructure

### Isolate Resources with VPC Service Controls
1.  **Find your Access Policy ID:**
    ```bash
    gcloud access-context-manager policies list --organization=ORGANIZATION_ID --format="value(name)"
    ```
2.  **Create a Service Perimeter:**
    ```bash
    gcloud access-context-manager perimeters create my-genai-perimeter \
      --title="GenAI Security Perimeter" \
      --policy=ACCESS_POLICY_ID \
      --resources=projects/PROJECT_NUMBER \
      --restricted-services="vertex.googleapis.com,storage.googleapis.com,aiplatform.googleapis.com,containerregistry.googleapis.com"
    ```

### Implement Secure Networking
1.  **Create a VPC Network and Subnet:**
    ```bash
    gcloud compute networks create genai-vpc --subnet-mode=custom

    gcloud compute networks subnets create genai-subnet \
      --network=genai-vpc \
      --range=10.0.1.0/24 \
      --region=us-central1
    ```
2.  **Enable Private Google Access:**
    ```bash
    gcloud compute networks subnets update genai-subnet \
      --region=us-central1 \
      --enable-private-ip-google-access
    ```

### Enforce Customer-Managed Encryption Keys (CMEK)
1.  **Create a KMS Key Ring and Key:**
    ```bash
    gcloud kms keyrings create genai-keyring --location=us-central1

    gcloud kms keys create genai-data-key \
      --keyring=genai-keyring \
      --location=us-central1 \
      --purpose=encryption
    ```
2.  **Grant Service Agents Access to the Key:**
    ```bash
    # Grant permissions to the Vertex AI service agent
    gcloud projects add-iam-policy-binding PROJECT_ID \
        --member serviceAccount:service-PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com \
        --role roles/cloudkms.cryptoKeyEncrypterDecrypter

    # Grant permissions to the Cloud Storage service agent
    gcloud projects add-iam-policy-binding PROJECT_ID \
        --member serviceAccount:service-PROJECT_NUMBER@gs-project-accounts.iam.gserviceaccount.com \
        --role roles/cloudkms.cryptoKeyEncrypterDecrypter
    ```

---

## Step 2: Manage Identity and Access (IAM)

### Use a Dedicated Service Account
1.  **Create the Service Account:**
    ```bash
    gcloud iam service-accounts create genai-pipeline-sa \
      --display-name="Service Account for GenAI Pipeline"
    ```
2.  **Grant Specific, Least-Privilege Roles:**
    ```bash
    SERVICE_ACCOUNT_EMAIL="genai-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com"

    # Grant permission to run Vertex AI jobs
    gcloud projects add-iam-policy-binding PROJECT_ID \
      --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
      --role="roles/aiplatform.user"

    # Grant permission to read/write data in Cloud Storage
    gcloud projects add-iam-policy-binding PROJECT_ID \
      --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
      --role="roles/storage.objectAdmin"
    ```

---

## Step 3: Configure Firewalls

### Create a Default-Deny Ingress Policy
1.  **Allow Internal Traffic (High Priority):**
    ```bash
    gcloud compute firewall-rules create allow-internal-traffic \
        --network=genai-vpc \
        --action=ALLOW \
        --rules=all \
        --source-ranges=10.0.1.0/24 \
        --direction=INGRESS \
        --priority=1000
    ```
2.  **Deny All Other Ingress (Low Priority):**
    ```bash
    gcloud compute firewall-rules create deny-all-ingress \
      --network=genai-vpc \
      --action=DENY \
      --rules=all \
      --direction=INGRESS \
      --priority=65534
    ```

---

## Step 4: Address Pipeline-Specific Risks

### Secure Data Artifacts
1.  **Enforce Public Access Prevention on Buckets:**
    ```bash
    gcloud storage buckets update gs://your-genai-data-bucket --public-access-prevention
    ```
2.  **Scan for Sensitive Data with Cloud DLP:**
    ```bash
    gcloud dlp jobs create inspect \
      --location=global \
      --info-types="PERSON_NAME,EMAIL_ADDRESS,PHONE_NUMBER" \
      --storage-config-cloud-storage-options-file-set-url="gs://your-genai-data-bucket/*"
    ```

### Enable Audit Logging
1.  **Get the Current IAM Policy:**
    ```bash
    gcloud projects get-iam-policy PROJECT_ID > policy.yaml
    ```
2.  **Edit `policy.yaml`:** Open the file and add the following `auditConfigs` section, or merge it with your existing one.
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
3.  **Apply the Updated Policy:**
    ```bash
    gcloud projects set-iam-policy PROJECT_ID policy.yaml
    ```
### Input and Output Validation (Code)
To prevent prompt injection and moderate content, use APIs to validate inputs and outputs. Here is a Python example using the Cloud Natural Language API.

1.  **Install the client library:**
    ```bash
    pip install google-cloud-language
    ```
2.  **Use this function in your application:**
    ```python
    from google.cloud import language_v2

    def moderate_text(text: str, project_id: str) -> language_v2.ModerateTextResponse:
        """Moderates the input text."""
        client = language_v2.LanguageServiceClient()
        document = language_v2.Document(
            content=text,
            type_=language_v2.Document.Type.PLAIN_TEXT,
            language_code="en",
        )
        response = client.moderate_text(document=document)

        print(f"Text: {text}")
        for category in response.moderation_categories:
            print(f"  Category: {category.name}, Confidence: {category.confidence:.2f}")

        return response

````
