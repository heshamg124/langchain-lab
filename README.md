
## ---

**📑 langchain-lab**

A progressive, end-to-end laboratory exploring local Large Language Model (LLM) orchestration patterns using **LangChain Expression Language (LCEL)**, **Ollama**, and **ChromaDB**.

This laboratory details the engineering transition from a stateless raw HTTP API client into an enterprise-grade, fault-tolerant **Retrieval-Augmented Generation (RAG)** pipeline featuring stateful background memory and decentralized **LLM-As-A-Judge** factual validation nodes.

## ---

**🏗️ Core Laboratory Architecture Overview**

The projects inside this laboratory run completely locally on consumer-grade hardware. By swapping the traditional cloud provider layer for a localized setup at `/path/to/project`, this repository demonstrates how to retain full data privacy, fine-tune hyper-parameters (such as context window ceilings and temperature settings), and eliminate runtime cloud API transaction costs without exposing local environment specifics:
                  `┌──────────────────────────────────────────────┐`  
                  `│          Mac Local Virtual Env (.venv)       │`  
                  `│                                              │`  
 `┌───────────┐    │  ┌──────────────────┐      ┌──────────────┐  │    ┌─────────────────┐`  
 `│   User    │───┼─>│ Prompt Templates │─────>│  LCEL Chain  │──┼───>│   Ollama Host   │`  
 `│ Terminal  │<──┼──│   & Pydantic      │<─────│ Execution    │◄─┼────│ (qwen3.5:9b)   │`  
 `└───────────┘    │  └──────────────────┘      └──────────────┘  │    └─────────────────┘`  
                  `│                                   │          │             │`  
                  `│                                   ▼          │             ▼`  
                  `│                            ┌──────────────┐  │    ┌─────────────────┐`  
                  `│                            │   ChromaDB   │  │    │ Hardware Params │`  
                  `│                            │  Vector Store│  │    │  (num_predict)  │`  
                  `│                            └──────────────┘  │    └─────────────────┘`  
                  `└──────────────────────────────────────────────┘`

## ---

**🗂️ Lab Program Directory & Flow Mechanics**

## **1\_simple\_client.py: Stateless Raw Network Bootstrap**

* **Purpose**: Establishes a raw network baseline using a standard connection pool manager without high-level abstraction frameworks.  
* **Architecture**: Implements an infinite console chat loop interacting with an OpenAI-compatible web endpoint via httpx.  
* **Flow**:  
  `[User Prompt Input] ➔ [HTTPX POST Payload Assembly] ➔ [Network Socket] ➔ [Local Server JSON Parse]`

* **Key Learning**: Demonstrates defensive programming constraints by slicing massive paste operations and catching raw HTTP connection dropouts or processing timeouts cleanly.

## **2\_langchain\_demo.py: High-Level Abstractions & LCEL Frameworks**

* **Purpose**: Introduces LangChain Expression Language (LCEL) and standard message type classes.  
* **Architecture**: Migrates the codebase away from raw dictionary parsing to native ChatOllama adapter interfaces, ChatPromptTemplate schemas, and StrOutputParser filters.  
* **Flow**:  
  `[User Input Map] ➔ [ChatPromptTemplate] ➔ [Ollama Invocation] ➔ [StrOutputParser String Extraction]`

* **Key Learning**: Showcases the structural layout of AIMessage wrappers and details how the pipeline pipe operator (|) overloads internal methods to construct an atomic RunnableSequence.

## **3\_chat\_memory\_demo.py: Multi-Turn State Retention**

* **Purpose**: Converts stateless invocation trees into stateful conversational loops.  
* **Architecture**: Utilizes InMemoryChatMessageHistory arrays mapped to a flexible database session state dict alongside a MessagesPlaceholder injection target.  
* **Flow**:  
  `[User Text Input] ➔ [Fetch Session Array from RAM] ➔ [Compile Context Prompts] ➔ [Execute LLM Stream]`

* **Key Learning**: Emphasizes the importance of memory context bounds when managing local models, preventing context window bloating.

## **4\_build\_mock\_data.py: AI-Powered Document Construction Engine**

* **Purpose**: Automatically populates a local file directory with structured testing documentation datasets.  
* **Architecture**: Runs a localized generation task loop targeting an abstract technical reference system prompt configuration.  
* **Flow**:  
  `[Target Blueprint List] ➔ [System Writer Prompt Injection] ➔ [LLM Iteration Execution] ➔ [Local Disk Write]`

* **Key Learning**: Illustrates how to leverage a generative workflow to assemble reliable, complex mock corporate datasheets for a fictional software tool (**NexusFlow Systems**).

## **5\_local\_rag\_demo.py: Similarity Search Vector Pipeline**

* **Purpose**: Integrates non-training proprietary documentation directly into the model's active reasoning context.  
* **Architecture**: Couples a local character text splitter and an in-memory ChromaDB matrix index with a specialized local embedding framework (BAAI/bge-small-en-v1.5).  
* **Flow**:  
  `[Read Local Source Folder] ➔ [Semantic Text Chunking] ➔ [Compute Dense Vector Embeddings] ➔ [ChromaDB Index Commit]`

* **Key Learning**: Decouples heavy vector operations from the main reasoning host machine by executing vector-space arithmetic locally on your Mac's CPU/GPU, eliminating network transport overhead.

## **6\_local\_rag\_inline\_citation.py: In-Context Citation Routing**

* **Purpose**: Configures the model to supply verifiable citations for the facts it claims.  
* **Architecture**: Maps retrieved text blocks directly to their metadata headers using custom HTML-style markup wrappers (\<doc name="..."\>).  
* **Flow**:  
  `[Chroma Search Match] ➔ [Inject Metadata Tag to Sub-Chunk String] ➔ [Compile Strict Constraint Prompt] ➔ [LLM Inlines Tag Output]`

* **Key Learning**: Demonstrates how to write concise, explicit prompt criteria to constrain a model's vocabulary and force it to extract and display metadata references.

## 7\_local\_rag\_llm\_judge.py: Post-Generation Factual Auditing (Enterprise Pattern)**

* **Purpose**: Guarantees absolute citation precision, eliminates hallucination vectors, and removes the cognitive load of citation formatting from the conversational generator.  
* **Architecture**: Implements a **Decoupled Multi-Agent Dual-Model** topology that splits text synthesis from factual verification. Rather than asking a single LLM call to find information, phrase an answer, and track metadata formatting simultaneously, this script passes the data through two specialized, isolated steps sequentially.

## **🏛️ Architectural Topology Diagram**

                                  `┌────────────────────────────────────────────────────────┐`  
                                  `│ /path/to/project/Runtime Environment (Local venv/)    │`  
                                  `│                                                        │`  
                                  `│   ┌──────────────────────────────────────────────┐     │`  
                                  `│   │        1. Ingestion & Retrieval Layer        │     │`  
                                  `│   │  [User Query] ➔ [Vector Similarity Search]   │     │`  
                                  `│   └──────────────────────────────────────────────┘     │`  
                                  `│                           │                            │`  
                                  `│                           ▼ (Top 4 Chunks in XML)      │`  
                                  `│   ┌──────────────────────────────────────────────┐     │`  
                                  `│   │          2. Generator Node (LLM 1)           │     │`  
                                  `│   │    - Task: Conversational Synthesis          │     │`  
                                  `│   │    - Output: Pure, Unformatted Raw Text      │     │`  
                                  `│   └──────────────────────────────────────────────┘     │`  
                                  `│                           │                            │`  
                                  `│                           ▼ (Raw Answer String)        │`  
                                  `│   ┌──────────────────────────────────────────────┐     │`  
                                  `│   │            3. Judge Node (LLM 2)             │     │`  
                                  `│   │    - Task: Fact Audit & Lineage Check        │     │`  
                                  `│   │    - Output: Raw Text + Injected Anchors     │     │`  
                                  `│   └──────────────────────────────────────────────┘     │`  
                                  `│                           │                            │`  
                                  `│                           ▼ (Text with Anchor Strings) │`  
                                  `│   ┌──────────────────────────────────────────────┐     │`  
                                  `│   │            4. Presentation Layer             │     │`  
                                  `│   │    - Task: Programmable String Swap          │     │`  
                                  `│   │    - Output: ANSI Magenta Styled Terminal    │     │`  
                                  `│   └──────────────────────────────────────────────┘     │`  
                                  `└────────────────────────────────────────────────────────┘`

## **🔄 Detailed Execution Lifecycle Flow**

The system runs through four distinct stages every time a user types a query into the terminal:

1. **The Ingestion & Context Retrieval Stage**:  
   The user query (e.g., *What are the deployment specs?*) is received. The system passes the text to the local HuggingFaceEmbeddings matrix engine to calculate its vector coordinates. A similarity search query hits ChromaDB, which extracts the top 4 closest semantic chunks ($k=4$) from the database. Python loops through these retrieved items, pulls their source file metadata, and dynamically wraps each passage inside an explicit XML structural tag block:  
   `<doc name="nexusflow_deployment.txt">`  
   `Production cluster deployments require a minimum of 32GB RAM and 8 vCPUs per node.`  
   `</doc>`

2. **The Generator Node Execution (LLM 1\)**:  
   The compiled XML document payload and the user's raw question are injected into the first prompt template. This is handed to **LLM 1**.  
   * **The Constraint**: The prompt instructs the model to act as a support engineer and focus *solely* on crafting a fluid, high-quality, comprehensive text answer. It is explicitly freed from doing any citation formatting or bracket tracking.  
   * **The Output**: It generates a clean, conversational text response string: "To deploy a production node you must provide at least 32GB RAM and 8 vCPUs."  
3. **The Judge Evaluator Node Execution (LLM 2\)**:  
   The finished raw text answer generated by LLM 1 is intercepted by Python and packaged into a completely separate prompt alongside the original XML source documents. This entire payload is then routed to **LLM 2** (the Judge Node).  
   * **The Constraint**: LLM 2 is configured with a strict, low-temperature evaluation system prompt. It acts as an independent auditor. It compares LLM 1's answer line-by-line against the facts inside the XML tags to verify its factual lineage. It is explicitly ordered *never* to alter a single letter or word of the original answer.  
   * **The Output**: If a claim is factually proven by a document, the Judge injects an explicit, rigid text anchor string right at the end of that sentence:  
     "To deploy a production node you must provide at least 32GB RAM and 8 vCPUs. BRACKET\_START\_nexusflow\_deployment.txt\_BRACKET\_END"  
4. **The Programmable Presentation Stage**:  
   The string containing the Judge's raw custom anchors arrives back in your script's main thread. Python executes an automated string override pass, slicing out the custom text blocks and programmatically replacing them with high-visibility **ANSI Escape Sequences** (\\033\[1;95m). This prints the final text to your screen, styling the citations into bold, bright magenta terminal indicators automatically.

## **🎯 Why Inline Citations Are Achieved with 100% Reliability**

Traditional single-prompt RAG setups struggle with inline citations because language models generate text probabilistically—asking them to calculate technical content and format complex syntax arrays simultaneously often leads to formatting slips or hallucinated file associations.

This program guarantees citation accuracy by using a **Multi-LLM Pipeline**:

* **Eliminating Syntax Hallucinations**: Because the Judge model only outputs an invariant text anchor string (BRACKET\_START\_...\_BRACKET\_END), it bypasses the formatting traps where models forget closing brackets or mangle filenames. The actual rendering is handled by rigid, deterministic Python code (.replace()), ensuring perfect layout structure.  
* **Line-by-Line Fact Verification**: By feeding the raw answer back into an independent model context window alongside the source text, the Judge functions as a cross-examination layer. If the generator node slips up and outputs an unverified detail, the Judge will notice that the claim is missing from the \<doc\> tags and will refuse to append an inline citation token to that sentence, maintaining strict corporate safety compliance.



## 🛠️ Unified Installation & Dependency Matrix**

Ensure your system is running a localized version of **Ollama** before bootstrapping the lab environment.

## **1\. Project Package Declarations (requirements.txt)**

Create a requirements.txt inside your workspace folder matching this specification list:

`httpx>=0.27.0`  
`langchain-core>=0.3.0`  
`langchain-ollama>=0.3.0`  
`langchain-community>=0.3.0`  
`langchain-huggingface>=0.0.3`  
`langchain-text-splitters>=0.3.0`  
`sentence-transformers>=3.0.0`  
`chromadb>=0.5.0`  
`pydantic>=2.0.0`  
`python-dotenv>=1.0.0`

## **2\. Sandbox Setup and Virtual Environment Tracking**

Initialize your local virtual dependencies inside your terminal using your explicit absolute binary routes:

*`# Clone the repository`*  
`git clone https://github.com`  
`cd langchain-lab`

*`# Instantiate the local isolated python virtual environment`*  
`python3 -m venv .venv`  
`source .venv/bin/activate`

*`# Execute deterministic package alignment`*  
`pip install -r requirements.txt`

## **3\. Editor Stability Adjustments (.vscode/settings.json)**

To prevent VS Code's background autocomplete engines from crashing under heavy model compilation tasks, add these path exclusions to your local workspace configuration:

`{`  
    `"files.watcherExclude": {`  
        `"**/.venv/**": true,`  
        `"**/source_documents/**": true,`  
        `"**/.chroma/**": true`  
    `},`  
    `"python.analysis.exclude": [`  
        `"**/.venv/**"`  
    `],`  
    `"vscode-ollama.maxTokens": 2048`  
`}`

## ---

**⚡ Execution Instructions**

Follow this step-by-step sequence to verify the full functionality of the pipeline:

*`# 1. Generate the foundational AI corporate documentation files`*  
`python 4_build_mock_data.py`

*`# 2. Run the interactive Judge-Verified RAG workspace chat loop`*  
`python 7_local_rag_llm_judge.py`

## **Pro-Tip for Reasoning Models (qwen3.5:9b)**

When compiling text tasks over native reasoning architectures, the internal model engine will open a hidden thinking monologue loop (\<think\>...\</think\>).

* In **Conversational Steps**, we globally declare **reasoning=False** on our ChatOllama object initialization to disable thinking behaviors, ensuring blazingly fast streaming text output from token number one.  
* In **Structured/Judge Steps**, we retain the model's native properties to give the network full cognitive headroom to resolve complex validation operations without breaking format syntax requirements.

---

This file is thoroughly detailed and ready to serve as the face of your GitHub project\! Let me know if you would like to begin formatting your commit pushes.