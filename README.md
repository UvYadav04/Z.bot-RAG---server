# 🤖 Z.bot — Retrieval Augmented Generation (RAG) Server

Z.bot is a **high-performance backend system for document-aware AI conversations**, built using a Retrieval Augmented Generation (RAG) pipeline.

It allows users to upload documents, query them intelligently, and receive **real-time streamed responses** powered by LLMs — with **context retention, minimal hallucination, and scalable architecture**.

---

## ✨ Key Features

* 📄 **PDF Document Ingestion**

  * Upload one or more documents
  * Automatic parsing, chunking, and embedding

* 🧠 **RAG-based Querying**

  * Context-aware responses using relevant document chunks
  * Reduces hallucination and improves accuracy

* ⚡ **Real-time Streaming Responses**

  * Token-level streaming from LLM → client
  * Significantly improves perceived latency (low TTFT impact)

* 🔍 **Semantic Retrieval (ChromaDB)**

  * Efficient similarity search across:

    * Document chunks
    * Past chat history

* 💬 **Persistent Chat Memory**

  * Past messages embedded and stored
  * Retrieved selectively for future queries

* 👤 **Dual Mode Support**

  * Works for:

    * Logged-in users (persistent data)
    * Anonymous users (session-based)

* 🔐 **Authentication & Sessions**

  * JWT-based authentication
  * Session binding for request context
  * Google OAuth login support

* ♻️ **Multi-Chat Support**

  * Create new chats
  * Resume previous conversations
  * Maintain isolated contexts per chat

---

## 🏗️ System Architecture

```
User Query
   ↓
Preprocessing (normalize, spelling, contractions)
   ↓
ChromaDB (vector search)
   ├── Relevant document chunks
   └── Relevant past chat history
   ↓
LLM (Groq)
   ↓
Streaming Response (token-by-token)
   ↓
Client UI
```

---

## 🛠️ Tech Stack

### 🔹 Core Backend

* **Python**
* **FastAPI**

### 🔹 AI / ML

* **Sentence Transformers** → embeddings
* **Groq LLM API** → inference
* *(Previously experimented with fine-tuned models — switched due to TTFT constraints)*

### 🔹 Data & Storage

* **ChromaDB** → vector database (documents + chat memory)
* **MongoDB** → document metadata & user data

### 🔹 Document Processing

* **Docling** → parsing & chunking PDFs

### 🔹 Auth & Sessions

* **JWT Tokens**
* **Session Middleware**
* **Google OAuth**

---

## 📂 Data Flow

### 📄 Document Upload

1. User uploads PDF(s)

2. Docling parses and chunks content

3. Each chunk is:

   * Embedded using Sentence Transformers
   * Stored in ChromaDB

4. Metadata stored:

   * `chunk_id`
   * `page_number`
   * `heading`
   * `user_id` (if logged in)
   * `session_id`
   * `document_id`

5. For logged-in users:

   * Document metadata is stored in MongoDB
   * Document IDs are linked for future retrieval

---

### 💬 Query Flow

1. User sends query

2. Preprocessing:

   * Lowercasing
   * Spelling correction
   * Contraction handling

3. Retrieve context from ChromaDB:

   * Relevant document chunks
   * Relevant past chat messages

4. Send enriched prompt → Groq LLM

5. Stream response:

   * Token-by-token delivery to client

---

### 🧠 Chat Memory

* Each interaction (user + assistant):

  * Embedded using same encoder
  * Stored in ChromaDB with metadata

* Future queries:

  * Retrieve **only relevant past messages**
  * Prevents:

    * Context overload
    * Irrelevant history injection
    * Hallucination

---

## 🔐 Authentication Flow

* **Logged-in users**

  * JWT issued
  * Session maintained
  * Documents persist in MongoDB

* **Guest users**

  * Session-based tracking
  * Temporary context handling

* Middleware:

  * Authenticates each request
  * Binds session → request lifecycle

---

## 🔁 Streaming Implementation

* Uses **chunked streaming**
* Response starts as soon as first token is generated
* Reduces:

  * Time To First Token (TTFT)
  * Perceived latency

---

## ⚙️ API Overview

### 🔹 Upload Document

```http
POST /documents/upload
```

* Accepts: `multipart/form-data`
* Processes and indexes PDF(s)

---

### 🔹 Query (Streaming)

```http
POST /chat/query
```

**Request Body:**

```json
{
  "query": "user question",
  "selected_chat_id": "chat_id",
  "document_ids": ["doc1", "doc2"]
}
```

**Response:**

* Streamed text (chunked)

---

## ▶️ Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/z-bot.git
cd z-bot/server
```

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Environment variables

Create a `.env` file:

```env
MONGO_URI=your_mongo_uri
CHROMA_DB_PATH=./chroma
GROQ_API_KEY=your_key
JWT_SECRET=your_secret
```

---

### 4. Run the server

```bash
uvicorn main:app --reload
```

---

## 📈 Design Decisions

* ❌ Avoided self-hosted fine-tuned models
  → High TTFT due to hardware constraints

* ✅ Switched to Groq
  → Faster inference + better streaming UX

* ✅ Vector-based chat memory
  → Selective recall instead of full history

---

## 🚀 Future Improvements

* Advanced reranking for better context selection
* Document versioning
* Rate limiting & monitoring
* Better retrieved document merging strategies
* More good ways to parse uploaded documents

---

## 🧠 Why Z.bot?

Z.bot is designed to solve a core problem in AI apps:

> “How do we make LLM responses grounded, fast, and context-aware — without overwhelming the model?”

By combining:

* **RAG (documents + chat memory)**
* **Efficient vector search**
* **Streaming-first UX**
