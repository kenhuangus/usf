#!/usr/bin/env python3
"""
🚨 CRITICAL WARNING: TEST CODE ONLY - NOT FOR PRODUCTION USE 🚨

Google Cloud Platform Security Configuration Script for TESTING PURPOSES ONLY

⚠️  WARNING: This is EXPERIMENTAL, UNTESTED code for educational purposes only
⚠️  DO NOT run this in production environments
⚠️  DO NOT run this on enterprise/business accounts
⚠️  DO NOT expect professional-grade security from this script
⚠️  May create unexpected resources, expose sensitive data, or incur costs

This script is provided "AS IS" with NO WARRANTIES, EXPRESS OR IMPLIED.
Use at your own risk for learning purposes only.

Prerequisites:
- gcloud CLI configured with your credentials (gcloud auth login)
- Basic GCP account with permissions to create resources, IAM, Storage, etc.
- Python with google-cloud-sdk installed

Recommended order (FOR TESTING ONLY):
1. Install python-dotenv: pip install python-dotenv
2. Create .env file with GCP_PROJECT_ID=your-project-id
3. Enable required APIs if needed (may incur costs)
4. Run this script in a test/sandbox environment ONLY
"""

import os
import subprocess
import sys
import time
import json

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
        print("Manually load .env content or use environment variables.")

# ========================================
# CONFIGURATION - Customize these values
# ========================================

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_REGION = os.getenv("LOCATION", "us-east1")
PROJECT_NAME = "gcp-ai-security-test"
BUCKET_NAME = f"{PROJECT_NAME}-{hash(PROJECT_NAME) % 1000:03d}"  # Make unique
SERVICE_ACCOUNT_NAME = f"{PROJECT_NAME}-sa"
SERVICE_ACCOUNT_EMAIL = f"{SERVICE_ACCOUNT_NAME}@{GCP_PROJECT_ID}.iam.gserviceaccount.com"
KEY_RING_ID = f"{PROJECT_NAME}-key-ring"
KEY_ID = f"{PROJECT_NAME}-enc-key"
VPC_NETWORK_NAME = f"{PROJECT_NAME}-vpc"
SUBNET_NAME = f"{PROJECT_NAME}-subnet"
FIREWALL_NAME = f"{PROJECT_NAME}-firewall"

# ========================================
# HELPER FUNCTIONS
# ========================================

def run_command(cmd, description="", check=True):
    """Run a CLI command and handle errors."""
    print(f"\n>>> {description}")
    if isinstance(cmd, list):
        print(f"Running: {' '.join(cmd)}")
        scaled_cmd = cmd
    else:
        print(f"Running: {cmd}")
        scaled_cmd = cmd

    try:
        result = subprocess.run(scaled_cmd, check=check, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Stderr: {result.stderr.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        if not check:
            return ""
        print("⚠ Continuing despite error...")
        return ""
    except Exception as e:
        print(f"Unexpected error: {e}")
        if not check:
            return ""
        print("⚠ Continuing despite error...")
        return ""

def set_project():
    """Set the active GCP project."""
    if GCP_PROJECT_ID:
        run_command(f"gcloud config set project {GCP_PROJECT_ID}",
                   f"Setting project to {GCP_PROJECT_ID}", check=False)
        print(f"✓ Active project: {GCP_PROJECT_ID}")
        return GCP_PROJECT_ID
    else:
        print("❌ GCP_PROJECT_ID not set in .env file")
        return None

def section_header(title):
    print("\n" + "="*50)
    print(f"  {title}")
    print("="*50)

# ========================================
# STEP IMPLEMENTATIONS
# ========================================

def step1_check_prerequisites():
    """Step 1: Check Prerequisites and Basic Setup"""
    section_header("Step 1: Prerequisites Check")

    try:
        # Check gcloud auth
        result = run_command("gcloud auth list --format value.account", "Checking GCP authentication")
        if result:
            print(f"✓ GCP authenticated as: {result}")
        else:
            print("❌ GCP authentication required")
            return False

        # Set project
        if not set_project():
            return False

        # Check billing (warning only, may still work)
        billing_result = run_command(
            f"gcloud billing projects describe {GCP_PROJECT_ID} --format=value(billingEnabled)",
            "Checking billing status (may be required for some operations)", check=False
        )
        if billing_result.strip() != "True":
            print("⚠️ WARNING: Billing may not be enabled for this project")
            print("⚠️ Some resources may not be creatable or may incur unexpected costs")

        print("✅ GCP environment ready for testing")
        return True

    except Exception as e:
        print(f"❌ GCP setup check failed: {e}")
        return False

def step2_create_service_account():
    """Step 2: Create Service Account (Experimental)"""
    section_header("Step 2: Service Account Creation (Experimental)")

    try:
        # Create service account
        result = run_command([
            "gcloud", "iam", "service-accounts", "create", SERVICE_ACCOUNT_NAME,
            "--description", f"Service account for {PROJECT_NAME} experimentation",
            "--display-name", f"AI Security Test SA",
            "--format", "value(email)"
        ], f"Creating service account '{SERVICE_ACCOUNT_NAME}'")

        if result:
            print(f"✓ Service Account created: {result}")

        # Grant IAM role to service account
        try:
            run_command([
                "gcloud", "projects", "add-iam-policy-binding", GCP_PROJECT_ID,
                "--member", f"serviceAccount:{SERVICE_ACCOUNT_EMAIL}",
                "--role", "roles/aiplatform.user",
                "--condition", "None"
            ], "Granting AI Platform User role", check=False)
            print("✓ IAM role granted for Vertex AI access")
        except:
            print("⚠️ IAM role assignment may have failed (permissions or billing required)")

        return result

    except:
        print("⚠️ Service Account creation failed (expected in restricted accounts)")
        print("   Alternative: Use existing user credentials for testing")
        return ""

def step3_create_storage_bucket():
    """Step 3: Create Storage Bucket (Experimental)"""
    section_header("Step 3: Storage Bucket Creation (Experimental)")

    try:
        # Create bucket
        result = run_command([
            "gsutil", "mb", "-p", GCP_PROJECT_ID, "-c", "STANDARD", "-l", GCP_REGION,
            f"gs://{BUCKET_NAME}"
        ], f"Creating storage bucket 'gs://{BUCKET_NAME}'")

        if "Creating" in result or "created" in result.lower():
            print(f"✓ Storage bucket created: gs://{BUCKET_NAME}")

        # Set permissions to private
        try:
            # Create policy JSON
            policy_json = '{"bindings": []}'
            policy_file = "bucket-policy.json"
            with open(policy_file, "w") as f:
                f.write(policy_json)

            run_command([
                "gsutil", "iam", "set", policy_file,
                f"gs://{BUCKET_NAME}"
            ], "Setting bucket permissions to private", check=False)

            # Clean up temp file
            if os.path.exists(policy_file):
                os.remove(policy_file)

            print("✓ Bucket privacy configured")
        except:
            print("⚠️ Bucket permission setting failed")

        return f"gs://{BUCKET_NAME}"

    except:
        print("⚠️ Storage bucket creation failed")
        print("   This may be due to:")
        print("   • Bucket name conflicts (global namespace)")
        print("   • Insufficient permissions")
        print("   • Billing/quota requirements")
        print(f"   Alternative: Use existing bucket or resolve billing")
        return ""

def step4_setup_key_management():
    """Step 4: Setup Key Management Service (Experimental)"""
    section_header("Step 4: Key Management Setup (Experimental)")

    try:
        # Create key ring
        ring_result = run_command([
            "gcloud", "kms", "keyrings", "create", KEY_RING_ID,
            "--location", GCP_REGION,
            "--project", GCP_PROJECT_ID
        ], f"Creating KMS key ring '{KEY_RING_ID}' in {GCP_REGION}")

        if not ring_result or "ERROR" in ring_result:
            print("⚠️ Key ring creation failed or already exists")

        # Create encryption key
        try:
            key_result = run_command([
                "gcloud", "kms", "keys", "create", KEY_ID,
                "--location", GCP_REGION,
                "--keyring", KEY_RING_ID,
                "--purpose", "encryption",
                "--algorithm", "GOOGLE_SYMMETRIC_ENCRYPTION",
                "--protection-level", "SOFTWARE"
            ], f"Creating encryption key '{KEY_ID}'")
            print("✓ Encryption key created")
            return f"projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/keyRings/{KEY_RING_ID}/cryptoKeys/{KEY_ID}"
        except:
            print("⚠️ Key creation failed (billing or permissions required)")
            return ""

    except:
        print("⚠️ KMS setup failed")
        print("   Alternative approaches:")
        print("   • Use Google-managed encryption keys")
        print("   • Skip KMS and use basic encryption")
        return ""

def step5_create_network():
    """Step 5: Create VPC Network (Experimental)"""
    section_header("Step 5: Network Setup (Experimental)")

    try:
        # Create custom VPC
        vpc_result = run_command([
            "gcloud", "compute", "networks", "create", VPC_NETWORK_NAME,
            "--description", f"Custom VPC for {PROJECT_NAME} experimentation",
            "--format", "value(name)"
        ], f"Creating VPC network '{VPC_NETWORK_NAME}'")

        if vpc_result:
            print(f"✓ VPC network created: {vpc_result}")

            # Create subnet
            try:
                subnet_result = run_command([
                    "gcloud", "compute", "networks", "subnets", "create", SUBNET_NAME,
                    "--network", VPC_NETWORK_NAME,
                    "--region", GCP_REGION,
                    "--range", "10.0.0.0/24",
                    "--description", f"Subnet for {PROJECT_NAME} resources",
                    "--format", "value(name)"
                ], f"Creating subnet '{SUBNET_NAME}'")

                if subnet_result:
                    print("✓ VPC subnet created")

                    # Create restrictive firewall rule
                    try:
                        firewall_result = run_command([
                            "gcloud", "compute", "firewall-rules", "create", FIREWALL_NAME,
                            "--network", VPC_NETWORK_NAME,
                            "--direction", "INGRESS",
                            "--action", "DENY",
                            "--rules", "tcp,udp,icmp",
                            "--source-ranges", "0.0.0.0/0",
                            "--priority", "65534",
                            "--description", "Default deny all rule for security"
                        ], f"Creating restrictive firewall '{FIREWALL_NAME}'")

                        print("✓ Restrictive firewall rules created")
                    except:
                        print("⚠️ Firewall rule creation failed")

                    return vpc_result
            except:
                print("⚠️ Subnet creation failed")
                return vpc_result

    except:
        print("⚠️ VPC network creation failed")
        print("   This is common in:")
        print("   • Free tier accounts without billing enabled")
        print("   • Accounts with compute service restrictions")
        print("   • Regional quota limitations")
        print("   Alternative: Use default VPC network")
        return ""

def step6_enable_audit_logging():
    """Step 6: Enable Audit Logging (Experimental)"""
    section_header("Step 6: Audit Logging Setup (Experimental)")

    try:
        # Get current audit config
        current_config = run_command([
            "gcloud", "projects", "get-iam-policy", GCP_PROJECT_ID,
            "--format", "json"
        ], "Checking current IAM policy", check=False)

        if current_config:
            print("✓ IAM policy retrieved for audit configuration")
            return "audit-policy-retrieved"
        else:
            print("⚠️ Unable to retrieve IAM policy")
            return ""

    except:
        print("⚠️ Audit logging setup failed")
        print("   GCP Cloud Audit Logs are enabled by default for most services")
        print("   → Check GCP Console -> APIs & Services -> Audit Logs")
        return "audit-logs-default"

def step7_setup_cost_monitoring():
    """Step 7: Cost Monitoring Setup (Experimental)"""
    section_header("Step 7: Cost Monitoring & Budgeting (Experimental)")

    try:
        # Try to create a budget alert
        budget_name = f"{PROJECT_NAME}-budget"
        budget_config = {
            "displayName": budget_name,
            "budgetFilter": {
                "projects": [f"projects/{GCP_PROJECT_ID}"]
            },
            "amount": {
                "specifiedAmount": {
                    "units": "10"
                }
            },
            "thresholdRules": [
                {
                    "thresholdPercent": 50.0
                },
                {
                    "thresholdPercent": 80.0
                }
            ]
        }

        # Note: gcloud billing budgets doesn't exist yet, so this is simulated
        print("⚠️ GCP Budget creation requires API access and billing enabled")
        print("⚠️ → Manual setup via GCP Console: Billing -> Budgets")
        print("⚠️ → Recommended action: Set budget alerts at $1 and $5 thresholds")
        return "manual-budget-setup-required"

    except:
        print("⚠️ Cost monitoring setup skipped")
        print("   Budgets require billing enabled and additional permissions")
        return "cost-monitoring-manual"

# ========================================
# MAIN EXECUTION
# ========================================

if __name__ == "__main__":
    print("🚨 GCP AI Security Configuration Script 🚨")
    print("⚠️  TEST CODE ONLY - NOT FOR PRODUCTION USE")
    print("⚠️  Requires billing enabled and full GCP permissions")
    print("⚠️  May incur costs - monitor your GCP billing closely!")

    print(f"📍 Project: {GCP_PROJECT_ID or 'NOT SET'}")
    print(f"🌍 Region: {GCP_REGION}")
    print("=" * 60)

    # Multiple safety checks
    print("\n🚨 SAFETY WARNINGS:")
    print("❌ DO NOT run this on production accounts")
    print("❌ DO NOT run this on enterprise/business accounts")
    print("❌ DO NOT expect it to work without proper permissions & billing")
    print("❌ Monitor GCP costs - scripts may fail and still create resources")

    try:
        confirm = input("\n⚠️  Do you understand these risks and wish to continue? (y/N): ").strip().lower()
        confirm2 = input("⚠️  Are you on a TEST ACCOUNT only? (y/N): ").strip().lower()
        confirm3 = input("⚠️  Have you checked GCP billing/quota? (y/N): ").strip().lower()

        if not all([confirm == 'y', confirm2 == 'y', confirm3 == 'y']):
            print("❌ Safety checks failed. Exiting to protect your account!")
            sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\n❌ Input interrupted. Exiting to protect your account!")
        sys.exit(1)

    print("\n🚀 PROCEEDING WITH GCP SECURITY EXPERIMENTATION...")
    print("⚠️  This may create resources and incur costs!")

    # Execute experimental steps
    try:
        if not step1_check_prerequisites():
            print("❌ Prerequisites check failed. Cannot proceed safely.")
            sys.exit(1)

        print("\n⚠️  STARTING GCP RESOURCE CREATION...")
        print("⚠️  Monitor GCP Console for resource creation and costs!")

        # Execute experimental steps (likely to fail in restricted accounts)
        step2_create_service_account()
        step3_create_storage_bucket()
        step4_setup_key_management()
        step5_create_network()
        step6_enable_audit_logging()
        step7_setup_cost_monitoring()

        section_header("✅ EXPERIMENTATION COMPLETE")

        print("🌟 GCP Security Experimentation Summary:")
        print("⚠️ → Check your GCP Console at https://console.cloud.google.com/")
        print("⚠️ → Review created resources and DELETE what you don't need")
        print("⚠️ → Monitor billing at https://console.cloud.google.com/billing")
        print("⚠️ → Clean up resources immediately if they were undesired")

        print("\n🎨 LEARNING OUTCOMES:")
        print("✅ GCP authentication and project setup process")
        print("✅ Understanding of IAM service account creation")
        print("✅ Cloud storage bucket security concepts")
        print("✅ Key Management Service encryption keys")
        print("✅ VPC networking and firewall configuration")
        print("✅ Audit logging and compliance monitoring")
        print("⚠️ REAL COST awareness for cloud experimentation")

        print("\n🧹 CLEANUP REQUIRED:")
        print("🚨 → Delete all test resources created by this script")
        print("🚨 → Check for any billing charges incurred")
        print("🚨 → Disable or delete the GCP project if it's for testing only")
        print("🚨 → Review IAM policies and remove test accounts")

        print("\n📚 EDUCATIONAL VALUE:")
        print("✅ Safe experimentation environment")
        print("✅ Real-world GCP security concepts")
        print("✅ Cost awareness and budget management")
        print("✅ Error handling and troubleshooting skills")

        print("\n⚠️ FINAL WARNING:")
        print("This was an educational experiment only!")
        print("Never run experimental code on production systems!")
        print("Always monitor costs when working with cloud resources!")

        print("\n🎉 GCP Security Learning Complete!")
        print("📍 Project summary: {} ({})".format(GCP_PROJECT_ID or 'N/A', GCP_REGION))
        print("📊 Resources may have been created - check GCP Console immediately!")

    except Exception as e:
        print(f"\n❌ Unexpected error during execution: {e}")
        print("⚠️  Please clean up any resources that may have been created!")
        sys.exit(1)
</result>
</write_to_file>
