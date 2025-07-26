import os
from dotenv import load_dotenv

def load_configuration():
    """
    Loads environment variables from a .env file located in the config directory.
    The .env file should be in the parent directory of the src folder.
    """
    # Construct the path to the .env file in the 'config' directory
    # This assumes this script is in 'src' and .env is in 'config' at the same level as 'src'
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
    
    if os.path.exists(config_path):
        load_dotenv(dotenv_path=config_path)
    else:
        print("Warning: .env file not found in config directory. Please create one from the example.")

def get_config():
    """
    Returns a dictionary of all the required configuration variables.
    """
    load_configuration()
    
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "perplexity_email": os.getenv("PERPLEXITY_EMAIL"),
        "perplexity_password": os.getenv("PERPLEXITY_PASSWORD"),
        "perplexity_cookies_path": os.getenv("PERPLEXITY_COOKIES_PATH"),
        "chatgpt_email": os.getenv("CHATGPT_EMAIL"),
        "chatgpt_password": os.getenv("CHATGPT_PASSWORD"),
        "chatgpt_cookies_path": os.getenv("CHATGPT_COOKIES_PATH"),
        "brave_browser_path": os.getenv("BRAVE_BROWSER_PATH"),
    }

if __name__ == '__main__':
    # For testing purposes
    config = get_config()
    print("Loaded configuration:")
    for key, value in config.items():
        # Mask passwords for printing
        if "password" in key and value:
            print(f"  {key}: {'*' * len(value)}")
        else:
            print(f"  {key}: {value}") 