import json
import logging
import asyncio
import aiohttp
import nest_asyncio
from typing import Dict, Any, Optional
from auth.aws_auth import get_bedrock_client

# Apply nest_asyncio to allow nested event loops (needed for async in Streamlit)
nest_asyncio.apply()

logger = logging.getLogger(__name__)

# Model IDs for Claude models in Bedrock
CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
# Choose which model to use - Sonnet is more capable but more expensive
DEFAULT_MODEL_ID = CLAUDE_3_SONNET

async def _generate_readme_async(repo_details: Dict[str, Any], model_id: str = DEFAULT_MODEL_ID) -> str:
    """
    Asynchronously generate a README using AWS Bedrock's Claude model.
    
    Args:
        repo_details: Dictionary containing repository details
        model_id: AWS Bedrock model ID to use
        
    Returns:
        str: The generated README content in markdown format
    """
    try:
        # Get AWS Bedrock client
        bedrock_client = get_bedrock_client()
        
        # Create the prompt for Claude
        prompt = _create_readme_prompt(repo_details)
        
        # Format the request body for Claude 3
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Invoke the model
        logger.info(f"Invoking Bedrock model {model_id} to generate README")
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response.get('body').read())
        generated_text = response_body.get('content', [{}])[0].get('text', '')
        
        # Log success and return the generated README
        logger.info(f"Successfully generated README of {len(generated_text)} characters")
        return generated_text
    
    except Exception as e:
        logger.error(f"Error generating README: {e}", exc_info=True)
        # Return an error message that can be displayed to the user
        return f"# README Generation Failed\n\nThere was an error generating the README: {str(e)}\n\nPlease check your AWS credentials and try again."

def _create_readme_prompt(repo_details: Dict[str, Any]) -> str:
    """
    Create a detailed prompt for Claude based on repository details.
    
    Args:
        repo_details: Dictionary containing repository details
        
    Returns:
        str: The formatted prompt string
    """
    repo_name = repo_details.get('name', 'Unknown Repository')
    project_name = repo_details.get('project_name', 'Unknown Project')
    description = repo_details.get('description', 'No description provided')
    default_branch = repo_details.get('default_branch', 'main')
    
    # You can customize this prompt based on your needs
    prompt = f"""
You are an expert software developer with excellent technical writing skills.
Your task is to generate a comprehensive, professional README.md file for a software repository
with the following details:

Repository Name: {repo_name}
Project: {project_name}
Description: {description}
Default Branch: {default_branch}

The README should follow best practices and include AT MINIMUM the following sections:
1. Title and concise introduction
2. Purpose/Description of the project
3. Technologies Used
4. Prerequisites/Dependencies
5. Installation and Setup
6. Usage Instructions
7. Contributing Guidelines (if applicable)
8. License Information (if available)

Additionally, analyze the repository details and add any other relevant sections that would be helpful
for users and contributors. The README should be well-structured, professional, and easy to navigate.

IMPORTANT: Write the README.md content in proper markdown format. Be concise but informative.
Do not include sections with placeholder text like "Fill this in later".
If information is missing, make reasonable assumptions based on the repository name and description.
"""
    
    return prompt

def generate_readme(repo_details: Dict[str, Any], model_id: str = DEFAULT_MODEL_ID) -> str:
    """
    Generate a README.md for a repository using AWS Bedrock.
    This is a synchronous wrapper around the async function.
    
    Args:
        repo_details: Dictionary containing repository details
        model_id: AWS Bedrock model ID to use
        
    Returns:
        str: The generated README content in markdown format
    """
    # Create a new event loop or use the existing one
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Run the async function and return the result
    return loop.run_until_complete(_generate_readme_async(repo_details, model_id))