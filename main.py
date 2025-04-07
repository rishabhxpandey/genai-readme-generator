import logging
import streamlit as st 
from dotenv import load_dotenv
from utils.logger_config import setup_logging
from utils.repo_util import get_repository_details
from generators.readme_generator import generate_readme

load_dotenv()
setup_logging()

st.set_page_config(page_title="ADO README Generator", layout="wide")
st.title("🚀 ADO README Generator")
st.write("Enter the HTTPS or SSH URL of your Azure DevOps repository below.")

repo_url = st.text_input("Repository URL:", placeholder="e.g., https://dev.azure.com/your_org/YourProject/_git/YourRepo")

if st.button("Generate README"):
    if not repo_url:
        st.warning("Please enter a repository URL.")
    else:
        logging.info(f"Starting README generation process for: {repo_url}")
        st.info(f"Processing repository: {repo_url}")

        with st.spinner("Fetching repository details..."):
            try:
                repo_details = get_repository_details(repo_url)
                
                if repo_details:
                    logging.info(f"Successfully fetched details for repository: {repo_details.get('name')}")
                    st.success("Repository details fetched successfully!")
                    
                    st.subheader("Fetched Repository Details:")
                    st.json(repo_details) # Display fetched details as JSON for now

                    st.subheader("Generated README:")
                    
                    with st.spinner("Generating README content..."):
                        generated_readme = generate_readme(repo_details)
                        st.text_area("README Content:", generated_readme, height=400)
                        st.success("README generated successfully.")
                        logging.info("README generated successfully.")
                
                else:
                    logging.error(f"Failed to fetch repository details for {repo_url}.")
                    st.error("Failed to fetch repository details. Check the URL and ensure the PAT has correct permissions.")

            except ValueError as e: # Catch auth errors specifically
                logging.error(f"Authentication error: {e}")
                st.error(f"Authentication Error: {e} Ensure AZURE_DEVOPS_PAT is set correctly in your .env file.")
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}", exc_info=True)
                st.error(f"An unexpected error occurred: {e}")
        
        logging.info("Processing finished for this request.")

st.markdown("---")
st.write("Ensure your `AZURE_DEVOPS_PAT` is set in the `.env` file in the project root.")