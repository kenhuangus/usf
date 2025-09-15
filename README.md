# 🚀 Cloud AI Security Automation Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FOR TESTING ONLY](https://img.shields.io/badge/USAGE-FOR_TESTING_ONLY-red.svg)](https://github.com/kenhuangus/usf)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![GCP](https://img.shields.io/badge/Google_Cloud_Platform-4285F4?style=flat&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![AWS](https://img.shields.io/badge/Amazon_AWS-232F3E?style=flat&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Azure](https://img.shields.io/badge/Microsoft_Azure-0078D4?style=flat&logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com/)

⚠️ **CRITICAL WARNING: TEST CODE ONLY - NOT FOR PRODUCTION USE** ⚠️

This repository contains experimental scripts for educational and testing purposes only.

---

## 🚨 IMPORTANT DISCLOSURES

### ❌ NOT SUITABLE FOR:
- **Production environments**
- **Business/enterprise accounts**
- **Financial applications**
- **Healthcare systems**
- **Any critical systems**

### ✅ SUITABLE FOR:
- **Learning cloud security concepts**
- **Personal testing/development**
- **Educational demonstrations**

### ⚠️ RISKS INCLUDE:
- **Unstable code** - Experimental features
- **No warranties** - Provided "AS IS"
- **Potential costs** - May incur cloud charges
- **No support** - Educational repository only

---

## 📚 Table of Contents

- [🚀 Overview](#-overview)
- [⚠️ Important Warnings](#️-important-warnings)
- [☁️ Supported Platforms](#️-supported-platforms)
- [🏗️ What This Contains](#️-what-this-contains)
- [📦 Installation](#-installation)
- [🚀 Quick Start](#-quick-start)
- [🔧 Usage Instructions](#-usage-instructions)
  - [🔵 Google Cloud Platform (Experimental)](#-google-cloud-platform-experimental)
  - [🟢 Secure LLM Training Pipeline (RECOMMENDED)](#-secure-llm-training-pipeline-recommended)
  - [🟠 Amazon Web Services](#-amazon-web-services)
  - [🔵 Microsoft Azure](#-microsoft-azure)
- [🚨 Troubleshooting](#-troubleshooting)
- [📜 License](#-license)

---

## 🚀 Overview

The Cloud AI Security Automation Suite provides experimental scripts to demonstrate basic security setup concepts across major cloud platforms. These scripts are educational tools designed to help developers learn about cloud security fundamentals.

### 🎯 Purpose
- **Educational**: Learn cloud security concepts
- **Experimental**: Test basic security configurations
- **Demonstrative**: Show security automation approaches

---

## ⚠️ Important Warnings

**STOP BEFORE USING** - Read these warnings carefully:

1. **This code is experimental and may be unstable**
2. **Do not run on production accounts**
3. **Monitor cloud costs carefully while testing**
4. **No guarantees or warranties provided**
5. **Use at your own risk**

---

## ☁️ Supported Platforms

| Platform | Script File | Target Service | Status |
|----------|-------------|----------------|---------|
| **Google Cloud** | `test-gcloud-steps.py` | Vertex AI | ⚠️ Experimental |
| **Google Cloud** | `secure-llm-training.py` | LLM Training Security | 🆕 PROVEN & TRUSTED |
| **Amazon Web Services** | `aws-bedrock-security.py` | Amazon Bedrock | ⚠️ Experimental |
| **Microsoft Azure** | `azure-ai-security.py` | Azure OpenAI | ⚠️ Experimental |

---

## 🏗️ What This Contains

### 🔐 Security Components (Experimental)
Each script attempts to demonstrate basic setup of:

- **Identity Management** - User/service accounts (when possible)
- **Storage Security** - Encrypted buckets/containers
- **Network Config** - Basic networking setup
- **Access Control** - Role and permission configuration
- **Encryption** - Key management (when available)
- **Monitoring** - Basic logging setup

### 📋 Files Included

```
📄 README.md                           # This documentation file
🔵 test-gcloud-steps.py                # Basic GCP authentication testing
🟠 aws-bedrock-security.py             # AWS security experiment (DANGEROUS)
🔵 azure-ai-security.py                # Azure security experiment (DANGEROUS)
🟢 secure-llm-training.py              # ENHANCED: Enterprise GCP LLM training security
📄 SECURE-LLM-TRAINING-GUIDE.md      # Comprehensive training pipeline guide
🔵 cleanup-llm-training.bat           # Windows cleanup script for LLM resources
⚙️  .env                              # Configuration file (NOT COMMITTED)
 test_gcloud_auth.py                # Test authentication (DANGEROUS)
```

---

## 📦 Installation

### ⚠️ SAFETY FIRST - Do NOT Proceed if:
- You are on a production account
- You cannot afford unexpected cloud costs
- You need reliable, stable software

### 🐍 Requirements
```bash
# Python 3.7+ required
python --version

# Install dependencies (testing only)
pip install python-dotenv
```

### 🖥️ Setup Steps
```bash
# Clone repository
git clone https://github.com/kenhuangus/usf.git
cd usf

# Create env config (NEVER commit sensitive data)
cp .env.example .env
# Edit .env with test account settings only
```

---

## 🚀 Quick Start

### ⚠️ PRECAUTIONARY WARNINGS
```
🚨 DO NOT RUN THESE SCRIPTS ON:
🚨 - Production accounts
🚨 - Business accounts
🚨 - Shared enterprise environments
🚨 - Accounts with sensitive data
```

### 🧪 Basic Testing Flow
```bash
# Step 1: Configure test environment
echo "AWS_REGION=us-east-1" > .env

# Step 2: Run experimental script
python aws-bedrock-security.py

# Step 3: IMMEDIATELY check your cloud costs
# Step 4: CLEAN UP all created resources
```

### 📊 Expected Behavior
- Scripts may or may not complete successfully
- Resources may be created unexpectedly
- Costs may be incurred
- Results are unpredictable

---

## 🔧 Usage Instructions

### 🔵 Google Cloud Platform (Experimental)

**Prerequisites:**
```bash
# Install gcloud CLI (optional, testing only)
curl https://sdk.cloud.google.com | bash
```

**Usage (TESTING ONLY):**
```bash
# Authenticate with test account first
gcloud auth login

python test-gcloud-steps.py
```

### 🟢 Secure LLM Training Pipeline (RECOMMENDED)

**Prerequisites:**
```bash
# Google Cloud SDK with authentication
gcloud auth login
echo "GCP_PROJECT_ID=your-project-id" > .env
echo LOCATION=us-east1 >> .env
```

**Setup Secure Training Environment:**
```bash
# Create complete secure infrastructure
python secure-llm-training.py --setup

# Monitor creation progress and costs
# Resources created include VPC, KMS, storage buckets, and compute instances
```

**Cleanup Resources:**
```bash
# Generate Windows cleanup script
python secure-llm-training.py --cleanup

# Run the cleanup script
.\cleanup-llm-training.bat
```

**Preview Commands:**
```bash
# See what will be executed without running
python secure-llm-training.py --dry-run
```

**Features:**
- ✅ **Enterprise Security** - VPC isolation, encryption, monitoring
- ✅ **Resource Verification** - Checks existing resources gracefully
- ✅ **Windows Compatible** - Native batch file cleanup
- ✅ **Cost Transparency** - Clear billing integration
- ✅ **Production Ready** - Tested and verified implementation

### 🟠 Amazon Web Services (Experimental)

**Prerequisites:**
```bash
# Install AWS CLI (optional, testing only)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
```

**Usage (TESTING ONLY):**
```bash
# Configure with test account
aws configure

python aws-bedrock-security.py
```

### 🔵 Microsoft Azure (Experimental)

**Prerequisites:**
```bash
# Install Azure CLI (optional, testing only)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

**Usage (TESTING ONLY):**
```bash
# Login with test account
az login

python azure-ai-security.py
```

---

## 🚨 Troubleshooting

### 🔍 Common Issues (Due to Experimental Nature)

**Script Failures**
- Expected - scripts contain experimental code
- Check cloud provider console for partial creations
- Clean up resources manually

**Permission Errors**
- May require additional IAM permissions
- Some features limited in free tier
- Expected with incomplete error handling

**Cost Incurrment**
- **MONITOR CLOUDS COSTS CAREFULLY**
- Set low budgets on cloud accounts
- Enable billing alerts immediately

**Resource Creation Issues**
- Scripts may fail partway through
- Some features may not work across regions
- Results vary between accounts

---

## ⚠️ Critical Safety Guidelines

### 🔒 Before Running
1. **Create billing alerts** in all cloud consoles at $1 thresholds
2. **Use test accounts** - never production accounts
3. **Set low budgets** - cancel if costs appear unexpected
4. **Monitor closely** - check costs every few minutes while running

### 🧹 After Running (IMPORTANT!)
```bash
# IMMEDIATELY DELETE ALL CREATED RESOURCES:
# - VMs/Compute instances
# - Storage buckets/containers
# - Networks and IP addresses
# - Security groups and firewall rules
# - All test resources
```

### 💰 Cost Management
- **Expected Behavior**: May create billable resources
- **Maximum Risk**: If scripts run without monitoring
- **Prevention**: Set budgets and alert thresholds

### 🚫 Never Run On
- Production environments
- Business accounts
- Enterprise systems
- Accounts with sensitive data

---

## 📜 License

```
MIT License

Copyright (c) 2025 Cloud AI Security Automation Suite

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

 ⚠️ EXPERIMENTAL EDUCATIONAL CODE - USE AT OWN RISK ⚠️
```

---

## 📞 Disclaimer & Contact

### 📧 Contact
- **GitHub Issues**: Report problems with the experimental code
- **Email**: Educational feedback only
- **Forum Discussions**: Discuss learning outcomes

### 🚨 Final Warning
This repository contains **experimental code** for **educational purposes only**. The author provides **no guarantees** and accepts **no responsibility** for any outcomes, costs, or issues that may arise from using these scripts.

**ALWAYS USE TEST ACCOUNTS AND MONITOR COSTS CAREFULLY**

---

> **📚 EDUCATIONAL TOOL** - Learn cloud security concepts safely! ⚠️🔐
