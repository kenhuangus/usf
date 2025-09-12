import boto3
import json
import time

REGION = 'us-east-1'  # Change as needed
S3_BUCKET = 'my-unique-secure-bucket-12345'  # Must be globally unique; change this
GLUE_ROLE_NAME = 'MyGlueServiceRole'
SAGEMAKER_ROLE_NAME = 'MySageMakerExecutionRole'
GLUE_JOB_NAME = 'MyGlueJob'
MODEL_NAME = 'MySageModel'
ENDPOINT_CONFIG_NAME = 'MyEndpointConfig'
ENDPOINT_NAME = 'MyEndpoint'
LOCAL_CSV = 'local_data.csv'

iam = boto3.client('iam')
s3 = boto3.client('s3', region_name=REGION)
glue = boto3.client('glue', region_name=REGION)
sm = boto3.client('sagemaker', region_name=REGION)

# 1. Create S3 bucket with encryption (if not exists)
def create_s3_bucket(bucket_name):
    try:
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': REGION})
        print(f"S3 bucket '{bucket_name}' created.")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"S3 bucket '{bucket_name}' already exists.")
    except Exception as e:
        print(f"Error creating bucket: {str(e)}")

    # Enable default encryption (AES256)
    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]
        }
    )
    print(f"Default encryption enabled for bucket '{bucket_name}'.")

# 2. Upload CSV data to S3 bucket
def upload_csv_to_s3(bucket_name, file_path, key):
    s3.upload_file(file_path, bucket_name, key, ExtraArgs={'ServerSideEncryption': 'AES256'})
    print(f"Uploaded {file_path} to s3://{bucket_name}/{key} with encryption.")

# 3. Create IAM role with minimal Glue permissions (trusts Glue service)
def create_glue_role(role_name):
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
          "Effect": "Allow",
          "Principal": {"Service": "glue.amazonaws.com"},
          "Action": "sts:AssumeRole"
        }]
    }
    try:
        response = iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy))
        print(f"IAM Role '{role_name}' created.")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"IAM Role '{role_name}' already exists.")
        response = iam.get_role(RoleName=role_name)
    role_arn = response['Role']['Arn']

    # Attach managed policy with Glue access and S3 read/write (for simplicity)
    iam.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole')
    iam.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess')  # For demo; restrict for prod
    return role_arn

# 4. Create IAM role for SageMaker execution (trust SageMaker service)
def create_sagemaker_role(role_name):
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
          "Effect": "Allow",
          "Principal": {"Service": "sagemaker.amazonaws.com"},
          "Action": "sts:AssumeRole"
        }]
    }
    try:
        response = iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy))
        print(f"IAM Role '{role_name}' created.")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"IAM Role '{role_name}' already exists.")
        response = iam.get_role(RoleName=role_name)
    role_arn = response['Role']['Arn']

    # Attach policies to allow SageMaker to access S3 and CloudWatch (for monitoring)
    iam.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess')  # For demo only
    iam.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess')
    iam.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/CloudWatchFullAccess')

    return role_arn

# 5. Create Glue Job Input: This example assumes a Glue script stored externally.
# For simplicity, a complex Glue job creation script is skipped. You would create Glue Job manually or upload Glue ETL script to S3.
# The script here focuses on the basics to get started.
def create_glue_job(job_name, role_arn, script_location, temp_dir):
    try:
        glue.create_job(
            Name=job_name,
            Role=role_arn,
            Command={'Name': 'glueetl', 'ScriptLocation': script_location, 'PythonVersion': '3'},
            DefaultArguments={'--TempDir': temp_dir, '--job-language': 'python'},
            MaxRetries=1,
            GlueVersion='3.0',
            NumberOfWorkers=2,
            WorkerType='G.1X'
        )
        print(f"Glue job '{job_name}' created.")
    except glue.exceptions.AlreadyExistsException:
        print(f"Glue job '{job_name}' already exists.")

# 6. Start Glue job
def start_glue_job(job_name):
    response = glue.start_job_run(JobName=job_name)
    print(f"Glue job '{job_name}' started with job run ID: {response['JobRunId']}")
    return response['JobRunId']

# 7. Start SageMaker training job
def start_sagemaker_training_job(role_arn, bucket_name, input_key):
    training_job_name = f"training-job-{int(time.time())}"
    sm.create_training_job(
        TrainingJobName=training_job_name,
        AlgorithmSpecification={
            'TrainingImage': '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:latest',
            'TrainingInputMode': 'File'
        },
        RoleArn=role_arn,
        InputDataConfig=[
            {
                'ChannelName': 'train',
                'DataSource': {'S3DataSource': {'S3DataType': 'S3Prefix', 'S3Uri': f's3://{bucket_name}/{input_key}'}},
                'ContentType': 'text/csv'
            }
        ],
        OutputDataConfig={'S3OutputPath': f's3://{bucket_name}/output/'},
        ResourceConfig={'InstanceType': 'ml.m5.xlarge', 'InstanceCount': 1, 'VolumeSizeInGB': 30},
        StoppingCondition={'MaxRuntimeInSeconds': 3600}
    )
    print(f"SageMaker training job '{training_job_name}' started.")
    return training_job_name

# 8. Deploy SageMaker model endpoint (basic example; no VPC config)
def deploy_model(training_job_name, role_arn, bucket_name):
    model_data = sm.describe_training_job(TrainingJobName=training_job_name)['ModelArtifacts']['S3ModelArtifacts']
    sm.create_model(
        ModelName=MODEL_NAME,
        ExecutionRoleArn=role_arn,
        PrimaryContainer={'Image': '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:latest', 'ModelDataUrl': model_data}
    )
    sm.create_endpoint_config(
        EndpointConfigName=ENDPOINT_CONFIG_NAME,
        ProductionVariants=[{'ModelName': MODEL_NAME, 'InstanceType': 'ml.m5.xlarge', 'InitialInstanceCount': 1, 'VariantName': 'AllTraffic'}]
    )
    sm.create_endpoint(EndpointName=ENDPOINT_NAME, EndpointConfigName=ENDPOINT_CONFIG_NAME)
    print(f"Model deployed to endpoint '{ENDPOINT_NAME}'.")

if __name__ == "__main__":
    print("Step 1: Creating S3 bucket...")
    create_s3_bucket(S3_BUCKET)
    
    print("Step 2: Uploading sample CSV data to S3...")
    upload_csv_to_s3(S3_BUCKET, LOCAL_CSV, 'input/data.csv')

    print("Step 3: Creating IAM roles for Glue and SageMaker...")
    glue_role_arn = create_glue_role(GLUE_ROLE_NAME)
    sagemaker_role_arn = create_sagemaker_role(SAGEMAKER_ROLE_NAME)

    print("Step 4: Please create a Glue ETL script in S3 and provide its S3 path here (manual step).")
    glue_script_path = 's3://your-glue-script-bucket/sample_etl_script.py'  # Replace with your uploaded script path
    temp_directory = f's3://{S3_BUCKET}/temp/'

    # Step 5: Create Glue job (manual setup needed)
    create_glue_job(GLUE_JOB_NAME, glue_role_arn, glue_script_path, temp_directory)

    print("Step 6: Starting Glue job...")
    glue_job_run_id = start_glue_job(GLUE_JOB_NAME)

    # Wait for Glue job completed in real use case (for demo, just proceed)

    print("Step 7: Starting SageMaker training job...")
    training_job_name = start_sagemaker_training_job(sagemaker_role_arn, S3_BUCKET, 'input/data.csv')

    # Wait for training job completion (demo skips this)

    print("Step 8: Deploying model endpoint...")
    deploy_model(training_job_name, sagemaker_role_arn, S3_BUCKET)

    print("Workflow complete! Monitor SageMaker endpoint and Glue job in AWS Console.")
