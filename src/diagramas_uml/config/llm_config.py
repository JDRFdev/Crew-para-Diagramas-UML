import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=groq_api_key, 
    temperature=0.3
)