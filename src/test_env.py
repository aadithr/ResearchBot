from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join('config', '.env'))
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))