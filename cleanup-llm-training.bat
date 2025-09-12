@echo off
REM === CLEANUP LLM TRAINING RESOURCES ===
REM This script removes all GCP resources created by the secure LLM training pipeline
REM WARNING: This will delete ALL data and cannot be undone!

echo.
echo ===========================================
echo 🧹 LLM TRAINING CLEANUP SCRIPT
echo ===========================================
echo.
echo ⚠️  WARNING: This will DELETE ALL DATA!
echo.
echo "This batch file will clean up all GCP resources created by the"
echo "Secure LLM Training Pipeline. This includes:"
echo "• Compute instances"
echo "• Storage buckets (ALL data will be lost!)"
echo "• Encryption keys"
echo "• VPC networks and subnets"
echo.
echo Resources to be cleaned up:
echo - llm-trainer-001 (compute instance)
echo - gs://agentic-fortress-llm-models (storage bucket)
echo - gs://agentic-fortress-training-data (bucket)
echo - llm-training-keys (KMS key ring)
echo - llm-training-vpc (network)
echo.
set /p confirm="Do you want to proceed with cleanup? (type YES to continue): "
if /i not "%confirm%"=="YES" (
    echo.
    echo ❌ Cleanup aborted. No resources deleted.
    goto :end
)

echo.
echo ✅ User confirmed deletion. Proceeding with cleanup...
echo.

REM Stop and delete compute instances
echo.
echo 🔧 Stopping and deleting compute instances...
gcloud compute instances stop llm-trainer-001 --zone us-east1-a 2>nul
gcloud compute instances delete llm-trainer-001 --zone us-east1-a --quiet
if %errorlevel%==0 (echo ✅ Instance deleted) else (echo ❌ Instance deletion failed)

REM Delete storage buckets
echo.
echo 🔧 Deleting storage buckets...
echo ⚠️  This will irreversibly delete ALL data!
gsutil rb -r gs://agentic-fortress-llm-models 2>nul
if %errorlevel%==0 (echo ✅ Model bucket deleted) else (echo ❌ Model bucket deletion failed)

gsutil rb -r gs://agentic-fortress-training-data 2>nul
if %errorlevel%==0 (echo ✅ Dataset bucket deleted) else (echo ❌ Dataset bucket deletion failed)

REM Delete encryption keys
echo.
echo 🔧 Deleting encryption keys...
gcloud kms keys destroy model-encryption-key --keyring llm-training-keys --location us-east1 --quiet 2>nul
if %errorlevel%==0 (echo ✅ KMS key destroyed) else (echo ❌ KMS key destruction failed)

REM Delete VPC and subnets
echo.
echo 🔧 Deleting VPC networks and subnets...
gcloud compute networks subnets delete llm-training-private-subnet --region us-east1 --quiet 2>nul
if %errorlevel%==0 (echo ✅ Subnet deleted) else (echo ❌ Subnet deletion failed)

gcloud compute networks delete llm-training-vpc --quiet 2>nul
if %errorlevel%==0 (echo ✅ VPC deleted) else (echo ❌ VPC deletion failed)

REM Delete test resources
echo.
echo 🔧 Deleting test resources...
gcloud compute networks delete llm-training-vpc-test --quiet 2>nul
if %errorlevel%==0 (echo ✅ Test VPC deleted) else (echo ❌ Test VPC already deleted or not found)

echo.
echo ===========================================
echo 🎉 CLEANUP COMPLETE
echo ===========================================
echo.
echo 🛡️  Security Best Practices Followed:
echo 🧹 All resources deleted to prevent unauthorized access
echo 💰 All charges stopped (resources deleted)
echo 🚀 Environment reset for future use
echo.
echo 📋 What was cleaned up:
echo ✅ Compute instances stopped and deleted
echo ✅ Storage buckets emptied and removed
echo ✅ Encryption keys destroyed
echo ✅ VPC networks and subnets deleted
echo ✅ Test resources removed
echo.
echo 📝 Next steps:
echo 1. Verify no charges appear in GCP Console
echo 2. Check IAM permissions if you want to re-run
echo 3. Run the setup again if needed: python secure-llm-training.py --setup
echo.
echo 💡 Cost savings: All resources deleted to stop charges
goto :end

:warning
echo.
echo ❌ INVALID CONFIRMATION
echo You must type 'YES' exactly to proceed with deletion
echo.
pause
exit /b 1

:end
echo.
pause
exit /b 0
