#!/usr/bin/env python3
"""
LLMManager using langchain-google-genai integration
"""

import os
from typing import Any, List
import re

from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
# If you need chat-specific calls:
# from langchain_google_genai import ChatGoogleGenerativeAI

class LLMManager:
    """
    Centralized manager for Gemini (via langchain-google-genai) LLM calls and embeddings
    """

    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash", temp: float = 0.1):
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        elif "GOOGLE_API_KEY" not in os.environ:
            raise ValueError("Google API key not provided or not set in environment")

        self.llm = GoogleGenerativeAI(model=model, temperature=temp)
        self.embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    def generate_text(self, prompt: str) -> str:
        """
        Use Gemini to generate text
        """
        # print("----------------------before invoke------------------------")
        response = self.llm.invoke(prompt)
        # print("----------------------after invoke-------------------------")
        cleaned_response = re.sub(r"^```json\s*|\s*```$", "", response, flags=re.MULTILINE).strip()
        # Adjust this if the SDK returns a different attribute (e.g., .content)
        return getattr(cleaned_response, "content", str(cleaned_response))

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings for given text
        """
        return self.embedding_model.embed_query(text)
