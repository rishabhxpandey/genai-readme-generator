import os
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, ProfileNotFound

logger = logging.getLogger(__name__)

def get_aws_credentials() -> Dict[str, str]:
    """
    Retrieves AWS credentials from environment variables or .aws/credentials file.
    Expects AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION to be set.
    
    Returns:
        dict: A dictionary containing AWS credential keys
    
    Raises:
        ValueError: If AWS credentials are not found
    """
    # First, try to get credentials from environment variables
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_REGION', 'us-west-2')  # Default to us-west-2 if not specified
    
    # If environment variables are set, use them
    if aws_access_key and aws_secret_key:
        logger.info("Using AWS credentials from environment variables")
        return {
            'aws_access_key_id': aws_access_key,
            'aws_secret_access_key': aws_secret_key,
            'region_name': aws_region
        }
    
    # Otherwise, try to use the default AWS credential provider chain
    # This will look for credentials in ~/.aws/credentials or EC2 instance profile
    logger.info("Environment variables not found. Attempting to use default AWS credential provider chain")
    try:
        # Test if we can create a boto3 client with the default credential provider chain
        boto3.client('sts').get_caller_identity()
        # If we reach here, credentials were found through the provider chain
        return {'region_name': aws_region}  # No need to explicitly provide keys
    except (ClientError, ProfileNotFound) as e:
        error_msg = "AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables or configure AWS CLI credentials."
        logger.error(f"{error_msg}: {e}")
        raise ValueError(error_msg)

def get_bedrock_client() -> Any:
    """
    Creates an AWS Bedrock client using the retrieved credentials.
    
    Returns:
        boto3.client: A configured boto3 Bedrock client
        
    Raises:
        ValueError: If credentials could not be retrieved or client creation fails
    """
    try:
        # Get AWS credentials
        credentials = get_aws_credentials()
        
        # Create and return the Bedrock client
        logger.info(f"Creating AWS Bedrock client in region {credentials.get('region_name', 'default')}")
        bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            **credentials
        )
        return bedrock_client
    except Exception as e:
        error_msg = f"Failed to create AWS Bedrock client: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)