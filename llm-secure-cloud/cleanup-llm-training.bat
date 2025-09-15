@echo off
REM === LLM TRAINING CLEANUP - WINDOWS BATCH FILE ===
REM This script automatically cleans up all GCP resources created by secure-llm-training.py
REM Generated on: us-east1 for project: agentic-fortress
REM WARNING: This will delete ALL data without confirmation!

echo.
echo ===========================================
echo 🧹 LLM TRAINING CLEANUP SCRIPT
echo ===========================================
echo.
echo ⚠️  WARNING: This will DELETE ALL DATA!
echo.
echo This batch file will clean up the following:
echo 📍 Compute Instance: llm-trainer-001 (us-east1-a)
echo 📦 Storage Buckets: gs://agentic-fortress-llm-models, gs://agentic-fortress-training-data
echo 🔐 KMS Keys: llm-training-keys
echo 🌐 Network Resources: llm-training-vpc and subnets
echo.
echo Press Ctrl+C NOW if you want to cancel!
echo.
timeout /t 10 /nobreak >nul
echo.
echo ✅ Proceeding with cleanup...
echo.

REM Stop and delete compute instance
echo 🔧 Stopping and deleting compute instance...
gcloud compute instances stop llm-trainer-001 --zone us-east1-a --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Instance stopped successfully
) else (
    echo ⚠️ Instance already stopped or not found
)

gcloud compute instances delete llm-trainer-001 --zone us-east1-a --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Compute instance deleted
) else (
    echo ❌ Compute instance deletion failed
)
echo.

REM Delete storage buckets (CAUTION: This will delete ALL data)
echo 🔧 Deleting storage buckets (ALL DATA WILL BE LOST)...
echo ⚠️  WARNING: Deleting gs://agentic-fortress-llm-models

gcloud storage rm -r gs://agentic-fortress-llm-models 2>nul
if %errorlevel%==0 (
    echo ✅ Model bucket deleted
) else (
    echo ❌ Model bucket deletion failed or not found
)

echo ⚠️  WARNING: Deleting gs://agentic-fortress-training-data
gcloud storage rm -r gs://agentic-fortress-training-data 2>nul
if %errorlevel%==0 (
    echo ✅ Dataset bucket deleted
) else (
    echo ❌ Dataset bucket deletion failed or not found
)
echo.

REM Delete encryption keys
echo 🔧 Deleting KMS encryption keys...
gcloud kms keys destroy model-encryption-key --keyring llm-training-keys --location us-east1 --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ KMS key destroyed
) else (
    echo ❌ KMS key destruction failed or not found
)
echo.

REM Delete VPC and subnets (LAST, as other resources depend on network)
echo 🔧 Deleting network resources (us-east1)...
echo firewall rules and subnets first...
gcloud compute firewall-rules delete allow-ssh-internal --quiet 2>nul
gcloud compute firewall-rules delete allow-iap-ssh --quiet 2>nul
gcloud compute firewall-rules delete default-deny-all-llm-training-vpc --quiet 2>nul

gcloud compute networks subnets delete llm-training-private-subnet --region us-east1 --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Subnet deleted
) else (
    echo ❌ Subnet deletion failed or not found
)

gcloud compute networks delete llm-training-vpc --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ VPC deleted
) else (
    echo ❌ VPC deletion failed or not found
)

REM Clean up test resources too
gcloud compute networks delete llm-training-vpc-test --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Test VPC cleaned up
) else (
    echo ❌ Test VPC already deleted or not found
)
echo.

echo ===========================================
echo 🎉 CLEANUP COMPLETE
echo ===========================================
pause
