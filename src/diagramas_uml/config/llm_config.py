import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=gemini_api_key, 
    temperature=0.3
)