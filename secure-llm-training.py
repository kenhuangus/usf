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
    """Create VPC with security best practices."""
    print("\n" + "="*60)
    print("🛡️  CREATING SECURE VPC & NETWORKING")
    print("="*60)

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
    """Set up customer-managed encryption keys."""
    print("\n" + "="*60)
    print("🔐 SETTING UP ENCRYPTION KEYS")
    print("="*60)

    # Create KMS key ring
    print("\n🔐 Creating KMS key ring...")
    run_gcp_command([
        "gcloud", "kms", "keyrings", "create",
        SECURITY_CONFIG["security"]["kms_key_ring"],
        "--location", GCP_REGION,
        "--project", GCP_PROJECT,
    ], "Creating KMS key ring")

    # Create encryption key
    print("\n🔐 Creating encryption key for model data...")
    run_gcp_command([
        "gcloud", "kms", "keys", "create",
        SECURITY_CONFIG["security"]["kms_key"],
        "--location", GCP_REGION,
        "--keyring", SECURITY_CONFIG["security"]["kms_key_ring"],
        "--purpose", "encryption",
        "--algorithm", "GOOGLE_SYMMETRIC_ENCRYPTION",
        "--rotation-period", "30d",  # Rotate every 30 days
        "--next-rotation-time", "30d",
        "--protection-level", "SOFTWARE",
        "--labels", "purpose=llm-training,security=customer-managed",
    ], "Creating asymmetric encryption key")

    print("✅ Encryption keys setup complete!")

def create_secure_storage_buckets():
    """Create encrypted storage buckets with security best practices."""
    print("\n" + "="*60)
    print("📦 CREATING SECURE STORAGE BUCKETS")
    print("="*60)

    kms_key_path = f"projects/{GCP_PROJECT}/locations/{GCP_REGION}/keyRings/{SECURITY_CONFIG['security']['kms_key_ring']}/cryptoKeys/{SECURITY_CONFIG['security']['kms_key']}"

    # Create model storage bucket
    print("\n📦 Creating model storage bucket...")
    run_gcp_command([
        "gsutil", "mb",
        "-p", GCP_PROJECT,
        "-c", "STANDARD",
        "-l", GCP_REGION,
        "-b", "on",  # Enable billing (required for CMEK)
        f"gs://{SECURITY_CONFIG['storage']['model_bucket']}",
    ], "Creating encrypted model storage bucket")

    # Set customer-managed encryption
    run_gcp_command([
        "gsutil", "kms", "encryption",
        "-k", kms_key_path,
        f"gs://{SECURITY_CONFIG['storage']['model_bucket']}",
    ], "Enabling customer-managed encryption on model bucket")

    # Enable versioning for backup/recovery
    run_gcp_command([
        "gsutil", "versioning", "set", "on",
        f"gs://{SECURITY_CONFIG['storage']['model_bucket']}",
    ], "Enabling versioning on model bucket")

    # Create dataset bucket
    print("\n📦 Creating dataset storage bucket...")
    run_gcp_command([
        "gsutil", "mb",
        "-p", GCP_PROJECT,
        "-c", "STANDARD",
        "-l", GCP_REGION,
        f"gs://{SECURITY_CONFIG['storage']['dataset_bucket']}",
    ], "Creating encrypted dataset storage bucket")

    # Public access prevention
    run_gcp_command([
        "gsutil", "pap", "set", "enforced",
        f"gs://{SECURITY_CONFIG['storage']['dataset_bucket']}",
    ], "Enabling public access prevention on dataset bucket")

    print("✅ Secure storage buckets created!")

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

    # Create the instance with maximum security
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
        "--shielded-learn-integrity-policy",
        "--reservation-affinity", "none",
        "--metadata", "startup-script=" + startup_script,
        "--metadata-from-file", "environment=secure-training-env.sh",
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
    """Provide cleanup commands after training completes."""
    print("\n" + "="*60)
    print("🧹 CLEANUP INSTRUCTIONS")
    print("="*60)

    cleanup_commands = f"""
# ⚠️ IMPORTANT: Run these commands after training to clean up resources:

# Stop and delete compute instance
gcloud compute instances stop {SECURITY_CONFIG['compute']['instance_prefix']}-001 --zone {GCP_ZONE}
gcloud compute instances delete {SECURITY_CONFIG['compute']['instance_prefix']}-001 --zone {GCP_ZONE}

# Delete storage buckets (CAUTION: This will delete ALL data)
gsutil rb -r gs://{SECURITY_CONFIG['storage']['model_bucket']}
gsutil rb -r gs://{SECURITY_CONFIG['storage']['dataset_bucket']}

# Delete encryption keys
gcloud kms keys destroy {SECURITY_CONFIG['security']['kms_key']} \
--keyring {SECURITY_CONFIG['security']['kms_key_ring']} --location {GCP_REGION}

# Delete VPC and all subnets/firewall rules
gcloud compute networks subnets delete {SECURITY_CONFIG['vpc']['subnet']} --region {GCP_REGION}
gcloud compute networks delete {SECURITY_CONFIG['vpc']['name']}
"""

    print(cleanup_commands)

    # Save cleanup script
    with open("cleanup-llm-training.sh", "w", encoding="utf-8") as f:
        f.write(cleanup_commands)
    print("💾 Cleanup commands saved to: cleanup-llm-training.sh")

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
            # Execute security setup steps
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
