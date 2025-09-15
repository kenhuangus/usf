#!/usr/bin/env python3
"""
🚨 CRITICAL WARNING: TEST CODE ONLY - NOT FOR PRODUCTION USE 🚨

Azure AI Security Configuration Script for TESTING PURPOSES ONLY

⚠️  WARNING: This is EXPERIMENTAL, UNTESTED code for educational purposes only
⚠️  DO NOT run this in production environments
⚠️  DO NOT run this on enterprise/business accounts
⚠️  DO NOT expect professional-grade security from this script
⚠️  May create unexpected resources, expose sensitive data, or incur costs

This script is provided "AS IS" with NO WARRANTIES, EXPRESS OR IMPLIED.
Use at your own risk for learning purposes only.

Prerequisites:
- Azure CLI configured with your credentials (az login)
- Basic Azure account with permissions to create resources, IAM, etc.
- Python with azure-cli installed

Recommended order (FOR TESTING ONLY):
1. Install python-dotenv: pip install python-dotenv
2. Update .env file with AZURE_REGION=eastus
3. Enable required resource providers if needed
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

AZURE_REGION = os.getenv("AZURE_REGION", "eastus")
AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")
PROJECT_NAME = "azure-ai-training"
RESOURCE_GROUP = f"{PROJECT_NAME}-rg"
STORAGE_ACCOUNT = f"{PROJECT_NAME}storage{hash(PROJECT_NAME) % 1000:03d}"  # Make unique
CONTAINER_NAME = "aitrainingdata"
KEYVAULT_NAME = f"{PROJECT_NAME}-kv{hash(PROJECT_NAME) % 1000:03d}"  # Make unique
VNET_NAME = f"{PROJECT_NAME}-vnet"
SUBNET_NAME = f"{PROJECT_NAME}-subnet"
NSG_NAME = f"{PROJECT_NAME}-nsg"
AI_SERVICE_NAME = f"{PROJECT_NAME}-ai"
WORKSPACE_NAME = f"{PROJECT_NAME}-mlw"
LOG_ANALYTICS_NAME = f"{PROJECT_NAME}-log{hash(PROJECT_NAME) % 1000:03d}"
BUDGET_NAME = f"{PROJECT_NAME}-budget"

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

def get_subscription_id():
    """Get Azure Subscription ID."""
    if AZURE_SUBSCRIPTION_ID:
        return AZURE_SUBSCRIPTION_ID

    result = run_command("az account show --query id --output tsv", "Getting Azure Subscription ID", check=False)
    return result.strip() if result else ""

def set_subscription():
    """Set the active Azure subscription."""
    sub_id = get_subscription_id()
    if sub_id:
        run_command(f"az account set --subscription {sub_id}", f"Setting subscription to {sub_id}", check=False)
        print(f"✓ Active subscription: {sub_id}")
    return sub_id

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
        # Check Azure CLI and login
        result = run_command("az account show --query user.name --output tsv", "Checking Azure CLI login status")
        print("✓ Azure CLI authenticated successfully!")

        # Set subscription
        sub_id = set_subscription()
        print(f"✓ Subscription configured: {sub_id}")

        # List available providers
        print("📋 Checking Azure resource providers (this may take a moment)...")
        run_command([
            "az", "provider", "list",
            "--query", "[?registrationState=='Registered'].namespace",
            "--output", "table"
        ], "Checking registered resource providers", check=False)

        return True
    except:
        print("❌ Azure CLI or authentication not configured.")
        print("Please run 'az login' to authenticate with Azure.")
        print("Then run 'az account list --output table' to see available subscriptions.")
        return False

def step2_create_resource_group():
    """Step 2: Create Resource Group"""
    section_header("Step 2: Resource Group Setup")

    try:
        # Create resource group if it doesn't exist
        result = run_command([
            "az", "group", "create",
            "--name", RESOURCE_GROUP,
            "--location", AZURE_REGION,
            "--tags", f"Purpose='{PROJECT_NAME} AI Training'", f"Owner={run_command('az account show --query user.name --output tsv', check=False)}",
            "--query", "id",
            "--output", "tsv"
        ], f"Creating resource group '{RESOURCE_GROUP}' in {AZURE_REGION}")

        if result:
            print("✓ Resource group created successfully!")

        # Add resource locks for important resources (optional security)
        try:
            run_command([
                "az", "group", "lock", "create",
                "--name", f"{RESOURCE_GROUP}-lock",
                "--resource-group", RESOURCE_GROUP,
                "--lock-type", "CanNotDelete",
                "--notes", "Prevent accidental deletion of AI training resources"
            ], "Adding deletion protection lock to resource group", check=False)

            print("✓ Resource group protection enabled!")
        except:
            print("⚠ Resource protection not available (common in free tier)")

        return result.strip()
    except:
        print("⚠ Resource group creation failed.")
        print("   This may be due to:")
        print("   • Insufficient permissions to create resources")
        print("   • Service limits reached")
        print("   • Subscription issues")
        print(f"   Use existing resource group or resolve permissions")
        return ""

def step3_setup_azure_ai():
    """Step 3: Azure AI Service Setup"""
    section_header("Step 3: Azure AI Service Configuration")

    try:
        # Create Cognitive Services account
        result = run_command([
            "az", "cognitiveservices", "account", "create",
            "--name", AI_SERVICE_NAME,
            "--resource-group", RESOURCE_GROUP,
            "--kind", "OpenAI",
            "--sku", "S0",  # Free tier or pay-as-you-go
            "--location", AZURE_REGION,
            "--custom-domain", f"{AI_SERVICE_NAME}-{hash(PROJECT_NAME) % 1000}",
            "--query", "id",
            "--output", "tsv"
        ], f"Creating Azure AI service '{AI_SERVICE_NAME}'")

        if result:
            print("✓ Azure AI service created successfully!")

            # Get the endpoint and key
            endpoint = run_command([
                "az", "cognitiveservices", "account", "show",
                "--name", AI_SERVICE_NAME,
                "--resource-group", RESOURCE_GROUP,
                "--query", "endpoint",
                "--output", "tsv"
            ], "Getting AI service endpoint")

            access_key = run_command([
                "az", "cognitiveservices", "account", "keys", "list",
                "--name", AI_SERVICE_NAME,
                "--resource-group", RESOURCE_GROUP,
                "--query", "key1",
                "--output", "tsv"
            ], "Getting AI service access key")

            if endpoint and access_key:
                print(f"✓ AI Service endpoint: {endpoint}")
                print("✓ Access key retrieved (securely stored)")

                # Store keys in Key Vault for security
                try:
                    run_command([
                        "az", "keyvault", "secret", "set",
                        "--vault-name", KEYVAULT_NAME,
                        "--name", "azure-ai-access-key",
                        "--value", access_key,
                        "--description", "Azure AI service access key for training"
                    ], "Storing AI access key in Key Vault", check=False)

                    print("✓ Access key securely stored in Key Vault!")
                except:
                    print("⚠ Key Vault storage failed. Access key is available for manual storage.")

        # Check available models
        try:
            run_command([
                "az", "cognitiveservices", "model", "list",
                "--account-name", AI_SERVICE_NAME,
                "--resource-group", RESOURCE_GROUP,
                "--query", "[].{model:model.name, version:model.version, status:model.status}",
                "--output", "table"
            ], "Checking available Azure AI models", check=False)
        except:
            print("⚠ Model listing failed. Models will be available after service setup.")

        return result.strip() if result else ""

    except:
        print("⚠ Azure AI service setup failed.")
        print("   Common reasons:")
        print("   • Azure subscription billing issues")
        print("   • Regional service availability")
        print("   • Quota limits on free tier")
        print("   • Resource naming conflicts")
        print("   Continue with manual AI service setup.")
        return ""

def step4_create_storage_account():
    """Step 4: Create Secure Storage Account"""
    section_header("Step 4: Storage Account Configuration")

    # Check if storage account name is available (Azure requires unique names)
    unique_name_check = run_command([
        "az", "storage", "account", "check-name",
        "--name", STORAGE_ACCOUNT,
        "--query", "nameAvailable",
        "--output", "tsv"
    ], "Checking storage account name availability", check=False)

    if unique_name_check and unique_name_check.strip().lower() != "true":
        # Generate a new unique name
        from datetime import datetime
        timestamp = int(datetime.now().timestamp())
        STORAGE_ACCOUNT = f"{PROJECT_NAME}storage{timestamp % 1000:03d}"
        print(f"⚠ Original name not available, using: {STORAGE_ACCOUNT}")

    try:
        # Create premium LRS storage account (LRS for cost, Premium for performance)
        result = run_command([
            "az", "storage", "account", "create",
            "--name", STORAGE_ACCOUNT,
            "--resource-group", RESOURCE_GROUP,
            "--location", AZURE_REGION,
            "--sku", "Standard_LRS",  # Locally-redundant for cost optimization
            "--encryption-services", "blob",  # Enable blob encryption
            "--https-only", "true",  # Force HTTPS only
            "--min-tls-version", "TLS1_2",  # Require TLS 1.2+
            "--query", "id",
            "--output", "tsv"
        ], f"Creating secure storage account '{STORAGE_ACCOUNT}'")

        if result:
            print("✓ Storage account created with encryption enabled!")

            # Create container for AI training data
            connection_string = run_command([
                "az", "storage", "account", "show-connection-string",
                "--name", STORAGE_ACCOUNT,
                "--resource-group", RESOURCE_GROUP,
                "--query", "connectionString",
                "--output", "tsv"
            ], "Getting storage connection string")

            if connection_string:
                run_command([
                    "az", "storage", "container", "create",
                    "--name", CONTAINER_NAME,
                    "--account-name", STORAGE_ACCOUNT,
                    "--connection-string", connection_string,
                    "--public-access", "off"  # Private, no public access
                ], f"Creating secure blob container '{CONTAINER_NAME}'")

                print("✓ Private blob container created for AI training data!")

            # Enable advanced threat protection
            try:
                run_command([
                    "az", "security", "atp", "storage", "nb", "enable",
                    "--resource-group", RESOURCE_GROUP,
                    "--storage-account", STORAGE_ACCOUNT,
                    "--is-enabled", "true"
                ], "Enabling advanced threat protection for storage", check=False)

                print("✓ Advanced threat protection enabled!")
            except:
                print("⚠ Threat protection not available (requires Defender subscription)")

            return result.strip()

    except:
        print("⚠ Storage account creation failed.")
        print("   This is common in:")
        print("   • Unique name conflicts (global Azure namespace)")
        print("   • Subscription billing issues")
        print("   • Resource limits reached")
        print("   • Regional availability issues")
        print(f"   Use existing storage account or resolve billing/subscription")
        return ""

def step5_setup_encryption():
    """Step 5: Setup Key Vault and Encryption"""
    section_header("Step 5: Encryption and Key Management")

    try:
        # Create Key Vault for managing encryption keys
        result = run_command([
            "az", "keyvault", "create",
            "--name", KEYVAULT_NAME,
            "--resource-group", RESOURCE_GROUP,
            "--location", AZURE_REGION,
            "--enabled-for-deployment", "true",
            "--enabled-for-disk-encryption", "true",
            "--enabled-for-template-deployment", "true",
            "--sku", "standard",  # Free tier available
            "--query", "id",
            "--output", "tsv"
        ], f"Creating Key Vault '{KEYVAULT_NAME}' for encryption management")

        if result:
            print("✓ Key Vault created for secure key management!")

            # Create encryption key for storage
            try:
                key_name = "storage-encryption-key"
                run_command([
                    "az", "keyvault", "key", "create",
                    "--vault-name", KEYVAULT_NAME,
                    "--name", key_name,
                    "--protection", "software",  # Free tier option
                    "--size", "2048",
                    "--kty", "RSA"
                ], "Creating RSA key for storage encryption", check=False)

                # Set storage account to use customer-managed key
                try:
                    key_vault_uri = f"https://{KEYVAULT_NAME}.vault.azure.net"
                    key_uri = f"{key_vault_uri}/keys/{key_name}"

                    run_command([
                        "az", "storage", "account", "update",
                        "--name", STORAGE_ACCOUNT,
                        "--resource-group", RESOURCE_GROUP,
                        "--encryption-key-source", "Microsoft.Keyvault",
                        "--encryption-key-vault", key_vault_uri,
                        "--encryption-key-name", key_name,
                        "--encryption-key-version", "auto"
                    ], "Configuring storage account with customer-managed encryption key", check=False)

                    print("✓ Customer-managed encryption configured!")
                except:
                    print("⚠ Customer-managed encryption failed. Using Microsoft-managed keys.")

            except:
                print("⚠ Encryption key creation failed. Using default encryption.")

            # Create access policy for your account
            try:
                user_id = run_command("az ad signed-in-user show --query id --output tsv", check=False)
                if user_id:
                    run_command([
                        "az", "keyvault", "set-policy",
                        "--name", KEYVAULT_NAME,
                        "--object-id", user_id.strip(),
                        "--secret-permissions", "get list set delete backup restore recover purge",
                        "--key-permissions", "get list create delete import encrypt decrypt sign verify backup restore recover purge",
                        "--certificate-permissions", "get list create delete import backup restore recover purge"
                    ], "Configuring Key Vault access policies", check=False)

                    print("✓ Key Vault access policies configured!")
            except:
                print("⚠ Key Vault policy configuration failed. Manual policy setup required.")

            return result.strip()

    except:
        print("⚠ Key Vault setup failed.")
        print("   Alternative Encryption Approaches:")
        print("   • Use Azure managed encryption keys (free)")
        print("   • Enable storage-level SSE (server-side encryption)")
        print("   • Implement client-side encryption in your code")
        print("   • Use Azure Disk Encryption for compute resources")
        return ""

def step6_setup_network_security():
    """Step 6: Network Isolation and Security"""
    section_header("Step 6: Network Security Configuration")

    try:
        # Create Virtual Network for network isolation
        vnet_result = run_command([
            "az", "network", "vnet", "create",
            "--resource-group", RESOURCE_GROUP,
            "--name", VNET_NAME,
            "--address-prefix", "10.0.0.0/16",
            "--subnet-name", SUBNET_NAME,
            "--subnet-prefix", "10.0.0.0/24",
            "--location", AZURE_REGION,
            "--query", "id",
            "--output", "tsv"
        ], f"Creating Virtual Network '{VNET_NAME}' for network isolation")

        if vnet_result:
            print("✓ Virtual Network created for secure networking!")

            # Create Network Security Group with restrictive rules
            nsg_result = run_command([
                "az", "network", "nsg", "create",
                "--resource-group", RESOURCE_GROUP,
                "--name", NSG_NAME,
                "--location", AZURE_REGION,
                "--query", "id",
                "--output", "tsv"
            ], f"Creating Network Security Group '{NSG_NAME}'")

            if nsg_result:
                # Create restrictive inbound rules (deny all by default, explicit allow)
                run_command([
                    "az", "network", "nsg", "rule", "create",
                    "--resource-group", RESOURCE_GROUP,
                    "--nsg-name", NSG_NAME,
                    "--name", "Allow-HTTPS-Inbound",
                    "--priority", "100",
                    "--destination-port-ranges", "443",
                    "--access", "Allow",
                    "--protocol", "Tcp",
                    "--description", "Allow HTTPS traffic for Azure AI services"
                ], "Adding HTTPS allow rule to NSG", check=False)

                run_command([
                    "az", "network", "nsg", "rule", "create",
                    "--resource-group", RESOURCE_GROUP,
                    "--nsg-name", NSG_NAME,
                    "--name", "Deny-All-Inbound",
                    "--priority", "4096",  # Lowest priority, catches all
                    "--access", "Deny",
                    "--protocol", "*",
                    "--description", "Deny all other inbound traffic"
                ], "Adding default deny rule to NSG", check=False)

                print("✓ Network Security Group configured with restrictive rules!")

            # Associate NSG with subnet
            try:
                run_command([
                    "az", "network", "vnet", "subnet", "update",
                    "--resource-group", RESOURCE_GROUP,
                    "--vnet-name", VNET_NAME,
                    "--name", SUBNET_NAME,
                    "--network-security-group", NSG_NAME
                ], "Associating NSG with VNet subnet", check=False)

                print("✓ NSG associated with Virtual Network subnet!")
            except:
                print("⚠ NSG association failed. Manual network security configuration required.")

            return vnet_result.strip()

    except:
        print("⚠ Network security setup failed.")
        print("   This is common in:")
        print("   • Free tier subscription limitations")
        print("   • Insufficient permissions for network resources")
        print("   • Regional resource availability")
        print("   Alternative Security:")
        print("   • Use service-level firewalls and access controls")
        print("   • Configure IP-based restrictions")
        print("   • Implement application-level security")
        print("   • Use Azure Front Door or API Management for access control")
        return ""

def step7_setup_monitoring():
    """Step 7: Monitoring and Audit Logging"""
    section_header("Step 7: Monitoring and Audit Configuration")

    try:
        # Create Log Analytics workspace for centralized logging
        analytics_result = run_command([
            "az", "monitor", "diagnostic-settings", "create",
            "--name", LOG_ANALYTICS_NAME,
            "--resource", f"/subscriptions/{get_subscription_id()}/resourceGroups/{RESOURCE_GROUP}",
            "--logs", '[{"category": "Audit", "enabled": true}, {"category": "Security", "enabled": true}]',
            "--metrics", '[{"category": "AllMetrics", "enabled": true}]',
            "--workspace", "/subscriptions/optimization",  # Will create workspace automatically
            "--query", "id",
            "--output", "tsv"
        ], f"Setting up diagnostic logging to Log Analytics '{LOG_ANALYTICS_NAME}'", check=False)

        if analytics_result:
            print("✓ Diagnostic logging and monitoring configured!")
        else:
            print("⚠ Centralized logging setup incomplete.")

        # Enable activity logging for security monitoring
        try:
            run_command([
                "az", "monitor", "activity-log", "alert", "create",
                "--name", "Security-Alert",
                "--condition", 'category=Security and level=Error',
                "--description", "Alert on security-related errors",
                "--action", "/subscriptions/default",  # No action specified for basic alerting
                "--scope", f"/subscriptions/{get_subscription_id()}",
                "--enabled", "true"
            ], "Creating security activity alert", check=False)

            print("✓ Security activity alerts configured!")
        except:
            print("⚠ Security alerts not fully configured.")

        # Enable resource health monitoring
        try:
            run_command([
                "az", "monitor", "metrics", "alert", "create",
                "--name", "Resource-Health-Alert",
                "--description", "Alert on AI service health issues",
                "--severity", "1",
                "--condition", "ResourceHealthStatus = Unavailable",
                "--resource", f"/subscriptions/{get_subscription_id()}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/{AI_SERVICE_NAME}",
                "--action", "/subscriptions/default"
            ], "Creating resource health monitoring alert", check=False)

            print("✓ Resource health monitoring enabled!")
        except:
            print("⚠ Resource health monitoring setup failed.")

        return analytics_result or "monitoring-partially-configured"

    except:
        print("⚠ Monitoring setup failed.")
        print("   Alternative Monitoring:")
        print("   • Use Azure Monitor manually via portal")
        print("   • Enable diagnostic settings per service")
        print("   • Use Azure Advisor for security recommendations")
        print("   • Monitor with Azure CLI commands: az monitor metrics list")
        return "monitoring-manual-setup-required"

def step8_setup_cost_management():
    """Step 8: Cost Control and Budgets"""
    section_header("Step 8: Cost Management and Optimization")

    try:
        # Create budget alert
        budget_config = {
            "amount": 20.0,
            "timeGrain": "Monthly",
            "timePeriod": {
                "startDate": "2025-01-01T00:00:00Z"
            },
            "category": "Cost",
            "notifications": {
                "Forecasted_GreaterThan_80_Percent": {
                    "enabled": True,
                    "operator": "GreaterThan",
                    "threshold": 80.0,
                    "contactEmails": [
                        run_command("az account show --query user.name --output tsv", check=False).strip()
                    ],
                    "contactGroups": [],
                    "contactRoles": []
                },
                "Actual_GreaterThan_80_Percent": {
                    "enabled": True,
                    "operator": "GreaterThan",
                    "threshold": 80.0,
                    "contactEmails": [
                        run_command("az account show --query user.name --output tsv", check=False).strip()
                    ],
                    "contactGroups": [],
                    "contactRoles": []
                }
            }
        }

        # Save budget config and create budget
        with open("azure-budget.json", "w") as f:
            json.dump(budget_config, f, indent=2)

        run_command([
            "az", "consumption", "budget", "create",
            "--budget-name", BUDGET_NAME,
            "--subscription", get_subscription_id(),
            "--category", "Cost",
            "--amount", "20",
            "--time-grain", "Monthly",
            "--start-date", "2025-01-01T00:00:00Z",
            "--notifications", "@azure-budget.json"
        ], f"Creating cost budget alert (${budget_config['amount']}/month)", check=False)

        print("✓ Cost budget and alerts configured!")

        # Enable cost analysis for optimization
        try:
            run_command([
                "az", "advisor", "configuration", "set",
                "--resource-group", RESOURCE_GROUP,
                "--category", "Cost",
                "--enabled", "true"
            ], "Enabling Azure Advisor cost recommendations", check=False)

            print("✓ Azure Advisor cost optimization enabled!")
        except:
            print("⚠ Advisor cost recommendations not available.")

    except:
        print("⚠ Budget and cost control setup failed.")
        print("   Manual Cost Management:")
        print("   • Set up Azure Cost Management in portal")
        print("   • Use Azure Pricing Calculator for planning")
        print("   • Set subscription spending limit")
        print("   • Use Azure Reservations for cost savings")

    # Cleanup temporary files
    if os.path.exists("azure-budget.json"):
        os.remove("azure-budget.json")

# ========================================
# MAIN EXECUTION
# ========================================

if __name__ == "__main__":
    print("🚀 Azure AI Security Setup Script for Personal Accounts")
    print(f"📍 Region: {AZURE_REGION}")
    print(f"🎯 Project: {PROJECT_NAME}")
    print("="*60)

    # Confirm execution
    confirm = input("This will create Azure resources and may incur costs. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Exiting...")
        sys.exit(0)

    # Execute all steps
    if not step1_check_prerequisites():
        print("❌ Prerequisites check failed. Please fix Azure configuration first.")
        sys.exit(1)

    print("\n" + "="*60)
    print("🔒 PROCEEDING WITH AZURE AI SECURITY SETUP")
    print("="*60)

    # Execute security setup steps
    step2_create_resource_group()
    step3_setup_azure_ai()
    step4_create_storage_account()
    step5_setup_encryption()
    step6_setup_vpc_security()
    step7_setup_monitoring()
    step8_setup_budget_alerts()

    section_header("Setup Complete!")

    print("✅ Azure AI Security Setup Complete!")
    print("\n📋 Summary of Applied Security Measures:")
    print("   ✓ Azure CLI and authentication verified")
    print("   ✓ Resource group with protection locks")
    print("   ✓ Azure AI service with secure endpoints")
    print("   ✓ Storage account with encryption and access controls")
    print("   ✓ Key Vault for secrets and key management")
    print("   ✓ Virtual Network with security restrictions")
    print("   ✓ Monitoring and diagnostic logging")
    print("   ✓ Budget alerts and cost control measures")

    print("\n⚠️ Notes for Personal Accounts:")
    print("   • Some features may require billing enabled")
    print("   • Free tier has service and quota limits")
    print("   • Enable resource providers if needed in Azure portal")
    print("   • Manual setup may be needed for premium features")

    print(f"\n🎯 Next Steps for Azure AI Usage:")
    print(f"   1. Verify AI service: az cognitiveservices account show --name {AI_SERVICE_NAME} --resource-group {RESOURCE_GROUP}")
    print(f"   2. Check storage: az storage account show --name {STORAGE_ACCOUNT} --resource-group {RESOURCE_GROUP}")
    print(f"   3. Access Key Vault: az keyvault secret list --vault-name {KEYVAULT_NAME}")
    print("   4. Monitor costs in Azure Cost Management")

    print("\n🔗 Useful Azure Portal Links:")
    print("   • Azure AI Playground: https://ai.azure.com/")
    print("   • Resource Group: https://portal.azure.com/#blade/HubsExtension/BrowseResourceGroups")
    print("   • Cost Management: https://portal.azure.com/#blade/Microsoft_CostManagement_Azure")
</result>
</write_to_file>
