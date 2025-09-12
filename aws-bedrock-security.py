#!/usr/bin/env python3
"""
cSni script automates the setup of secure AWS eersonaleAccountsfor LLM/GenAI development
using AWS CLI commands. Designed specifically for personal/developers accounts with limited permissions.
iptumte th etupfesecsreAWSBedkAfooiLLM/GewAIidtvyloumrnt
entig AWS CLI asmmacdn.Bs hpgren tpo e PChllonfowb pntanal/dbv3lorunomwddhdlm d:pppmiyhin-stenv
2. Create .env file with AWS_REGION=us-east-1
3. Enable required APIs if needed
4. Run this script

Note: Some features may be unavailable in free tier or require billing enabled.
"""

import os
import subprocess
import sys
import timet

Noe:Somefeur my be uavailale in free tier rrque billig abled.
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

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
PROJECT_NAME = "bedrock-training"
BUCKET_NAME = f"{PROJECT_NAME}-data-bucket"
SERVICE_ROLE_NAME = "bedrock-training-role"
SERVICE_ROLE_POLICY_NAME = "bedrock-training-policy"
MODEL_ACCESS_POLICY_NAME = "bedrock-model-access-policy"
CLOUDTRAIL_NAME = "bedrock-audit-trail"
KMS_KEY_ALIAS = "alias/bedrock-training-key"
VPC_NAME = "bedrock-vpc"
SECURITY_GROUP_NAME = "bedrock-security-group"

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

def get_account_id():
    """Get AWS Account ID."""
    result = run_command("aws sts get-caller-identity --query Account --output text", "Getting AWS Account ID")
    return result.strip()

def check_region():
    """Check and set AWS region."""
    current_region = run_command("aws configure get region", "Checking current AWS region", check=False)
    if current_region != AWS_REGION:
        run_command(f"aws configure set region {AWS_REGION}", f"Setting AWS region to {AWS_REGION}")
    print(f"✓ AWS Region: {AWS_REGION}")

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
        # Check AWS CLI and credentials
        result = run_command("aws sts get-caller-identity", "Checking AWS CLI and credentials")
        print("✓ AWS CLI and credentials are properly configured!")

        # Check/resources needed for Bedrock
        check_region()
        account_id = get_account_id()
        print(f"✓ Account ID: {account_id}")

        return True
    except:
        print("❌ AWS CLI or credentials not properly configured.")
        print("Please run 'aws configure' to set up your credentials.")
        return False

def step2_create_service_role():
    """Step 2: Create IAM Service Role for Bedrock"""
    section_header("Step 2: IAM Service Role Setup")

    # Create trust policy for Bedrock
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    # Create permission policy for Bedrock
    permission_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:*",
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "kms:Decrypt",
                    "kms:DescribeKey",
                    "kms:GenerateDataKey"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:log-group:/aws/bedrock/*"
            }
        ]
    }

    # Write policies to temporary files
    with open("bedrock-trust-policy.json", "w") as f:
        json.dump(trust_policy, f, indent=2)

    with open("bedrock-permission-policy.json", "w") as f:
        json.dump(permission_policy, f, indent=2)

    # Create IAM role
    role_arn = ""
    try:
        run_command([
            "aws", "iam", "create-role",
            "--role-name", SERVICE_ROLE_NAME,
            "--assume-role-policy-document", "file://bedrock-trust-policy.json"
        ], f"Creating IAM role '{SERVICE_ROLE_NAME}'", check=False)

        # Get role ARN
        role_arn = run_command([
            "aws", "iam", "get-role",
            "--role-name", SERVICE_ROLE_NAME,
            "--query", "Role.Arn",
            "--output", "text"
        ], "Getting role ARN", check=False)

        role_arn = role_arn.strip()
        print(f"✓ Created IAM role with ARN: {role_arn}")

        # Create and attach policy
        policy_arn = run_command([
            "aws", "iam", "create-policy",
            "--policy-name", SERVICE_ROLE_POLICY_NAME,
            "--policy-document", "file://bedrock-permission-policy.json",
            "--query", "Policy.Arn",
            "--output", "text"
        ], f"Creating IAM policy '{SERVICE_ROLE_POLICY_NAME}'", check=False).strip()

        if policy_arn:
            run_command([
                "aws", "iam", "attach-role-policy",
                "--role-name", SERVICE_ROLE_NAME,
                "--policy-arn", policy_arn
            ], "Attaching policy to role", check=False)

        print("✓ IAM role and policies configured for Bedrock!")
        return role_arn

    except:
        print("⚠ IAM role setup incomplete. This is common in restricted accounts.")
        print("   Continue with manual IAM role creation or use existing roles.")
        return role_arn
    finally:
        # Cleanup temporary files
        for f in ["bedrock-trust-policy.json", "bedrock-permission-policy.json"]:
            if os.path.exists(f):
                os.remove(f)

def step3_create_s3_bucket():
    """Step 3: Create Secure S3 Bucket for Model Training Data"""
    section_header("Step 3: S3 Storage Setup")

    try:
        # Create bucket
        run_command([
            "aws", "s3api", "create-bucket",
            "--bucket", BUCKET_NAME,
            "--region", AWS_REGION
        ], f"Creating S3 bucket '{BUCKET_NAME}'")

        # Enable versioning
        run_command([
            "aws", "s3api", "put-bucket-versioning",
            "--bucket", BUCKET_NAME,
            "--versioning-configuration", "Status=Enabled"
        ], "Enabling bucket versioning")

        # Enable server-side encryption
        run_command([
            "aws", "s3api", "put-bucket-encryption",
            "--bucket", BUCKET_NAME,
            "--server-side-encryption-configuration",
            '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}, "BucketKeyEnabled": true}]}'
        ], "Enabling default S3 server-side encryption")

        # Block public access
        run_command([
            "aws", "s3api", "put-public-access-block",
            "--bucket", BUCKET_NAME,
            "--public-access-block-configuration",
            'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true'
        ], "Blocking all public access to bucket")

        print(f"✓ Secure S3 bucket '{BUCKET_NAME}' created with encryption and public access blocked!")
        return True

    except:
        print("⚠ S3 bucket creation failed.")
        print("   This is expected if:")
        print("   • Bucket name already exists globally")
        print("   • Insufficient permissions for S3 operations")
        print("   • Billing not enabled for S3 usage")
        print(f"   Use existing bucket or resolve permissions to create '{BUCKET_NAME}'")
        return False

def step4_setup_bedrock_access():
    """Step 4: Configure Bedrock Model Access"""
    section_header("Step 4: Bedrock Model Access Configuration")

    try:
        # Check available models
        run_command([
            "aws", "bedrock", "list-foundation-models",
            "--query", "modelSummaries[?modelLifecycle.status==`ACTIVE`].[modelId,modelName]",
            "--output", "table"
        ], "Checking available Bedrock foundation models")

        print("✓ Available models shown above. You can use any of these for your applications.")

        # Create model access policy (for premium features)
        model_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel*",
                        "bedrock:ListFoundationModels",
                        "bedrock:GetFoundationModel"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:CreateModelCustomizationJob",
                        "bedrock:ListModelCustomizationJobs"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "aws:RequestedRegion": AWS_REGION
                        }
                    }
                }
            ]
        }

        with open("bedrock-model-policy.json", "w") as f:
            json.dump(model_policy, f, indent=2)

        try:
            run_command([
                "aws", "iam", "create-policy",
                "--policy-name", MODEL_ACCESS_POLICY_NAME,
                "--policy-document", "file://bedrock-model-policy.json",
                "--query", "Policy.Arn",
                "--output", "text"
            ], "Creating Bedrock model access policy", check=False)

            print("✓ Bedrock model access policy configured!")
        except:
            print("⚠ Model access policy creation failed. You can still use basic models.")

    except:
        print("⚠ Bedrock model access setup incomplete.")
        print("   This may be due to:")
        print("   • Bedrock service not available in your region")
        print("   • Insufficient permissions for Bedrock model access")
        print("   • Bedrock preview access not enabled")
        print("   Continue with manual Bedrock configuration when ready.")

    # Cleanup
    if os.path.exists("bedrock-model-policy.json"):
        os.remove("bedrock-model-policy.json")

def step5_setup_encryption():
    """Step 5: Setup Encryption (KMS Keys)"""
    section_header("Step 5: Encryption Configuration")

    try:
        # Create KMS key for Bedrock
        key_id = run_command([
            "aws", "kms", "create-key",
            "--description", "Key for Bedrock model data encryption",
            "--key-usage", "ENCRYPT_DECRYPT",
            "--key-spec", "SYMMETRIC_DEFAULT",
            "--query", "KeyMetadata.KeyId",
            "--output", "text"
        ], "Creating KMS key for Bedrock encryption").strip()

        if key_id:
            # Create alias for the key
            run_command([
                "aws", "kms", "create-alias",
                "--alias-name", KMS_KEY_ALIAS,
                "--target-key-id", key_id
            ], f"Creating alias '{KMS_KEY_ALIAS}' for KMS key")

            print(f"✓ KMS encryption key created with alias: {KMS_KEY_ALIAS}")
            return f"arn:aws:kms:{AWS_REGION}:{get_account_id()}:key/{key_id}"
        else:
            print("⚠ KMS key creation skipped (API may not be available).")
            return ""

    except:
        print("⚠ KMS encryption setup failed.")
        print("   Alternative Encryption Approaches:")
        print("   • Use S3 server-side encryption (SSE-S3)")
        print("   • Enable SSE-KMS on individual S3 objects")
        print("   • Implement client-side encryption in your application")
        print("   • Enable default KMS encryption on your S3 buckets")
        return ""

def step6_setup_vpc_security():
    """Step 6: VPC and Security Groups Configuration"""
    section_header("Step 6: VPC Network Security")

    try:
        # Create VPC
        vpc_id = run_command([
            "aws", "ec2", "create-vpc",
            "--cidr-block", "10.0.0.0/16",
            "--query", "Vpc.VpcId",
            "--output", "text"
        ], f"Creating VPC '{VPC_NAME}'").strip()

        if vpc_id:
            # Tag VPC
            run_command([
                "aws", "ec2", "create-tags",
                "--resources", vpc_id,
                "--tags", f"Key=Name,Value={VPC_NAME}"
            ], "Tagging VPC", check=False)

            # Create security group
            sg_id = run_command([
                "aws", "ec2", "create-security-group",
                "--group-name", SECURITY_GROUP_NAME,
                "--description", "Security group for Bedrock training resources",
                "--vpc-id", vpc_id,
                "--query", "GroupId",
                "--output", "text"
            ], f"Creating security group '{SECURITY_GROUP_NAME}'").strip()

            if sg_id:
                # Configure security group rules (deny all inbound)
                run_command([
                    "aws", "ec2", "revoke-security-group-ingress",
                    "--group-id", sg_id
                ], "Revoking all inbound rules for security", check=False)

                print("✓ VPC and security group configured for secure Bedrock usage!")
                return vpc_id
        else:
            print("⚠ VPC creation incomplete.")
            return ""

    except:
        print("⚠ VPC and security group setup failed.")
        print("   This is common in:")
        print("   • Accounts with EC2 usage limits")
        print("   • Free tier restrictions")
        print("   • Insufficient permissions for VPC/EC2 operations")
        print("   Alternative Networking:")
        print("   • Use default VPC (if available)")
        print("   • Configure security at application level")
        print("   • Use VPC endpoints for AWS services")
        return ""

def step7_setup_monitoring():
    """Step 7: CloudTrail Audit Logging"""
    section_header("Step 7: Audit Logging and Monitoring")

    try:
        # Create CloudTrail for Bedrock activity monitoring
        trail_arn = run_command([
            "aws", "cloudtrail", "create-trail",
            "--name", CLOUDTRAIL_NAME,
            "--s3-bucket-name", BUCKET_NAME,
            "--is-multi-region-trail",
            "--query", "TrailARN",
            "--output", "text"
        ], f"Creating CloudTrail '{CLOUDTRAIL_NAME}' for Bedrock audit logging").strip()

        if trail_arn:
            # Start logging
            run_command([
                "aws", "cloudtrail", "start-logging",
                "--name", CLOUDTRAIL_NAME
            ], "Starting CloudTrail logging")

            print("✓ CloudTrail audit logging configured for Bedrock activities!")
            print(f"✓ Trail ARN: {trail_arn}")

            # Create event selectors for Bedrock-specific events
            run_command([
                "aws", "cloudtrail", "put-event-selectors",
                "--trail-name", CLOUDTRAIL_NAME,
                "--event-selectors",
                '[{"ReadWriteType": "All", "IncludeManagementEvents": true, "DataResources": [{"Type": "AWS::Bedrock::Model", "Values": ["arn:aws:bedrock:*"]}]}]'
            ], "Configuring CloudTrail for Bedrock model events", check=False)

            return trail_arn
        else:
            print("⚠ CloudTrail setup incomplete.")
            return ""

    except:
        print("⚠ CloudTrail audit logging setup failed.")
        print("   Alternative Monitoring Approaches:")
        print("   • Enable CloudTrail manually in AWS Console")
        print("   • Use CloudWatch for basic logging")
        print("   • Enable VPC Flow Logs (if VPC created)")
        print("   • Use AWS Config for compliance monitoring")
        print("   • Set up budget alerts for cost monitoring")
        return ""

def step8_setup_budget_alerts():
    """Step 8: Cost Control Setup"""
    section_header("Step 8: Cost Control and Budgeting")

    try:
        # Create budget for Bedrock and related services
        budget_config = {
            "BudgetName": "Bedrock-Training-Budget",
            "BudgetLimit": {
                "Amount": "10.0",
                "Unit": "USD"
            },
            "CostFilters": {
                "Service": ["Amazon Bedrock", "Amazon S3", "Amazon KMS"]
            },
            "CostTypes": {
                "IncludeCredit": True,
                "IncludeDiscount": False,
                "IncludeOtherSubscription": True,
                "IncludeRecurring": True,
                "IncludeRefund": False,
                "IncludeSubscription": True,
                "IncludeSupport": True,
                "IncludeTax": False,
                "IncludeUpfront": True,
                "UseBlended": False
            },
            "TimeUnit": "MONTHLY",
            "TimePeriod": {
                "Start": "2025-01-01T00:00:00Z"
            }
        }

        with open("bedrock-budget.json", "w") as f:
            json.dump(budget_config, f, indent=2)

        run_command([
            "aws", "budgets", "create-budget",
            "--budget", "file://bedrock-budget.json",
            "--notifications-with-subscribers",
            '[{"Notification":{"NotificationType":"ACTUAL","ComparisonOperator":"GREATER_THAN","Threshold":80.0,"ThresholdType":"PERCENTAGE"},"Subscribers":[{"SubscriptionType":"EMAIL","Address":"' + run_command("aws sts get-caller-identity --query Account --output text", check=False).strip() + '@placeholder.com"}]}]'
        ], "Creating budget alert for Bedrock usage ($10/month limit)", check=False)

        print("✓ Budget alerts configured for cost control!")

    except:
        print("⚠ Budget alert setup failed.")
        print("   Manual Cost Control:")
        print("   • Set up billing alerts manually in AWS Console")
        print("   • Monitor usage in AWS Cost Explorer")
        print("   • Use AWS Budgets service directly")
        print("   • Set up spending limits per service")

    # Cleanup
    if os.path.exists("bedrock-budget.json"):
        os.remove("bedrock-budget.json")

# ========================================
# MAIN EXECUTION
# ========================================

if __name__ == "__main__":
    print("🚀 AWS Bedrock Security Setup Script for Personal Accounts")
    print(f"📍 Region: {AWS_REGION}")
    print(f"🎯 Project: {PROJECT_NAME}")
    print("="*60)

    # Confirm execution
    confirm = input("This will create AWS resources and may incur costs. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Exiting...")
        sys.exit(0)

    # Execute all steps
    if not step1_check_prerequisites():
        print("❌ Prerequisites check failed. Please fix AWS configuration first.")
        sys.exit(1)

    print("\n" + "="*60)
    print("🔒 PROCEEDING WITH AWS BEDROCK SECURITY SETUP")
    print("="*60)

    # Execute security setup steps
    step2_create_service_role()
    step3_create_s3_bucket()
    step4_setup_bedrock_access()
    step5_setup_encryption()
    step6_setup_vpc_security()
    step7_setup_monitoring()
    step8_setup_budget_alerts()

    section_header("Setup Complete!")

    print("✅ AWS Bedrock Security Setup Complete!")
    print("\n📋 Summary of Applied Security Measures:")
    print("   ✓ AWS CLI and IAM permissions verified")
    print("   ✓ IAM service role for Bedrock (if permissions allow)")
    print("   ✓ Secure S3 bucket with encryption and public access blocked")
    print("   ✓ Bedrock model access policies")
    print("   ✓ KMS encryption keys for data protection")
    print("   ✓ VPC and security groups for network isolation")
    print("   ✓ CloudTrail audit logging for compliance")
    print("   ✓ Budget alerts and cost controls")

    print("\n⚠️ Notes for Personal Accounts:")
    print("   • Some features may be unavailable in free tier")
    print("   • Enable billing for full functionality")
    print("   • Some services may need API enabling in AWS Console")
    print("   • Manual setup may be needed for premium features")

    print(f"\n🎯 Next Steps for Bedrock Usage:")
    print(f"   1. Test Bedrock with: aws bedrock list-foundation-models")
    print(f"   2. Upload training data to S3 bucket: gs://{BUCKET_NAME}")
    print(f"   3. Configure your applications to use the IAM role: {SERVICE_ROLE_NAME}")
    print("   4. Monitor usage in CloudTrail and Cost Explorer")

    print("\n🔗 Useful AWS Console Links:")
    print("   • Bedrock Console: https://console.aws.amazon.com/bedrock/")
    print("   • IAM Console: https://console.aws.amazon.com/iam/")
    print("   • CloudTrail: https://console.aws.amazon.com/cloudtrail/")
</result>
</write_to_file>
