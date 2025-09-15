
# ⚠️ IMPORTANT: Run these commands after training to clean up resources:

# Stop and delete compute instance
gcloud compute instances stop llm-trainer-001 --zone us-east1-a
gcloud compute instances delete llm-trainer-001 --zone us-east1-a

# Delete storage buckets (CAUTION: This will delete ALL data)
gsutil rb -r gs://agentic-fortress-llm-models
gsutil rb -r gs://agentic-fortress-training-data

# Delete encryption keys
gcloud kms keys destroy model-encryption-key --keyring llm-training-keys --location us-east1

# Delete VPC and all subnets/firewall rules
gcloud compute networks subnets delete llm-training-private-subnet --region us-east1
gcloud compute networks delete llm-training-vpc
