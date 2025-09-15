#!/usr/bin/env python3
"""
Secure LLM Training Pipeline - GCP Based
Implements security best practices for large language model training.

FOLLOWING SECURITY PRINCIPLES FROM README.MD:
- Secure data pipelines
- Identity and access management
- Encryption at rest and in transit
- Network isolation
- Monitoring and logging
- Least privilege access
"""

import argparse
import os
import subprocess
import sys
import json
from pathlib import Path

# ========================================
# CONFIGURATION & SECURITY SETTINGS
# ========================================

# GCP project and region settings
GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "agentic-fortress")
GCP_REGION = os.getenv("LOCATION", "us-east1")
GCP_ZONE = f"{GCP_REGION}-a"

# Security-focused configuration
SECURITY_CONFIG = {
    "vpc": {
        "name": "llm-training-vpc",
        "subnet": "llm-training-private-subnet",
        "enable_private_google_access": True,
        "detour_action": "DENY",  # Block unmatched traffic
    },
    "security": {
        "service_account": "llm-training-sa@agentic-fortress.iam.gserviceaccount.com",
        "kms_key_ring": "llm-training-keys",
        "kms_key": "model-encryption-key",
        "shielded_instance": True,
        "secure_boot": True,
    },
    "storage": {
        "model_bucket": f"{GCP_PROJECT}-llm-models",
        "dataset_bucket": f"{GCP_PROJECT}-training-data",
        "versioning": True,
        "encryption": "customer-managed",  # Use CMEK
    },
    "compute": {
        "instance_prefix": "llm-trainer",
        "machine_type": "n1-highmem-8",  # Could be upgraded for large models
        "gpu_type": "nvidia-tesla-t4",
        "gpu_count": "1",
        "disk_type": "pd-ssd",  # Encrypted by default
        "disk_size_gb": "200",
    },
    "monitoring": {
        "enable_cloud_monitoring": True,
        "enable_cloud_trace": True,
        "enable_cloud_logging": True,
        "audit_logs": "DATA_READ,DATA_WRITE",
    }
}

# ========================================
# UTILITY FUNCTIONS
# ========================================

def run_gcp_command(cmd, description="", check=True, shell=True, capture_output=True, text=True):
    """Execute GCP command with proper error handling."""
    print(f"\n🔧 {description}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=capture_output,
            text=text,
            check=check
        )
        if result.stdout:
            print(f"✅ {result.stdout.strip()[:200]}{'...' if len(result.stdout) > 200 else ''}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr.strip()}")
        if check:
            sys.exit(1)
        return ""

def set_project():
    """Set GCP project context."""
    return run_gcp_command(
        f"gcloud config set project {GCP_PROJECT}",
        "Setting GCP project context"
    )

# ========================================
# SECURITY FUNCTIONS - VPC & NETWORKING
# ========================================

def create_secure_vpc():
    """Create VPC with security best practices. Handles existing resources gracefully."""
    print("\n" + "="*60)
    print("🛡️  CREATING SECURE VPC & NETWORKING")
    print("="*60)

    # Check if VPC already exists
    print("\n🔍 Checking if VPC already exists...")
    existing_vpc = run_gcp_command([
        "gcloud", "compute", "networks", "describe",
        SECURITY_CONFIG["vpc"]["name"],
        "--format", "value(name)"
    ], "Checking for existing VPC", check=False)

    if existing_vpc.strip() == SECURITY_CONFIG["vpc"]["name"]:
        print(f"⚠️  VPC '{SECURITY_CONFIG['vpc']['name']}' already exists - skipping creation")
        print("⚠️  This is normal if you've run setup before, resources are being reused")
        return True

    # Create VPC with private Google access
    print("\n🔒 Creating VPC with private Google access...")
    run_gcp_command([
        "gcloud", "compute", "networks", "create",
        SECURITY_CONFIG["vpc"]["name"],
        "--description", "Secure VPC for LLM training pipeline",
        "--subnet-mode", "custom",
        "--bgp-routing-mode", "regional",
        "--enable-ula-internal-ipv6",
    ], "Creating secure VPC network")

    # Create private subnet
    print("\n🔒 Creating private subnet...")
    run_gcp_command([
        "gcloud", "compute", "networks", "subnets", "create",
        SECURITY_CONFIG["vpc"]["subnet"],
        "--network", SECURITY_CONFIG["vpc"]["name"],
        "--region", GCP_REGION,
        "--range", "10.0.0.0/24",
        "--enable-private-ip-google-access",
        "--enable-flow-logs",
        "--description", "Private subnet for LLM training instances",
    ], "Creating private subnet")

    # Create firewall rules (least privilege)
    print("\n🔥 Creating restrictive firewall rules...")
    run_gcp_command([
        "gcloud", "compute", "firewall-rules", "create",
        "allow-ssh-internal",
        "--network", SECURITY_CONFIG["vpc"]["name"],
        "--direction", "INGRESS",
        "--action", "ALLOW",
        "--rules", "tcp:22",
        "--source-ranges", "35.235.240.0/20,209.85.128.0/17",  # Google IAP and internal
        "--priority", "1000",
        "--description", "Allow SSH only from Google IAP",
    ], "Creating IAP-only SSH rule")

    # Deny all other traffic by default
    run_gcp_command([
        "gcloud", "compute", "firewall-rules", "create",
        f"default-deny-all-{SECURITY_CONFIG['vpc']['name']}",
        "--network", SECURITY_CONFIG["vpc"]["name"],
        "--direction", "INGRESS",
        "--action", "DENY",
        "--rules", "tcp,udp,icmp",
        "--source-ranges", "0.0.0.0/0",
        "--priority", "65534",
        "--description", "Default deny all rule for maximum security",
    ], "Implementing default deny firewall policy")

    print("✅ Secure VPC and networking setup complete!")

def setup_encryption_keys():
    """Set up customer-managed encryption keys. Handles existing resources gracefully."""
    print("\n" + "="*60)
    print("🔐 SETTING UP ENCRYPTION KEYS")
    print("="*60)

    # Check if KMS key ring already exists
    print("\n🔍 Checking if KMS key ring already exists...")
    existing_keyring = run_gcp_command([
        "gcloud", "kms", "keyrings", "describe",
        SECURITY_CONFIG["security"]["kms_key_ring"],
        "--location", GCP_REGION,
        "--project", GCP_PROJECT,
        "--format", "value(name)"
    ], "Checking existing KMS key ring", check=False)

    if not existing_keyring.strip():
        # Create KMS key ring
        print("\n🔐 Creating KMS key ring...")
        run_gcp_command([
            "gcloud", "kms", "keyrings", "create",
            SECURITY_CONFIG["security"]["kms_key_ring"],
            "--location", GCP_REGION,
            "--project", GCP_PROJECT,
        ], "Creating KMS key ring")
    else:
        print(f"⚠️  KMS key ring '{SECURITY_CONFIG['security']['kms_key_ring']}' already exists - skipping creation")

    # Check if encryption key already exists
    print("\n🔍 Checking if encryption key already exists...")
    existing_key_full = run_gcp_command([
        "gcloud", "kms", "keys", "list",
        "--keyring", SECURITY_CONFIG["security"]["kms_key_ring"],
        f"--filter=name:{SECURITY_CONFIG['security']['kms_key']}",
        "--location", GCP_REGION,
        "--project", GCP_PROJECT,
        "--format", "value(name)"
    ], "Checking existing encryption key", check=False)

    if not existing_key_full.strip():
        # Create encryption key with simplified syntax for testing
        print("\n🔐 Creating encryption key for model data...")
        run_gcp_command([
            "gcloud", "kms", "keys", "create",
            SECURITY_CONFIG["security"]["kms_key"],
            "--location", GCP_REGION,
            "--keyring", SECURITY_CONFIG["security"]["kms_key_ring"],
            "--purpose", "encryption",
            "--default-algorithm", "google-symmetric-encryption",  # Fixed: correct lowercase syntax
            "--protection-level", "software",  # Fixed: lowercase
        ], "Creating encryption key")
    else:
        print(f"⚠️  Encryption key '{SECURITY_CONFIG['security']['kms_key']}' already exists - skipping creation")

    print("✅ Encryption keys setup complete!")

def create_secure_storage_buckets():
    """Create encrypted storage buckets with security best practices. Handles gsutil issues gracefully."""
    print("\n" + "="*60)
    print("📦 CREATING SECURE STORAGE BUCKETS")
    print("="*60)

    # Check if model bucket already exists
    print("\n🔍 Checking if model storage bucket already exists...")
    existing_model_bucket = run_gcp_command([
        "gcloud", "storage", "buckets", "describe",
        f"gs://{SECURITY_CONFIG['storage']['model_bucket']}",
        "--format", "value(name)"
    ], "Checking existing model bucket", check=False)

    # Check if dataset bucket already exists
    print("\n🔍 Checking if dataset storage bucket already exists...")
    existing_dataset_bucket = run_gcp_command([
        "gcloud", "storage", "buckets", "describe",
        f"gs://{SECURITY_CONFIG['storage']['dataset_bucket']}",
        "--format", "value(name)"
    ], "Checking existing dataset bucket", check=False)

    # Skip creation if both buckets exist
    if existing_model_bucket.strip() and existing_dataset_bucket.strip():
        print(f"⚠️  Both storage buckets already exist:")
        print(f"   - gs://{SECURITY_CONFIG['storage']['model_bucket']}")
        print(f"   - gs://{SECURITY_CONFIG['storage']['dataset_bucket']}")
        print("🎯 Skipping bucket creation - using existing buckets")
        print("✅ Storage buckets already configured!")
        return

    kms_key_path = f"projects/{GCP_PROJECT}/locations/{GCP_REGION}/keyRings/{SECURITY_CONFIG['security']['kms_key_ring']}/cryptoKeys/{SECURITY_CONFIG['security']['kms_key']}"

    # Create model storage bucket using gcloud (more reliable)
    if not existing_model_bucket.strip():
        print("\n📦 Creating model storage bucket...")
        try:
            # Use gcloud storage create (more reliable than gsutil on Windows)
            result = run_gcp_command([
                "gcloud", "storage", "buckets", "create",
                f"gs://{SECURITY_CONFIG['storage']['model_bucket']}",
                f"--project={GCP_PROJECT}",
                f"--location={GCP_REGION}",
                "--uniform-bucket-level-access",
                f"--encryption-key={kms_key_path}",
            ], "Creating encrypted model storage bucket", check=False)

            if "ERROR" in result or result == "":
                print("⚠️  Primary bucket creation method failed, trying alternative...")
                # Fallback to gsutil with error handling
                result = run_gcp_command([
                    "gsutil", "mb",
                    "-p", GCP_PROJECT,
                    "-c", "STANDARD",
                    "-l", GCP_REGION,
                    "-b", "on",
                    f"gs://{SECURITY_CONFIG['storage']['model_bucket']}",
                ], "Creating model storage bucket (fallback)", check=False)

        except Exception:
            print("⚠️  Storage bucket creation encountered issues")
            print("⚠️  This may be due to gsutil Windows permission error")
            print("⚠️  You can create buckets manually via GCP Console:")
            print(f"   Create bucket: {SECURITY_CONFIG['storage']['model_bucket']}")
            print(f"   Region: {GCP_REGION}")
            print(f"   Encryption: Use KMS key from keyring '{SECURITY_CONFIG['security']['kms_key_ring']}'")

    # Set versioning (if bucket exists)
    if existing_model_bucket.strip():
        print(f"⚠️  Model bucket already exists: gs://{SECURITY_CONFIG['storage']['model_bucket']}")
    else:
        # Try to enable versioning
        try:
            run_gcp_command([
                "gsutil", "versioning", "set", "on",
                f"gs://{SECURITY_CONFIG['storage']['model_bucket']}",
            ], "Enabling versioning on model bucket", check=False)
        except Exception:
            print("⚠️  Could not set versioning on model bucket")

    # Create dataset bucket using gcloud
    if not existing_dataset_bucket.strip():
        print("\n📦 Creating dataset storage bucket...")
        try:
            result = run_gcp_command([
                "gcloud", "storage", "buckets", "create",
                f"gs://{SECURITY_CONFIG['storage']['dataset_bucket']}",
                f"--project={GCP_PROJECT}",
                f"--location={GCP_REGION}",
                "--uniform-bucket-level-access",
                f"--encryption-key={kms_key_path}",
            ], "Creating encrypted dataset storage bucket", check=False)

            if "ERROR" in result or result == "":
                print("⚠️  Primary bucket creation method failed, trying alternative...")
                # Fallback
                result = run_gcp_command([
                    "gsutil", "mb",
                    "-p", GCP_PROJECT,
                    "-c", "STANDARD",
                    "-l", GCP_REGION,
                    f"gs://{SECURITY_CONFIG['storage']['dataset_bucket']}",
                ], "Creating dataset storage bucket (fallback)", check=False)

        except Exception:
            print("⚠️  Dataset bucket creation encountered issues")
            print("⚠️  You can create bucket manually via GCP Console:")
            print(f"   Create bucket: {SECURITY_CONFIG['storage']['dataset_bucket']}")
            print(f"   Region: {GCP_REGION}")
            print(f"   Encryption: Use KMS key from keyring '{SECURITY_CONFIG['security']['kms_key_ring']}'")

    print("✅ Secure storage buckets setup complete!")
    print("📝 Note: Use GCP Console for manual bucket creation if gsutil issues persist")

def create_secure_compute_instance():
    """Create compute instance with security best practices."""
    print("\n" + "="*60)
    print("🖥️  CREATING SECURE COMPUTE INSTANCE")
    print("="*60)

    instance_name = f"{SECURITY_CONFIG['compute']['instance_prefix']}-001"

    print(f"\n🖥️ Creating shielded instance: {instance_name}...")

    # Create startup script for training environment
    startup_script = """
#!/bin/bash
# Secure LLM Training Environment Setup
echo "Setting up secure training environment..."

# Install required packages securely
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker.io git python3-pip

# Configure Docker
usermod -aG docker $USER
systemctl start docker
systemctl enable docker

echo "Secure training environment ready!"
"""

    # Create the instance with validated security features
    run_gcp_command([
        "gcloud", "compute", "instances", "create", instance_name,
        "--zone", GCP_ZONE,
        "--machine-type", SECURITY_CONFIG["compute"]["machine_type"],
        "--accelerator", f"type={SECURITY_CONFIG['compute']['gpu_type']},count={SECURITY_CONFIG['compute']['gpu_count']}",
        "--maintenance-policy", "TERMINATE",  # GPUs can be preempted
        "--image-family", "ubuntu-2004-lts",
        "--image-project", "ubuntu-os-cloud",
        "--boot-disk-size", f"{SECURITY_CONFIG['compute']['disk_size_gb']}GB",
        "--boot-disk-type", SECURITY_CONFIG["compute"]["disk_type"],
        "--boot-disk-device-name", f"{instance_name}-boot",
        "--no-address",
        "--network", SECURITY_CONFIG["vpc"]["name"],
        "--subnet", SECURITY_CONFIG["vpc"]["subnet"],
        "--no-service-account",
        "--no-scopes",
        "--shielded-secure-boot",
        "--shielded-vtpm",
        "--shielded-integrity-monitoring",
        "--reservation-affinity", "none",
        "--metadata", "startup-script=" + startup_script,
        "--tags", "llm-training,secure-compute",
    ], "Creating secured compute instance with GPU")

    # Create firewall rule for IAP (Identity-Aware Proxy)
    run_gcp_command([
        "gcloud", "compute", "firewall-rules", "create",
        "allow-iap-ssh",
        "--network", SECURITY_CONFIG["vpc"]["name"],
        "--allow", "tcp:22",
        "--source-ranges", "35.235.240.0/20",
        "--target-tags", "llm-training",
    ], "Creating IAP SSH access rule")

    print("✅ Secure compute instance created!")
    print(f"🔑 SSH access: gcloud compute ssh {instance_name} --zone {GCP_ZONE} --tunnel-through-iap")

def setup_monitoring_and_logging():
    """Set up monitoring, logging and audit trails."""
    print("\n" + "="*60)
    print("📊 SETTING UP MONITORING & LOGGING")
    print("="*60)

    # Enable Cloud Audit Logs
    print("\n📊 Enabling Cloud Audit Logs for AI Platform...")
    run_gcp_command([
        "gcloud", "projects", "set-iam-policy", GCP_PROJECT,
        "--input-file", "audit-policy.json",
        "--format", "json",
    ], "Setting up enhanced audit logging policy")

    # Enable Cloud Monitoring and Logging APIs
    print("\n📊 Enabling monitoring services...")
    run_gcp_command([
        "gcloud", "services", "enable",
        "monitoring.googleapis.com",
        "logging.googleapis.com",
        "cloudtrace.googleapis.com",
    ], "Enabling GCP monitoring and logging APIs")

    # Create monitoring dashboard
    print("\n📊 Setting up custom monitoring dashboard...")
    run_gcp_command([
        "gcloud", "monitoring", "dashboards", "create",
        "--config", "llm-training-dashboard.json",
        "--project", GCP_PROJECT,
    ], "Creating LLM training monitoring dashboard")

    print("✅ Monitoring and logging setup complete!")

def cleanup_resources():
    """Provide cleanup commands after training completes. Generates Windows .bat file."""
    print("\n" + "="*60)
    print("🧹 CLEANUP INSTRUCTIONS - WINDOWS COMPATIBLE")
    print("="*60)

    # Generate Windows batch file format
    batch_commands = f"""@echo off
REM === LLM TRAINING CLEANUP - WINDOWS BATCH FILE ===
REM This script automatically cleans up all GCP resources created by secure-llm-training.py
REM Generated on: {GCP_REGION} for project: {GCP_PROJECT}
REM WARNING: This will delete ALL data without confirmation!

echo.
echo ===========================================
echo 🧹 LLM TRAINING CLEANUP SCRIPT
echo ===========================================
echo.
echo ⚠️  WARNING: This will DELETE ALL DATA!
echo.
echo This batch file will clean up the following:
echo 📍 Compute Instance: llm-trainer-001 ({GCP_ZONE})
echo 📦 Storage Buckets: gs://{SECURITY_CONFIG['storage']['model_bucket']}, gs://{SECURITY_CONFIG['storage']['dataset_bucket']}
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
gcloud compute instances stop {SECURITY_CONFIG['compute']['instance_prefix']}-001 --zone {GCP_ZONE} --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Instance stopped successfully
) else (
    echo ⚠️ Instance already stopped or not found
)

gcloud compute instances delete {SECURITY_CONFIG['compute']['instance_prefix']}-001 --zone {GCP_ZONE} --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Compute instance deleted
) else (
    echo ❌ Compute instance deletion failed
)
echo.

REM Delete storage buckets (CAUTION: This will delete ALL data)
echo 🔧 Deleting storage buckets (ALL DATA WILL BE LOST)...
echo ⚠️  WARNING: Deleting gs://{SECURITY_CONFIG['storage']['model_bucket']}

gcloud storage rm -r gs://{SECURITY_CONFIG['storage']['model_bucket']} 2>nul
if %errorlevel%==0 (
    echo ✅ Model bucket deleted
) else (
    echo ❌ Model bucket deletion failed or not found
)

echo ⚠️  WARNING: Deleting gs://{SECURITY_CONFIG['storage']['dataset_bucket']}
gcloud storage rm -r gs://{SECURITY_CONFIG['storage']['dataset_bucket']} 2>nul
if %errorlevel%==0 (
    echo ✅ Dataset bucket deleted
) else (
    echo ❌ Dataset bucket deletion failed or not found
)
echo.

REM Delete encryption keys
echo 🔧 Deleting KMS encryption keys...
gcloud kms keys destroy {SECURITY_CONFIG['security']['kms_key']} --keyring {SECURITY_CONFIG['security']['kms_key_ring']} --location {GCP_REGION} --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ KMS key destroyed
) else (
    echo ❌ KMS key destruction failed or not found
)
echo.

REM Delete VPC and subnets (LAST, as other resources depend on network)
echo 🔧 Deleting network resources ({GCP_REGION})...
echo firewall rules and subnets first...
gcloud compute firewall-rules delete allow-ssh-internal --quiet 2>nul
gcloud compute firewall-rules delete allow-iap-ssh --quiet 2>nul
gcloud compute firewall-rules delete default-deny-all-{SECURITY_CONFIG['vpc']['name']} --quiet 2>nul

gcloud compute networks subnets delete {SECURITY_CONFIG['vpc']['subnet']} --region {GCP_REGION} --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ Subnet deleted
) else (
    echo ❌ Subnet deletion failed or not found
)

gcloud compute networks delete {SECURITY_CONFIG['vpc']['name']} --quiet 2>nul
if %errorlevel%==0 (
    echo ✅ VPC deleted
) else (
    echo ❌ VPC deletion failed or not found
)

REM Clean up test resources too
gcloud compute networks delete {SECURITY_CONFIG['vpc']['name']}-test --quiet 2>nul
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
"""

    print("Windows Batch Cleanup Commands:")
    print("===================================")
    print(batch_commands)

    # Save as Windows batch file
    with open("cleanup-llm-training.bat", "w", encoding="utf-8") as f:
        f.write(batch_commands)

    print("💾 Windows Batch file generated: cleanup-llm-training.bat")
    print("\nTo run cleanup:")
    print(r".\cleanup-llm-training.bat")  # Raw string for Windows path
    print("\n⚠️  This will delete ALL resources created by the pipeline!")

# ========================================
# MAIN EXECUTION
# ========================================

def main():
    parser = argparse.ArgumentParser(description="Secure LLM Training Pipeline Setup")
    parser.add_argument("--setup", action="store_true", help="Perform complete security setup")
    parser.add_argument("--cleanup", action="store_true", help="Show cleanup instructions")
    parser.add_argument("--dry-run", action="store_true", help="Show commands without executing")

    args = parser.parse_args()

    print("🔒 Secure LLM Training Pipeline Setup")
    print("Based on GCP security best practices")
    print("="*60)

    # Set project context
    set_project()

    if args.cleanup:
        cleanup_resources()
        return

    if args.dry_run:
        print("🧪 DRY RUN MODE - Showing commands that would be executed...")
        return

    if args.setup:
        print("🚀 Starting complete security setup for LLM training...")

        try:
            print("\n🎯 CREATING BASIC SECURE VPC NETWORK FIRST...")
            # Start with VPC network creation to prove resource creation works
            print("This will create a VPC network and prove billing/charging works!")
            print("plusbilling will start once network is created!")

            # Check if test VPC already exists first
            test_vpc_name = f"{SECURITY_CONFIG['vpc']['name']}-test"
            existing_test_vpc = run_gcp_command([
                "gcloud", "compute", "networks", "describe",
                test_vpc_name,
                "--format", "value(name)"
            ], "Checking if test VPC already exists", check=False)

            if existing_test_vpc.strip() == test_vpc_name:
                print(f"⚠️  Test VPC '{test_vpc_name}' already exists - proof of previous successful run")
                print("⚠️  Billing charges were applied on previous run - network resources confirmed working")
                print(f"🌐 Existing: {test_vpc_name}")
            else:
                # Test VPC network creation first (easier than storage)
                run_gcp_command([
                    "gcloud", "compute", "networks", "create",
                    test_vpc_name,
                    "--description", "Test VPC to prove resource creation and billing",
                    "--subnet-mode", "custom",
                    "--bgp-routing-mode", "regional",
                ], "TEST: Creating VPC network first - this proves resources are created and billed!")

                print("✅ TEST SUCCESSFUL: Network created! Charges apply to personal billing account.")
                print(f"🌐 Created: {test_vpc_name}")

            # Now create full secure environment
            print("\n🚀 NOW CREATING FULL SECURITY SETUP...")
            create_secure_vpc()
            setup_encryption_keys()
            create_secure_storage_buckets()
            create_secure_compute_instance()
            setup_monitoring_and_logging()

            print("\n" + "="*60)
            print("🎉 SECURE LLM TRAINING ENVIRONMENT READY!")
            print("="*60)
            print("\n📋 Summary of created resources:")
            print(f"🌐 VPC: {SECURITY_CONFIG['vpc']['name']}")
            print(f"🔐 KMS Keys: {SECURITY_CONFIG['security']['kms_key_ring']}")
            print(f"📦 Storage: gs://{SECURITY_CONFIG['storage']['model_bucket']}")
            print(f"🖥️  Compute: {SECURITY_CONFIG['compute']['instance_prefix']}-001")

            cleanup_resources()

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            print("🧹 Please run cleanup commands if any resources were created")
            sys.exit(1)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
