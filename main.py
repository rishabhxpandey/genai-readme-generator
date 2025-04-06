import logging
import os
from dotenv import load_dotenv
from utils.logger_config import setup_logging

def main():
    # Load environment variables from .env file FIRST
    load_dotenv() 

    # Setup logging as the next step
    setup_logging() 

    logging.info("Starting Auto README Generator...")
    
    logging.info("Application finished.")

if __name__ == "__main__":
    main()