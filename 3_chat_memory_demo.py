#!/usr/bin/env python3
"""LangChain Phase 2: Production Multi-Turn Chatbot with Native Control."""

import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

# Ensure environment variables are loaded
load_dotenv()

# =====================================================================
# STEP 2.1: Environment Setup
# =====================================================================
base_url = (os.getenv("ANTHROPIC_BASE_URL") or "http://localhost:11434").strip()
if "/v1" in base_url:
    base_url = base_url.replace("/v1/chat/completions", "").replace("/v1", "")

model_name = os.getenv("CLAUDE_MODEL", "qwen3.5:9b").strip()

print("\n-----------------------------------------")
print("--- Phase 2: Conversational Chat Loops ---")
print("-----------------------------------------")
print(f"Target Server: {base_url.strip('/')}")
print(f"Target Model:  {model_name}\n")

# THE KEY ENGINE CONFIGURATION:
llm = ChatOllama(
    base_url=base_url.strip("/"),
    model=model_name,
    temperature=0.7,
    reasoning=False
)

# Persistent storage engines for conversation history
memory_db = InMemoryChatMessageHistory()       # Used by Step 2.2/2.3
summary_memory_db = InMemoryChatMessageHistory() # Used by Step 2.4

# Global string variable to hold our background summary state
running_conversation_summary = "No conversation has occurred yet."


# =====================================================================
# STEP 2.2 & 2.3: The Dynamic Chat State Loop (Preserved Exactly)
# =====================================================================
def run_chat_loop():
    print("---------------------------------------------------------")
    print("--- Production Chat via Clean Context Windows -----------")
    print("---------------------------------------------------------")
    print("Type your message and press Enter. Type 'exit' to quit.\n")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an entertaining, concise chat assistant. Fulfill user requests immediately. Never output <think> tags."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_input}")
    ])
    
    parser = StrOutputParser()
    chain = prompt | llm.bind(options={"num_predict": 1000}) | parser

    while True:
        try:
            user_text = input("👤 You: ").strip()
            if not user_text:
                continue
            if user_text.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break

            print("🤖 AI: ", end="", flush=True)

            raw_history = memory_db.messages
            recent_history = raw_history[-6:] if raw_history else [AIMessage(content="[Session Started]")]

            ai_response_accumulator = ""
            for chunk in chain.stream({"history": recent_history, "user_input": user_text}):
                print(chunk, end="", flush=True)
                ai_response_accumulator += chunk
            print()

            memory_db.add_message(HumanMessage(content=user_text))
            memory_db.add_message(AIMessage(content=ai_response_accumulator))

        except KeyboardInterrupt:
            print("\nSession closed.")
            break
        except Exception as e:
            print(f"\n[!] Error: {e}")


# =====================================================================
# STEP 2.4: Generalized Background Summary Generator Chain (UNBIASED)
# =====================================================================
def update_background_summary(latest_user_msg: str, latest_ai_msg: str):
    """Executes an unbiased background call to condense conversation history."""
    global running_conversation_summary

    # FIX: Replaced the specific "joke counter" rule with an objective, 
    # universal framework that captures topics, key entities, and quantitative metrics dynamically.
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an objective background data compiler. Your job is to maintain a running conversation summary.
        Review the current summary and the latest exchange, then write an updated, highly concise summary string.
        
        CRITICAL CORE RULES:
        1. Capture all core topics, tasks, or user attributes introduced in the exchange.
        2. Maintain an accurate running count of key actions, requests, or items processed during the session.
        3. Drop old trivial phrasing, but preserve cumulative long-term facts, metrics, and project details.
        4. Do not introduce any conversational fluff or introductory text. Respond ONLY with the updated summary block.
        
        CURRENT SUMMARY:
        {current_summary}
        """),
        ("human", f"New Exchange:\nUser: {latest_user_msg}\nAI: {latest_ai_msg}")
    ])
    
    summary_chain = summary_prompt | llm.bind(options={"num_predict": 300}) | StrOutputParser()
    
    running_conversation_summary = summary_chain.invoke({
        "current_summary": running_conversation_summary
    }).strip()


# =====================================================================
# STEP 2.4: Summary Memory Chat Loop (UPDATED WITH LIVE OUTPUT)
# =====================================================================
def run_summary_chat_loop():
    print("---------------------------------------------------------")
    print("--- Step 2.4: Chat via Live Background Summary Memory ---")
    print("---------------------------------------------------------")
    print("Type your message and press Enter. Type 'exit' to quit.\n")

    # Main prompt template injecting the dynamic global_summary into the system rules
    main_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an entertaining chat assistant. Fulfill user requests immediately.
        
        CONTEXT OF PAST CONVERSATION:
        {global_summary}
        """),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_input}")
    ])
    
    parser = StrOutputParser()
    main_chain = main_prompt | llm.bind(options={"num_predict": 1000}) | parser

    while True:
        try:
            user_text = input("👤 You: ").strip()
            if not user_text:
                continue
            if user_text.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break

            print("🤖 AI: ", end="", flush=True)

            raw_history = summary_memory_db.messages
            recent_history = raw_history[-2:] if raw_history else [AIMessage(content="[Session Started]")]

            ai_response_accumulator = ""
            for chunk in main_chain.stream({
                "global_summary": running_conversation_summary,
                "history": recent_history,
                "user_input": user_text
            }):
                print(chunk, end="", flush=True)
                ai_response_accumulator += chunk
            print()

            # 1. Commit text to our persistent history database object
            summary_memory_db.add_message(HumanMessage(content=user_text))
            summary_memory_db.add_message(AIMessage(content=ai_response_accumulator))

            # 2. Trigger the automated background compression routine
            update_background_summary(user_text, ai_response_accumulator)

            # 3. LIVE OUTPUT DISPLAY: Show the updated background memory log state
            print(f"🧠 [System Memory Update]: {running_conversation_summary}")
            print("-" * 57)  # Separator line for visual scanning

        except KeyboardInterrupt:
            print("\nSession closed.")
            break
        except Exception as e:
            print(f"\n[!] Error: {e}")


# =====================================================================
# Main Execution Entrypoint
# =====================================================================
if __name__ == "__main__":
    run_summary_chat_loop()
