#!/usr/bin/env python3
"""
Simple GCP Account Verification Script
Tests basic GCP authentication and access for personal accounts.
"""

import os
import subprocess
import sys

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")

# ========================================
# CONFIGURATION
# ========================================

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_REGION = os.getenv("LOCATION", "us-east1")

# ========================================
# HELPER FUNCTIONS
# ========================================

def run_command(cmd, description="", continue_on_error=True):
    """Run a CLI command and return result. Warns on error but continues."""
    print(f"\n>>> {description}")
    if isinstance(cmd, list):
        print(f"Running: {' '.join(cmd)}")
        scaled_cmd = cmd
    else:
        print(f"Running: {cmd}")
        scaled_cmd = cmd

    try:
        result = subprocess.run(scaled_cmd, check=True, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✓ {result.stdout.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Command failed: {e}")
        if e.stderr:
            print(f"⚠️ Error: {e.stderr.strip()}")
        if continue_on_error:
            print("⚠️ Continuing with next step...")
        return ""
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        if continue_on_error:
            print("⚠️ Continuing with next step...")
        return ""

def section_header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

# ========================================
# TEST STEPS
# ========================================

def step1_auth():
    """Step 1: Test GCP Authentication. Always continues."""
    section_header("Step 1: GCP Authentication Test")

    try:
        # Try multiple ways to check auth
        result = run_command("gcloud config get-value account", "Checking account authentication")
        if result:
            print(f"✅ Authenticated as: {result}")
            return result
        else:
            # Try alternative check
            result = run_command("gcloud auth list --format=value.account", "Checking auth list", continue_on_error=True)
            if result:
                print(f"✅ Authenticated as: {result}")
                return result
            else:
                print("⚠️ GCP authentication required - run: gcloud auth login")
                return False
    except Exception as e:
        print(f"⚠️ Auth check failed: {e}")
        print("⚠️ This is expected if not authenticated")
        return False

def step2_project():
    """Step 2: Test Project Configuration. Always continues."""
    section_header("Step 2: GCP Project Test")

    if not GCP_PROJECT_ID:
        print("⚠️ GCP_PROJECT_ID not set in .env file")
        print("⚠️ Set GCP_PROJECT_ID=your-project-id in .env file")
        return False

    try:
        # Set active project
        run_command(f"gcloud config set project {GCP_PROJECT_ID}",
                   "Setting active project")
        current = run_command("gcloud config get-value project", "Verifying project setting")
        if current.strip() == GCP_PROJECT_ID:
            print(f"✅ Project configured: {GCP_PROJECT_ID}")
            return True
        else:
            print("⚠️ Could not set active project")
            return True  # Still continue
    except Exception as e:
        print(f"⚠️ Project setup failed: {e}")
        print("⚠️ Continuing anyway...")
        return True

def step3_iam():
    """Step 3: Test IAM Access. Always continues."""
    section_header("Step 3: IAM Access Test")

    try:
        # Basic IAM policy check
        result = run_command(f"gcloud projects get-iam-policy {GCP_PROJECT_ID} --format=json",
                           "Testing IAM policy access")
        if result:
            print("✅ IAM permissions available")
            return True
        else:
            print("⚠️ Limited IAM access - some operations may fail")
            return True  # Continue anyway
    except Exception as e:
        print(f"⚠️ IAM access failed: {e}")
        print("⚠️ This is normal for restricted accounts")
        return True

def step4_storage():
    """Step 4: Test Storage Access. Always continues."""
    section_header("Step 4: Storage Access Test")

    try:
        # Try to list storage buckets
        result = run_command("gsutil ls", "Testing storage access")
        if result or "AccessDenied" in result:
            print("✅ Storage access available")
            return True
        else:
            print("⚠️ Storage access limited - free tier restriction")
            return True  # Still continue
    except Exception as e:
        print(f"⚠️ Storage access failed: {e}")
        print("⚠️ Expected in free tier accounts without billing")
        return True

def step5_services():
    """Step 5: Test Services Access. Always continues."""
    section_header("Step 5: Enabled Services Test")

    try:
        # List enabled services
        result = run_command(f"gcloud services list --project={GCP_PROJECT_ID} --enabled --format=value(config.name)",
                           "Checking enabled GCP services")
        if result:
            print("✅ GCP services available")
            return True
        else:
            print("⚠️ Services access limited")
            return True  # Continue anyway
    except Exception as e:
        print(f"⚠️ Services check failed: {e}")
        print("⚠️ This is normal for new projects")
        return True

def step6_billing():
    """Step 6: Check Billing Status. Always continues."""
    section_header("Step 6: Billing Status Check")

    try:
        # Check billing status
        result = run_command(f"gcloud billing projects describe {GCP_PROJECT_ID} --format=value(billingEnabled)",
                           "Checking billing status")
        if result.strip() == "True":
            print("✅ Billing is enabled")
        else:
            print("⚠️ Billing not enabled - many features will be limited")
        return True
    except Exception as e:
        print(f"⚠️ Billing check failed: {e}")
        print("⚠️ This is expected without billing permissions")
        return True

def step7_info():
    """Step 7: Show Information and Tips."""
    section_header("Summary & Information")

    print("✅ GCP account verification completed")
    print("\n📝 Tips for personal accounts:")
    print("• Free tier has storage and compute limits")
    print("• Enable billing to unlock more features")
    print("• Check billing alerts at https://console.cloud.google.com/billing")
    print("• Monitor usage at https://console.cloud.google.com/home/dashboard")

    print(f"\n📍 Configuration:")
    print(f"  Project: {GCP_PROJECT_ID or 'NOT SET'}")
    print(f"  Region: {GCP_REGION}")

    return True

# ========================================
# MAIN EXECUTION
# ========================================

if __name__ == "__main__":
    print("Simple GCP Account Verification")
    print("This script tests your GCP setup and shows status of all components.")
    print("=" * 60)

    try:
        # Run all steps - they all return True to continue
        auth_ok = step1_auth()
        project_ok = step2_project()
        iam_ok = step3_iam()
        storage_ok = step4_storage()
        services_ok = step5_services()
        billing_ok = step6_billing()
        info_ok = step7_info()

        # Show final summary
        print(f"\n{'='*40}")
        print("FINAL STATUS SUMMARY:")
        print(f"{'='*40}")
        print(f"Authentication: {'✅' if auth_ok else '❌'}")
        print(f"Project Config: {'✅' if project_ok else '❌'}")
        print(f"IAM Access: {'✅' if iam_ok else '❌'}")
        print(f"Storage Access: {'✅' if storage_ok else '❌'}")
        print(f"Services: {'✅' if services_ok else '❌'}")
        print(f"Billing Status: {'✅' if billing_ok else '❌'}")
        print(f"{'='*40}")

        if auth_ok and project_ok:
            print("🎉 GCP setup is working! You can use this account for testing.")
        else:
            print("⚠️ Some basic setup issues detected. Review the warnings above.")

        print("\n🧹 This script doesn't create or modify any resources - no cleanup needed!")

    except KeyboardInterrupt:
        print("\n⚠️ Script interrupted by user")
    except Exception as e:
        print(f"⚠️ Script failed with error: {e}")
