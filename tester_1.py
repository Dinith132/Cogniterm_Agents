# %%
import logging
import json
import os
import yaml
import importlib.util
import uuid
from typing import Annotated, Sequence, Callable, Dict, Any, List, Optional
from functools import wraps
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.agents import initialize_agent, AgentType
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import pprint
from agents.llm_manager import LLMManager
from agents.planner_agent import PlannerAgent
# llm_manager = LLMManager(api_key="AIzaSyDbhQyaZc5BN45QeyYF3lZsrtZ4vvEWUSM")


planner= PlannerAgent()
# Call Gemini to generate plan
prompt = "how to check my ip in linux"
# plan_text = llm_manager.generate_text(prompt)


plan_text=planner.plan_request(prompt)

# %%
import json
# data=json.loads(plan_text['content'])
# %%

type(plan_text)
# %%
