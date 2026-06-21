#!/usr/bin/env python3
"""LangChain Foundations: From Raw Queries to LCEL Chains."""

import json
import os
import re
from typing import List, Generator, Iterable
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

# Ensure environment variables are loaded
load_dotenv()

# =====================================================================
# STEP 1.1: Environment Setup
# =====================================================================
base_url = (os.getenv("ANTHROPIC_BASE_URL") or "http://localhost:11434").strip()

if "/v1" in base_url:
    base_url = base_url.replace("/v1/chat/completions", "").replace("/v1", "")

model_name = os.getenv("CLAUDE_MODEL", "qwen3.5:9b").strip()

print("\n-----------------------------------------")
print("--- Step 1.1: Environment Initialised ---")
print("-----------------------------------------")
print(f"Target Server: {base_url.strip('/')}")
print(f"Target Model:  {model_name}\n")

# Global model client configuration
llm = ChatOllama(
    base_url=base_url.strip("/"),
    model=model_name,
    temperature=0
)


# =====================================================================
# REUSABLE CORE FILTER ENGINE (The Refactor)
# =====================================================================
def filter_reasoning_stream(chunks: Iterable[str]) -> Generator[str, None, None]:
    """
    A unified, stateful generator filter that processes text tokens.
    It completely strips out internal reasoning <think> blocks on the fly.
    """
    inside_thinking = False
    buffer = ""

    for chunk in chunks:
        buffer += chunk

        # Scenario A: We hit the opening tag
        if "<think>" in buffer and "</think>" not in buffer:
            if not inside_thinking:
                inside_thinking = True
            continue

        # Scenario B: We hit the closing tag. Extract remaining text and reset state
        if inside_thinking and "</think>" in buffer:
            inside_thinking = False
            remaining_text = buffer.split("</think>")[-1]
            buffer = ""  # Reset buffer
            if remaining_text:
                yield remaining_text
            continue

        # Scenario C: Stream is moving along normally outside of thoughts
        if not inside_thinking:
            yield chunk
            buffer = ""  # Keep buffer clean

    # Edge Case Protection: If the stream finishes but was cut off mid-thought
    if inside_thinking and buffer:
        yield f"\n[Reasoning truncated mid-thought]"


def clean_static_text(text: str) -> str:
    """Reusable wrapper for legacy static steps using our core filter logic."""
    if not text:
        return "[Server Error: Response data is empty.]"
    # We pass the static text as a single-item list to our stream filter
    return "".join(list(filter_reasoning_stream([text]))).strip()


# =====================================================================
# STEP 1.2: The Raw Chat Model & AIMessage Objects
# =====================================================================
def run_step_1_2():
    print("\n-------------------------------------------")
    print("--- Step 1.2: Raw Chat Model Invocation ---")
    print("-------------------------------------------")

    limited_llm = llm.bind(options={"num_predict": 4000})
    response = limited_llm.invoke("What are the three primary colours?")
    
    cleaned_content = clean_static_text(response.content)
    print(f"Raw AIMessage Content:\n{cleaned_content}\n")


# =====================================================================
# STEP 1.3: Prompt Templates
# =====================================================================
def run_step_1_3():
    print("\n------------------------------------------------------------")
    print("--- Step 1.3: ChatPromptTemplate System/Human Separation ---")
    print("------------------------------------------------------------")
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a concise support bot. Answer in exactly one sentence."),
        ("human", "My order #{order_id} is missing. Can you check it?")
    ])
    
    formatted_messages = prompt_template.format_messages(order_id="99823")
    
    limited_llm = llm.bind(options={"num_predict": 4000})
    response = limited_llm.invoke(formatted_messages)
    
    cleaned_content = clean_static_text(response.content)
    print(f"Model Response:\n{cleaned_content}\n")


# =====================================================================
# STEP 1.4: Structured Output (Pydantic)
# =====================================================================
class SupportTicket(BaseModel):
    issue_category: str = Field(description="The category of the issue, e.g., Shipping, Billing, Technical")
    urgency: str = Field(description="Urgency level: Low, Medium, or High")
    summary: str = Field(description="A brief 5-word summary of the user's problem")
    tags: List[str] = Field(description="A list of 2 relevant keywords for sorting")

def run_step_1_4():
    print("\n------------------------------------------------")
    print("--- Step 1.4: Structured Output via Pydantic ---")
    print("------------------------------------------------")

    structured_llm = llm.with_structured_output(SupportTicket)
    user_input = "I am locked out of my account and I keep getting a 403 forbidden error screen."
    
    ticket = structured_llm.invoke(user_input)
    print(f"JSON Output:\n{ticket.model_dump_json(indent=2)}\n")


# =====================================================================
# STEP 1.5: The LCEL Chain (The Pipe Operator)
# =====================================================================
def run_step_1_5():
    print("\n---------------------------------------------------------")
    print("--- Step 1.5: Combining Components into an LCEL Chain ---")
    print("---------------------------------------------------------")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a precise translator. Translate the user text directly into the target language requested. Do not explain anything."),
        ("human", "Translate this text into {target_language}: {text_to_translate}")
    ])
    parser = StrOutputParser()
    
    chain = prompt | llm.bind(options={"num_predict": 10000}) | parser
    
    raw_result = chain.invoke({
        "target_language": "Spanish",
        "text_to_translate": "Hello, it is a pleasure learning how to code chains today."
    })
    
    cleaned_result = clean_static_text(raw_result)
    print(f"Chain Result:\n{cleaned_result}\n")


# =====================================================================
# STEP 1.6: Output Templating Bonus Step
# =====================================================================
def run_output_template_demo():
    print("\n----------------------------------------")
    print("--- Step 1.6: Text Output Templating ---")
    print("----------------------------------------")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a notification generator.
        You MUST format your final response EXACTLY like this text template, including the brackets:
        [ALERT]: {status_type}
        [USER]: {{user_name}}
        [MESSAGE]: Your request regarding '{{topic}}' was processed.
        """),
        ("human", "Write a notification. Status is urgent. User is John. Topic is billing password.")
    ])
    
    chain = prompt | llm.bind(options={"num_predict": 4000}) | StrOutputParser()
    raw_result = chain.invoke({"status_type": "URGENT_CRITICAL"})
    
    cleaned_result = clean_static_text(raw_result)
    print(f"Template Result:\n{cleaned_result}\n")


# =====================================================================
# STEP 1.7: The Live Streaming Pipeline (REFACTORED)
# =====================================================================
def run_step_1_7_streaming():
    print("\n--------------------------------------------------")
    print("--- Step 1.7: Real-Time Live Streaming to Screen ---")
    print("--------------------------------------------------")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful essayist. Write a short paragraph explaining why software engineering is creative."),
        ("human", "Write the paragraph now.")
    ])
    parser = StrOutputParser()
    
    chain = prompt | llm.bind(options={"num_predict": 4000}) | parser
    
    print("🤖 Streaming response live: ", end="", flush=True)
    
    # 1. Get the raw stream generator from LangChain
    raw_stream = chain.stream({})
    
    # 2. Pipe the raw stream straight through our single reusable cleaner filter!
    clean_stream = filter_reasoning_stream(raw_stream)
    
    # 3. Print tokens effortlessly as they are yielded
    for clean_chunk in clean_stream:
        print(clean_chunk, end="", flush=True)
            
    print("\n\n--- Stream Completed Successfully ---")

# =====================================================================
# STEP 1.8: Fallback Architecture (Resilience)
# =====================================================================
# =====================================================================
# STEP 1.8: Fallback Architecture (Resilience)
# =====================================================================
def run_step_1_8_fallbacks():
    print("\n---------------------------------------------------------")
    print("--- Step 1.8: Dynamic Model Fallbacks (Fault Tolerance) --")
    print("---------------------------------------------------------")

    # 1. Create a primary model that deliberately points to a broken port
    broken_llm = ChatOllama(
        base_url="http://localhost:9999", # Wrong port to simulate a server crash
        model=model_name,
        timeout=2.0
    )
    
    # 2. FIX: Increase backup token headroom to 1000 so reasoning doesn't clip the text
    backup_llm = llm.bind(options={"num_predict": 1000})
    
    # 3. Link them using .with_fallbacks()
    resilient_llm = broken_llm.with_fallbacks([backup_llm])
    
    print("⚠️ Attempting call via broken primary model connection...")
    response = resilient_llm.invoke("Say the word 'Success' if you can read this.")
    
    cleaned_content = clean_static_text(response.content)
    print(f"Final Execution Status: {cleaned_content}\n")

# =====================================================================
# STEP 1.9: Inspecting the Internal Prompt Matrix (Debugging)
# =====================================================================
def run_step_1_9_inspect_prompt():
    print("\n---------------------------------------------------------")
    print("--- Step 1.9: Inspecting Compiled Prompt Graph Arrays ----")
    print("---------------------------------------------------------")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert coder. Answer in language: {programming_language}."),
        ("human", "How do I print text to the screen?")
    ])
    
    compiled_messages = prompt.invoke({"programming_language": "Python 3.12"})
    
    print("🔍 Behind-the-Scenes Compiled Structure Type:")
    print(f"{type(compiled_messages)}")
    
    print("\n🔍 Raw Array Transmitted over the Network JSON Payload:")
    # FIX: Access the underlying messages list, then dump them safely
    raw_messages_list = compiled_messages.to_messages()
    
    # We can turn each internal message object into a clean dictionary for printing
    formatted_json_payload = [msg.model_dump() for msg in raw_messages_list]
    print(json.dumps(formatted_json_payload, indent=2))

# =====================================================================
# Main Execution Entrypoint
# =====================================================================
if __name__ == "__main__":
    try:
        run_step_1_2()
        run_step_1_3()
        run_step_1_4()
        run_step_1_5()
        run_output_template_demo()
        run_step_1_7_streaming()
        run_step_1_8_fallbacks()
        run_step_1_9_inspect_prompt()
    except Exception as e:
        print(f"\n[!] An error occurred during execution: {e}")
