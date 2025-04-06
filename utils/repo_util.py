import logging
import requests
from urllib.parse import urlparse
import os

# Assuming azure_auth.py is in the auth directory, one level up and then down
# Adjust the import path if your project structure is different or use package-relative imports
try:
    from auth.azure_auth import get_auth_headers
except ImportError:
    # Handle cases where this might be run standalone or structure changes
    logging.error("Could not import get_auth_headers from auth.azure_auth. Check import path.")
    # Define a dummy function or re-raise to prevent downstream errors
    def get_auth_headers():
        raise ImportError("auth.azure_auth not found")

logger = logging.getLogger(__name__)

def parse_azure_devops_url(repo_url: str) -> dict | None:
    """Parses an Azure DevOps Git repository URL (HTTPS or SSH) 
       to extract organization, project, and repo name.

    Args:
        repo_url: The full URL of the Azure DevOps repository. 
                  e.g., https://org@dev.azure.com/org/project/_git/repo
                  e.g., git@ssh.dev.azure.com:v3/org/project/repo

    Returns:
        A dictionary containing 'organization', 'project', 'repo_name', 
        and 'api_base_url', or None if parsing fails.
    """
    try:
        parsed = urlparse(repo_url)
        
        if '@' in parsed.netloc and 'dev.azure.com' in parsed.netloc and parsed.path.startswith('/'): # HTTPS format 1: https://user@dev.azure.com/org/proj/_git/repo
            parts = parsed.path.strip('/').split('/')
            if len(parts) >= 4 and parts[-2] == '_git':
                org = parts[0]
                project = parts[1]
                repo_name = parts[-1]
                api_base_url = f"https://dev.azure.com/{org}/{project}"
                logger.info(f"Parsed HTTPS URL: org={org}, project={project}, repo={repo_name}")
                return {"organization": org, "project": project, "repo_name": repo_name, "api_base_url": api_base_url}
        elif 'dev.azure.com' in parsed.netloc and parsed.path.startswith('/'): # HTTPS format 2: https://dev.azure.com/org/project/_git/repo
             parts = parsed.path.strip('/').split('/')
             if len(parts) >= 4 and parts[-2] == '_git':
                org = parts[0]
                project = parts[1]
                repo_name = parts[-1]
                api_base_url = f"https://dev.azure.com/{org}/{project}"
                logger.info(f"Parsed HTTPS URL: org={org}, project={project}, repo={repo_name}")
                return {"organization": org, "project": project, "repo_name": repo_name, "api_base_url": api_base_url}
        elif parsed.scheme == 'ssh' or (parsed.scheme == '' and '@' in parsed.path and 'dev.azure.com' in parsed.path): # SSH format: git@ssh.dev.azure.com:v3/org/project/repo
            # Handle potential 'git@' prefix if urlparse didn't catch scheme
            path_part = parsed.path
            if path_part.startswith('git@'):
                 path_part = repo_url.split('@', 1)[1] # Get part after git@
            
            # Path is like ssh.dev.azure.com:v3/org/project/repo or v3/org/project/repo
            if ':' in path_part:
                 path_part = path_part.split(':', 1)[1] # Get part after :
            
            parts = path_part.strip('/').split('/')
            if len(parts) == 4 and parts[0] == 'v3': # Expecting v3/org/project/repo
                org = parts[1]
                project = parts[2]
                repo_name = parts[3]
                api_base_url = f"https://dev.azure.com/{org}/{project}"
                logger.info(f"Parsed SSH URL: org={org}, project={project}, repo={repo_name}")
                return {"organization": org, "project": project, "repo_name": repo_name, "api_base_url": api_base_url}
        logger.warning(f"Could not parse Azure DevOps URL: {repo_url}")
        return None
    except Exception as e:
        logger.error(f"Error parsing Azure DevOps URL '{repo_url}': {e}", exc_info=True)
        return None


def make_devops_api_call(api_url: str, headers: dict) -> dict | None:
    """Makes a GET request to the Azure DevOps API.

    Args:
        api_url: The full URL for the API endpoint.
        headers: Authentication headers obtained from get_auth_headers().

    Returns:
        The JSON response as a dictionary if successful, None otherwise.
    """
    try:
        response = requests.get(api_url, headers=headers, timeout=15) # Added timeout
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        
        logger.debug(f"API call successful to {api_url}. Status: {response.status_code}")
        return response.json()
    
    except requests.exceptions.Timeout:
        logger.error(f"API call timed out: {api_url}")
        return None
    except requests.exceptions.RequestException as e:
        # Log specific HTTP errors if possible
        status_code = e.response.status_code if e.response is not None else "N/A"
        error_content = e.response.text if e.response is not None else "N/A"
        logger.error(f"API call failed to {api_url}. Status: {status_code}. Error: {e}. Content: {error_content[:200]}...")
        if status_code == 401:
            logger.error("Authentication failed (401). Check your PAT and permissions.")
        return None
    except Exception as e: # Catch unexpected errors
        logger.error(f"Unexpected error during API call to {api_url}: {e}", exc_info=True)
        return None


def get_repository_details(repo_url: str) -> dict | None:
    """Fetches repository details (name, ID, default branch, description) from Azure DevOps.

    Args:
        repo_url: The full URL of the Azure DevOps repository.

    Returns:
        A dictionary containing repository details, or None if fetching fails.
    """
    parsed_info = parse_azure_devops_url(repo_url)
    if not parsed_info:
        return None

    org = parsed_info["organization"]
    project = parsed_info["project"]
    repo_name = parsed_info["repo_name"]
    api_base_url = parsed_info["api_base_url"]
    
    # Construct the API URL for getting repository information
    # API Versioning is important! Check Azure DevOps REST API docs for current versions.
    api_version = "7.1-preview.1"  # Example version, check docs
    repo_api_url = f"{api_base_url}/_apis/git/repositories/{repo_name}?api-version={api_version}"
    
    logger.info(f"Fetching repository details for '{repo_name}' from {repo_api_url}")

    try:
        headers = get_auth_headers() # Get PAT auth header
    except ValueError as e:
        logger.error(f"Could not get authentication headers: {e}")
        return None
    except ImportError as e:
         logger.error(f"Import error fetching auth headers: {e}")
         return None

    repo_data = make_devops_api_call(repo_api_url, headers)

    if repo_data:
        logger.info(f"Successfully fetched details for repository: {repo_data.get('name')}")
        # Extract key details - adjust keys based on actual API response structure
        details = {
            "id": repo_data.get("id"),
            "name": repo_data.get("name"),
            "description": repo_data.get("project", {}).get("description"), # Description might be at project level
            "project_name": repo_data.get("project", {}).get("name"),
            "default_branch": repo_data.get("defaultBranch", "refs/heads/main").replace("refs/heads/", ""), # Clean up branch name
            "ssh_url": repo_data.get("sshUrl"),
            "web_url": repo_data.get("webUrl"),
            "api_url": repo_api_url # Store the specific API URL used
        }
        return details
    else:
        logger.error(f"Failed to fetch repository details for {repo_name}.")
        return None

# --- Example Usage ---
# if __name__ == '__main__':
#     # Make sure .env is loaded if running directly or AZURE_DEVOPS_PAT is set
#     from dotenv import load_dotenv
#     load_dotenv() 
#     import sys
#     # Add project root to path if necessary to find auth module
#     # sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
#     # Configure logging for testing
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     test_repo_url_https = "https://your_org@dev.azure.com/your_org/YourProject/_git/YourRepoName"
#     # test_repo_url_ssh = "git@ssh.dev.azure.com:v3/your_org/YourProject/YourRepoName"
    
#     print(f"--- Testing with URL: {test_repo_url_https} ---")
#     details = get_repository_details(test_repo_url_https)
    
#     if details:
#         print("\nRepository Details:")
#         for key, value in details.items():
#             print(f"  {key}: {value}")
#     else:
#         print("\nFailed to get repository details.")

#     # Add more test cases if needed (invalid URL, SSH URL, etc.)