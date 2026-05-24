# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from openai import OpenAI
from anthropic import Anthropic

# Running on local machines
import os;
from dotenv import load_dotenv # Load in environment variable, including secrete keys for .env
# *** If using this method ensure .env is listed in .gitignore do it STAYS local

load_dotenv() # Load environment variables from .env file

openai_api_key = os.getenv("HOME_MAC_OPENAI_API_KEY")
print(f"Checking that the OPENAI_API_KEY can be loaded & works with the OpenAI API...") 
print(f"Loaded OPENAI_API_KEY: {'Yes' if openai_api_key else 'No'}") # Debug print to confirm key loading
print(f"OPENAI_API_KEY: {openai_api_key[:5]}...") # Print first 5 characters for verification without exposing full key


from openai import OpenAI
openai_client = OpenAI(api_key=openai_api_key)
try:
  models  = openai_client.models.list() # Test API key by listing available models, will raise an error if key is invalid
except Exception as e:
  print(f"Authentication error with OpenAI API: {e}")
else:
  print("Successfully authenticated with OpenAI API.")
  for model in models.data:
    print(f"Available model: {model.id}") 
#llm = ChatOpenAI(model="gpt-4", temperature=0, api_key=openai_api_key) 


anthropic_api_key = os.getenv("HOME_MAC_ANTHROPIC_API_KEY")
print(f"Checking that the OPENAI_API_KEY can be loaded & works with the OpenAI API...") 
print(f"Loaded ANTHROPIC_API_KEY: {'Yes' if anthropic_api_key else 'No'}") # Debug print to confirm key loading
print(f"ANTHROPIC_API_KEY: {anthropic_api_key[-5:]}...") # Print first 5 characters for verification without exposing full key

from anthropic import Anthropic
anthropic_client = Anthropic(api_key=anthropic_api_key)
try:
  models = anthropic_client.models.list() # Test API key by listing available models, will raise an error if key is invalid
except Exception as e:
  print(f"Authentication error with Anthropic API: {e}")
else:  
  print("Successfully authenticated with Anthropic API.")
  for model in models.data:
    print(f"Available model: {model.id}") 

#llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0, api_key=anthropic_api_key)

