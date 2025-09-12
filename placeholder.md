# How to Get or Create Placeholder Values for Google Cloud Security

## Using a Personal Google Account (No Organization ID)

If you are using a personal Google Cloud account and do **not** have an Organization ID, you can still complete most security setup steps for your project. Some steps and placeholders (like `ORGANIZATION_ID` or `ACCESS_POLICY_ID`) are only relevant for users in an organization.

### What You Need

For most commands, you only need:

| Placeholder                | Description                              | Example                 |
|----------------------------|------------------------------------------|-------------------------|
| `PROJECT_ID`               | Your Google Cloud project ID             | `my-genai-project`      |
| `PROJECT_NUMBER`           | Your Google Cloud project number         | `987654321098`          |
| `your-genai-data-bucket`   | Unique Cloud Storage bucket name         | `genai-pipeline-data-23`|
| `YOUR_TRUSTED_IP_RANGE`    | Trusted IP ranges for network rules      | `203.0.113.0/24`        |

### How to Get Project ID and Project Number

```bash
# List all your projects
gcloud projects list

# Set your project for future commands
gcloud config set project YOUR_PROJECT_ID

# Show your project number
gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"
```

### What to Do When a Command Asks for ORGANIZATION_ID or ACCESS_POLICY_ID

- **Skip or modify steps that require these values.**
- For VPC Service Controls or organizational policies, you will not be able to apply these controls as a personal account. You can skip perimeter-related steps.
- Most IAM, bucket, and KMS commands will work as shown.

### Example: Skipping Perimeter Creation

If you see a command like:
```bash
gcloud access-context-manager perimeters create llm-training-perimeter \
  --title="LLM Training Perimeter" \
  --policy=ACCESS_POLICY_ID \
  --resources=projects/PROJECT_NUMBER \
  --restricted-services="vertex.googleapis.com,storage.googleapis.com"
```
**You can skip this step for personal accounts.**

### Example: Creating VPC and Firewall Setup for Personal Accounts

For firewalls and network rules, personal accounts can create custom VPCs:

```bash
# Create a VPC network
gcloud compute networks create genai-vpc --subnet-mode=custom

# Then create firewall rules as shown in the guide
```

### The Rest of the Guide

Continue to follow the guide using your project-specific values. Most security practices (IAM, buckets, KMS, audit logging) apply to personal accounts.

---

## Using an Organizational Account

If you are in a Google Cloud Organization (usually business, education, or enterprise), you will need additional values:

| Placeholder         | Description                                | Example          |
|---------------------|--------------------------------------------|------------------|
| `ORGANIZATION_ID`   | Your numeric Organization ID               | `123456789012`   |
| `ACCESS_POLICY_ID`  | ID for your organization's Access Policy   | `123456789`      |

### How to Get ORGANIZATION_ID

```bash
gcloud organizations list
```

### How to Get ACCESS_POLICY_ID

```bash
gcloud access-context-manager policies list --organization=ORGANIZATION_ID
```

Fill in these values for steps involving VPC perimeters, access policies, and org-level controls.

---

**If you have questions about either setup, open an issue or discussion on the repository!**
