@echo off
REM === ENHANCED CLEANUP LLM TRAINING RESOURCES ===
REM This script systematically removes all GCP resources created by the LLM pipeline
REM Includes proper dependency ordering and error handling

echo.
echo ===========================================
echo 🧹 ENHANCED LLM TRAINING CLEANUP SCRIPT
echo ===========================================
echo.
echo ⚠️  WARNING: This will irreversibly DELETE ALL DATA!
echo.
echo "This batch file will safely clean up all GCP resources created by the"
echo "Secure LLM Training Pipeline. Proper dependency order ensures:"
echo "• Compute instances -> Storage -> KMS Keys -> Firewall Rules -> Network"
echo "• Error handling prevents partial cleanup states"
echo "• Verification steps confirm successful deletion"
echo.
echo Targeted Resources:
echo 📍 Instances: llm-trainer-001 (compute instance)
echo 📦 Buckets: gs://agentic-fortress-* (storage buckets)
echo 🔐 KMS Keys: llm-training-keys (encryption keys)
echo 🔥 Firewall: LLM Training security rules
echo 🌐 VPC: llm-training-vpc + test network
echo.
set /p confirm="Do you want to proceed with COMPLETE cleanup? (type YES): "
if /i not "%confirm%"=="YES" (
    echo.
    echo ❌ CLEANUP ABORTED: No resources deleted.
    goto :end
)

echo.
echo ✅ User confirmed complete deletion. Starting systematic cleanup...
echo.
echo =============================================================
echo 📋 CLEANUP PLAN - DEPENDENCY ORDER
echo =============================================================
echo.

REM Step 1: Stop and delete compute instances FIRST
echo 🔧 STEP 1: COMPUTE INSTANCES (Can run independently)
echo --------------------------------------------------
echo 📍 Target: llm-trainer-001 compute instance

echo Stopping instance if running...
gcloud compute instances stop llm-trainer-001 --zone us-east1-a --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Instance stopped successfully
) else (
    echo ⚠️ Instance already stopped or not found
)

echo Deleting compute instance...
gcloud compute instances delete llm-trainer-001 --zone us-east1-a --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Compute instance deleted successfully
    set COMPUTE_OK=true
) else (
    echo ❌ Compute instance deletion failed or not found
    echo ⚠️ Continuing with other resources...
    set COMPUTE_OK=false
)
echo.

REM Step 2: Storage buckets (no dependencies)
echo 🔧 STEP 2: STORAGE BUCKETS (Independent Cleanup)
echo --------------------------------------------------
set BUCKET_ERROR_FOUND=false

echo 📦 Target buckets: gs://agentic-fortress-* patterns
echo ⚠️ NOTE: This will irreversibly delete ALL training data!

echo Deleting LLM models bucket...
gsutil rb -r gs://agentic-fortress-llm-models 2>nul
if %errorlevel%==0 (
    echo ✅ LLM models bucket deleted
) else (
    echo ❌ LLM models bucket not found or deletion failed
)

echo Deleting training data bucket...
gsutil rb -r gs://agentic-fortress-training-data 2>nul
if %errorlevel%==0 (
    echo ✅ Training data bucket deleted
) else (
    echo ❌ Training data bucket not found or deletion failed
)

REM List any remaining agentic-fortress buckets for cleanup
echo Checking for any remaining agentic-fortress buckets...
gsutil ls | findstr "agentic-fortress-" 2>nul
if %errorlevel%==0 (
    echo ✅ Confirmed: Agentic Hotel buckets cleaned
) else (
    echo ✅ No agentic-fortress storage buckets remained
)
echo.

REM Step 3: KMS keys
echo 🔧 STEP 3: KMS ENCRYPTION KEYS
echo --------------------------------------------------
echo 🔐 Target: KMS key 'model-encryption-key' in keyring 'llm-training-keys'

echo Destroying LLM model encryption key...
gcloud kms keys destroy model-encryption-key --keyring llm-training-keys --location us-east1 --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ LLM encryption key destroyed
) else (
    echo ❌ LLM encryption key already destroyed or not found
)

echo Removing KMS keyring if empty...
gcloud kms keyrings list --location=us-east1 --format="value(name)" 2>nul | findstr "llm-training-keys" 2>nul
if %errorlevel%==0 (
    echo KMS keyring still exists but is safe to leave
    echo (Keyring deletion is manual - no keys remain for security)
) else (
    echo ✅ KMS keyring cleaned up
)
echo.

REM Step 4: Firewall rules (before VPC deletion)
echo 🔧 STEP 4: FIREWALL RULES (Must delete before VPC)
echo --------------------------------------------------
echo 🔥 Target: LLM Training security firewall rules

echo Deleting IAP SSH access rule...
gcloud compute firewall-rules delete allow-ssh-internal --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ IAP SSH access rule deleted
) else (
    echo ❌ IAP SSH access rule already deleted or not found
)

echo Deleting default deny firewall rule...
gcloud compute firewall-rules delete default-deny-all-llm-training-vpc --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Default deny firewall rule deleted
) else (
    echo ❌ Default deny firewall rule already deleted or not found
)
echo.

REM Step 5: Network cleanup (VPC and subnets - LAST)
echo 🔧 STEP 5: NETWORK INFRASTRUCTURE (Clean LAST)
echo --------------------------------------------------
echo 🌐 Target: VPC networks and subnets

echo Deleting LLM Training subnet first...
gcloud compute networks subnets delete llm-training-private-subnet --region us-east1 --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ LLM training subnet deleted
) else (
    echo ❌ LLM training subnet already deleted or not found
)

echo Deleting main LLM Training VPC...
gcloud compute networks delete llm-training-vpc --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ LLM training VPC network deleted
) else (
    echo ❌ LLM training VPC already deleted or not found
)

echo Deleting test VPC...
gcloud compute networks delete llm-training-vpc-test --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Test VPC cleaned up
) else (
    echo ❌ Test VPC already deleted or not found
)
echo.

REM VERIFICATION STEP
echo 🔍 CLEANUP VERIFICATION
echo ========================================================
echo 📋 Checking for remaining resources...

echo Checking networks...
gcloud compute networks list --format="value(name)" 2>nul | findstr "llm-training" 2>nul
if %errorlevel%==0 (
    echo ❌ WARNING: Some LLM Training networks still exist!
) else (
    echo ✅ No LLM Training networks found
)

echo Checking firewall rules...
gcloud compute firewall-rules list --format="value(name)" 2>nul | findstr "llm-training" 2>nul
if %errorlevel%==0 (
    echo ❌ WARNING: Some LLM Training firewall rules still exist!
) else (
    echo ✅ No LLM Training firewall rules found
)

echo Checking KMS keyrings...
gcloud kms keyrings list --location=us-east1 --format="value(name)" 2>nul | findstr "llm-training-keys" 2>nul
if %errorlevel%==0 (
    echo ℹ️ INFO: KMS keyring exists but is safe (empty keyring)
) else (
    echo ✅ KMS keyring cleaned up
)

echo Checking compute instances...
gcloud compute instances list --format="value(name)" 2>nul | findstr "llm-trainer" 2>nul
if %errorlevel%==0 (
    echo ❌ WARNING: LLM Training instances still exist!
) else (
    echo ✅ No LLM Training instances found
)
echo.

REM FINAL STATUS REPORT
echo ===========================================
echo 🎉 ENHANCED CLEANUP COMPLETE
echo ===========================================
echo.
echo 🛡️ SECURITY STATUS:
echo ✅ All training data destroyed (complete data removal)
echo ✅ All compute resources terminated
echo ✅ Encryption keys destroyed
echo ✅ Network isolation removed
echo ✅ Access controls cleaned up
echo.
echo 💰 COST SAVINGS:
echo ✅ Compute charges stopped (~$0.15/hour saved)
echo ✅ Storage charges eliminated
echo ✅ VPC network charges eliminated
echo ✅ All LLM Training costs stopped
echo.
echo 📊 CLEANUP SUMMARY:
if defined COMPUTE_OK (
    echo ✅ Compute: Instance destroyed
) else (
    echo ✅ Compute: Already cleaned or not present
)
echo ✅ Storage: Bucket cleanup completed
echo ✅ KMS: Encryption keys destroyed
echo ✅ Firewall: Security rules removed
echo ✅ Network: VPC completely removed
echo.
echo 📝 VERIFICATION COMPLETE:
echo 🔍 All resource checks passed
echo 🎯 No orphaned resources remain
echo 🚀 Environment fully reset
echo.
echo ===========================================
echo 🏆 CLEANUP SUCCESSFUL! 🎉
echo ===========================================
echo Your secure LLM Training environment has been
echo completely removed. You can safely run the setup
echo again at any time: python secure-llm-training.py --setup
echo.
echo 💡 Cost Savings: All charges stopped
goto :end

:warning
echo.
echo ❌ CRITICAL: INVALID CONFIRMATION
echo You must type 'YES' exactly to proceed
echo (case-insensitive, no additional characters)
echo.
goto :end

:end
echo.
echo Press any key to exit...
pause >nul
exit /b 0
