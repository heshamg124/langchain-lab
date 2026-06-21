#!/usr/bin/env python3
"""LangChain Phase 3: Interactive Local Document Chat Workspace with Metadata Sources."""

import os
from typing import Generator, Iterable
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document  # Import Document for manual attachment

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

# Main Chat Model
llm = ChatOllama(
    base_url=base_url.strip("/"),
    model=model_name,
    temperature=0, 
    reasoning=False
)

# Local HuggingFace Embeddings Engine
print("⚡ Loading Local Vector Math Engine...")
embeddings_engine = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)


# =====================================================================
# Core RAG Ingestion Routine (Updated with Metadata Injection)
# =====================================================================
def load_and_embed_documents() -> Chroma:
    """Manually reads local text files, splits them, injects filename metadata, and stores in ChromaDB."""
    print("📦 Ingesting local 'source_documents' directory...")
    
    # We create a list to hold official LangChain Document objects (text + metadata dictionary)
    langchain_documents = []
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc_folder = os.path.join(script_dir, "source_documents")
    
    if not os.path.exists(doc_folder) or not os.listdir(doc_folder):
        raise FileNotFoundError(
            f"[!] Error: The directory '{doc_folder}' is missing or empty. Please execute 4_build_mock_data.py first!"
        )
    
    # Read each text file manually
    for filename in os.listdir(doc_folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(doc_folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read()
                
            # INJECTION: Create a proper Document object and store the raw filename inside the metadata dict
            doc_obj = Document(
                page_content=file_content,
                metadata={"source": filename}  # This will be preserved across text splitting
            )
            langchain_documents.append(doc_obj)
                
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=30
    )
    
    # Split the documents. LangChain automatically copies the original metadata down to every smaller chunk
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
        If the answer cannot be found in the context fragments, say "I do not have access to that corporate data."
        
        VERIFIED CONTEXT FRAGMENTS:
        {document_context}
        """),
        ("human", "{user_question}")
    ])
    
    parser = StrOutputParser()
    chain = r_chain = rag_prompt | llm | parser

    print("---------------------------------------------------------")
    print("--- NexusFlow AI Corporate Knowledge Base Assistant ---")
    print("---------------------------------------------------------")
    print("Ask any question about your local files. Type 'exit' to quit.\n")

    while True:
        try:
            user_query = input("👤 Query: ").strip()
            if not user_query:
                continue
            if user_query.lower() in ["exit", "quit"]:
                print("\nWorkspace closed. Goodbye!")
                break

            # 1. Fetch matching chunks from ChromaDB
            matching_fragments = vector_store.similarity_search(user_query, k=4)
            
            # Combine snippets into one text block for the system prompt instructions
            context_payload = "\n---\n".join([doc.page_content for doc in matching_fragments])
            
            # 2. Stream out the live response tokens word-by-word
            print("🤖 Answer: ", end="", flush=True)
            
            raw_stream = chain.stream({
                "document_context": context_payload,
                "user_question": user_query
            })
            
            for chunk in raw_stream:
                print(chunk, end="", flush=True)
            print() # End answer text block line

            # 3. METADATA STEP: Extract and display the exact source files used
            # We use a set to automatically eliminate duplicate file names if multiple chunks came from the same file
            unique_sources = set()
            for doc in matching_fragments:
                # Pull out the "source" dictionary string we injected during loading
                file_source = doc.metadata.get("source", "Unknown Document Source")
                unique_sources.add(file_source)
                
            # Print the panel beautifully right below the streaming block
            print("📂 [Source Material Consulted]:")
            for source in sorted(unique_sources):
                print(f"  📄 {source}")
            print() # Trailing separation line break

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
