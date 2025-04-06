# auth/azure_auth.py
import os
import base64
import logging

logger = logging.getLogger(__name__)

def get_auth_headers():

    pat = os.environ.get('AZURE_DEVOPS_PAT')
    
    if not pat:
        error_msg = "Azure DevOps PAT not found in environment variable 'AZURE_DEVOPS_PAT'. Please set this variable."
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Successfully retrieved Azure DevOps PAT from environment variable.")

    # Azure DevOps uses Basic Authentication with the PAT as the password 
    # (username can be empty or anything).
    # We need to Base64 encode "user:PAT"
    authorization = str(base64.b64encode(bytes(':'+pat, 'ascii')), 'ascii')

    headers = {
        'Authorization': f'Basic {authorization}',
        'Content-Type': 'application/json'
    }
    
    logger.debug("Generated Azure DevOps authentication headers.")
    return headers

