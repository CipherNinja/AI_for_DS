from langchain_groq import ChatGroq
from pydantic import SecretStr
import os

opts = {
    'api_key': SecretStr(os.getenv('GROQ_API_KEY', '')),
    "model": "llama3-groq-70b-8192-tool-use-preview"
}

llm = ChatGroq(
    **opts
)
