#!/usr/bin/env python3
"""LangChain Phase 3: Interactive Local Document Chat Workspace with High-Visibility Citations."""

import os
from typing import Generator, Iterable
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

print("\n-----------------------------------------")
print("--- Phase 3: Interactive RAG Chat Loop ---")
print("-----------------------------------------")
print(f"Target Server: {base_url.strip('/')}")
print(f"Target Model:  {model_name}\n")

llm = ChatOllama(
    base_url=base_url.strip("/"),
    model=model_name,
    temperature=0, 
    reasoning=False
)

print("⚡ Loading Local Vector Math Engine...")
embeddings_engine = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)


# =====================================================================
# Core RAG Ingestion Routine (Tuned Context Windows)
# =====================================================================
def load_and_embed_documents() -> Chroma:
    """Manually reads local text files, splits them with safety overlap metrics, and stores in ChromaDB."""
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
                
    # PRODUCTION CALIBRATION: Increased chunk sizing to 500 and overlap to 100 
    # to protect multi-line database specifications from truncating.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    
    split_chunks = text_splitter.split_documents(langchain_documents)
    print(f"  -> Successfully generated {len(split_chunks)} semantic text chunks with metadata.")
    
    print("🧠 Computing mathematical vector math LOCALLY on your Mac...")
    vector_db = Chroma.from_documents(
        documents=split_chunks,
        embedding=embeddings_engine
    )
    print("💾 Vector database index is ready.\n")
    return vector_db


# =====================================================================
# Interactive Chat Workspace Loop Execution
# =====================================================================
def run_interactive_rag():
    vector_store = load_and_embed_documents()
    
    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an internal corporate technical support assistant.
        Answer the user's question accurately using ONLY the provided verified context fragments.
        
        CRITICAL CITATION RULE: The context contains blocks wrapped in <doc name="filename.txt">...</doc> tags.
        When you use information from a document, you MUST append its file name using this EXACT tag structure right after the fact: 
        SOURCE_TAG_filename.txt_ENDTAG
        
        Example: The port is 9443 SOURCE_TAG_nexusflow_architecture.txt_ENDTAG.
        Do not add spaces inside the tag. Do not use brackets. Use this format strictly.
        
        If the answer cannot be found in the context fragments, say "I do not have access to that corporate data."
        """),
        ("human", """VERIFIED CONTEXT FRAGMENTS:
        {document_context}
        
        USER QUESTION:
        {user_question}""")
    ])
    
    parser = StrOutputParser()
    chain = r_chain = rag_prompt | llm | parser

    print("---------------------------------------------------------")
    print("--- NexusFlow AI Corporate Knowledge Base Assistant ---")
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

            matching_fragments = vector_store.similarity_search(user_query, k=4)
            
            context_list = []
            for doc in matching_fragments:
                filename = doc.metadata.get("source", "unknown_file.txt")
                formatted_chunk = f'<doc name="{filename}">\n{doc.page_content}\n</doc>'
                context_list.append(formatted_chunk)
                
            context_payload = "\n\n".join(context_list)
            
            print("🤖 Answer: ", end="", flush=True)
            
            raw_stream = chain.stream({
                "document_context": context_payload,
                "user_question": user_query
            })
            
            # Robust stateful text streaming buffer window
            stream_buffer = ""
            
            for chunk in raw_stream:
                stream_buffer += chunk
                
                # Check if we have a fully completed tag inside our tracking buffer
                if "SOURCE_TAG_" in stream_buffer and "_ENDTAG" in stream_buffer:
                    # Parse the string boundaries cleanly using standard split arrays
                    before_tag, current_tag_payload = stream_buffer.split("SOURCE_TAG_", 1)
                    filename, after_tag = current_tag_payload.split("_ENDTAG", 1)
                    
                    # Print the leading text content
                    if before_tag:
                        print(before_tag, end="", flush=True)
                    
                    # Output the beautifully colored terminal bracket tag
                    print(f" {MAGENTA_BOLD}[📂 {filename}]{RESET_COLOR}", end="", flush=True)
                    
                    # Reset the buffer to track remaining upcoming text stream tokens
                    stream_buffer = after_tag
                
                # If there's content trailing before an upcoming open tag block, print it
                elif "SOURCE_TAG_" not in stream_buffer:
                    print(stream_buffer, end="", flush=True)
                    stream_buffer = ""
            
            # Empty out any residual trailing characters
            if stream_buffer:
                print(stream_buffer, end="", flush=True)
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
