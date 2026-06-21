#!/usr/bin/env python3
"""LangChain Phase 3: Production RAG with an LLM-As-A-Judge Citation Evaluator."""

import os
import json
from typing import List
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# Ensure environment variables are loaded
load_dotenv()

# =====================================================================
# STEP 3.1: Environment Setup
# =====================================================================
base_url = (os.getenv("ANTHROPIC_BASE_URL") or "http://localhost:11434").strip()
if "/v1" in base_url:
    base_url = base_url.replace("/v1/chat/completions", "").replace("/v1", "")

model_name = os.getenv("CLAUDE_MODEL", "qwen3.5:9b").strip()

print("\n-------------------------------------------------------------")
print("--- Phase 3: Production RAG with Judge-Injected Citations ----")
print("-------------------------------------------------------------")
print(f"Target Server: {base_url.strip('/')}")
print(f"Target Model:  {model_name}\n")

# Connect to our local model
llm = ChatOllama(
    base_url=base_url.strip("/"),
    model=model_name,
    temperature=0,  # Hard zero for strict objectivity
    reasoning=False
)

print("⚡ Loading Local Vector Math Engine...")
embeddings_engine = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)


# =====================================================================
# Core RAG Ingestion Routine
# =====================================================================
def load_and_embed_documents() -> Chroma:
    """Manually reads local text files, splits them, and stores them in ChromaDB."""
    print("📦 Ingesting local 'source_documents' directory...")
    
    langchain_documents = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc_folder = os.path.join(script_dir, "source_documents")
    
    if not os.path.exists(doc_folder) or not os.listdir(doc_folder):
        raise FileNotFoundError(
            f"[!] Error: The directory '{doc_folder}' is missing or empty. Please execute 4_build_mock_data.py first!"
        )
    
    for filename in os.listdir(doc_folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(doc_folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read()
                
            doc_obj = Document(
                page_content=file_content,
                metadata={"source": filename}
            )
            langchain_documents.append(doc_obj)
                
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    
    split_chunks = text_splitter.split_documents(langchain_documents)
    print(f"  -> Successfully generated {len(split_chunks)} semantic text chunks.")
    return Chroma.from_documents(documents=split_chunks, embedding=embeddings_engine)


# =====================================================================
# THE LLM-AS-A-JUDGE CITATION INJECTOR
# =====================================================================
def judge_and_inject_citations(raw_answer: str, document_context: str) -> str:
    """Acts as an independent Judge evaluator node.
    
    It cross-references the raw answer against the source documents, 
    verifies factual lineage, and programmatically binds the citation token.
    """
    judge_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a strict, objective Quality Assurance Judge. Your task is to take a raw answer and add precise inline citations to it based on the verified source documents provided.
        
        CRITICAL ENGINE RULES:
        1. Read the raw answer carefully. For every sentence or claim that can be factually proven by a specific document in the sources, append the exact source identifier as 'BRACKET_START_filename.txt_BRACKET_END' at the end of that sentence.
        2. If a sentence contains claims from multiple documents, append both citation tokens consecutively.
        3. Do not modify, rephrase, or expand the original raw answer text. Keep it completely identical, only injecting the required 'BRACKET_START_filename.txt_BRACKET_END' tokens where supported.
        4. If a sentence cannot be proven by any source document, do not add a citation token to it.
        """),
        ("human", """VERIFIED SOURCE DOCUMENTS:
        {document_context}
        
        RAW ANSWER TO EVALUATE:
        {raw_answer}""")
    ])
    
    judge_chain = judge_prompt | llm | StrOutputParser()
    
    # Run the separate background verification call
    return judge_chain.invoke({
        "document_context": document_context,
        "raw_answer": raw_answer
    })


# =====================================================================
# Interactive Chat Workspace Loop Execution
# =====================================================================
def run_interactive_rag():
    vector_store = load_and_embed_documents()
    
    # Node 1: Pure Generation Prompt (No complex formatting rules to slow it down)
    generator_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an internal corporate technical support assistant.
        Answer the user's question accurately using ONLY the provided verified context fragments.
        If the answer cannot be found in the context fragments, say "I do not have access to that corporate data."
        """),
        ("human", """VERIFIED CONTEXT FRAGMENTS:
        {document_context}
        
        USER QUESTION:
        {user_question}""")
    ])
    
    generator_chain = generator_prompt | llm | StrOutputParser()

    print("\n---------------------------------------------------------")
    print("--- NexusFlow AI Judge-Verified RAG Assistant ----------")
    print("---------------------------------------------------------")
    print("Ask any question about your local files. Type 'exit' to quit.\n")

    # ANSI terminal color escape codes
    MAGENTA_BOLD = "\033[1;95m"
    RESET_COLOR = "\033[0m"

    while True:
        try:
            user_query = input("👤 Query: ").strip()
            if not user_query:
                continue
            if user_query.lower() in ["exit", "quit"]:
                print("\nWorkspace closed. Goodbye!")
                break

            # 1. Similarity Retrieval (Fetch chunks from vector store)
            matching_fragments = vector_store.similarity_search(user_query, k=4)
            
            context_list = []
            for doc in matching_fragments:
                filename = doc.metadata.get("source", "unknown_file.txt")
                formatted_chunk = f'--- START DOCUMENT: {filename} ---\n{doc.page_content}\n--- END DOCUMENT ---'
                context_list.append(formatted_chunk)
            context_payload = "\n\n".join(context_list)
            
            # 2. Step 1: Fast conversational text generation
            print("⏳ Step 1/2: Generating core answer response...")
            raw_answer = generator_chain.invoke({
                "document_context": context_payload,
                "user_question": user_query
            })
            
            # Guard clause for out-of-bounds queries
            if "I do not have access" in raw_answer:
                print(f"🤖 Answer: {raw_answer}\n")
                continue
                
            # 3. Step 2: Background factual lineage check via the Judge Node
            print("⚖️ Step 2/2: Verifying source lineage via LLM-As-A-Judge...")
            judged_output = judge_and_inject_citations(raw_answer, context_payload)
            
            # 4. Final Stage: Apply beautiful terminal color formatting to Judge tokens
            print("🤖 Final Verified Answer: ", end="")
            
            # Programmatically swap the Judge's markers for high-visibility terminal text strings
            final_display = judged_output.replace(
                "BRACKET_START_", f" {MAGENTA_BOLD}[📂 "
            ).replace(
                "_BRACKET_END", f"]{RESET_COLOR}"
            )
            
            print(final_display)
            print("\n" + "-" * 57 + "\n")

        except KeyboardInterrupt:
            print("\nSession closed.")
            break
        except Exception as e:
            print(f"\n[!] Error during execution loop: {e}")


if __name__ == "__main__":
    try:
        run_interactive_rag()
    except Exception as e:
        print(f"\n[!] Critical Startup Failure: {e}")
