import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
from contextlib import asynccontextmanager 

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_ollama import OllamaLLM as Ollama
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch 

from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "jamb_rag_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "jamb_documents")
MONGO_VECTOR_INDEX_NAME = os.getenv("MONGO_VECTOR_INDEX_NAME", "vector_index") 

LLM_MODEL_NAME = "llama3.2:1b"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
rag_chain = None
embeddings = None
vectordb = None
llm = None
mongo_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    Initializes RAG components and handles MongoDB connection.
    """
    global rag_chain, embeddings, vectordb, llm, mongo_client

    print("--- Starting up JAMB AI Assistant API ---")

    if not MONGO_URI:
        print("Error: MONGO_URI environment variable not set. Please set it in your .env file or environment.")
        raise ValueError("MONGO_URI is not set.")

    try:
        print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        print("Embedding model loaded.")

        print(f"Connecting to MongoDB: {MONGO_DB_NAME}.{MONGO_COLLECTION_NAME}...")
        mongo_client = MongoClient(MONGO_URI)
        collection = mongo_client[MONGO_DB_NAME][MONGO_COLLECTION_NAME]

        
        vectordb = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embeddings,
            index_name=MONGO_VECTOR_INDEX_NAME, 
            text_key="text", 
            embedding_key="embedding" 
        )
        print("Vector database (MongoDB Atlas Vector Search) connected.")

        retriever = vectordb.as_retriever(search_kwargs={"k": 10})

        print(f"Initializing LLM: {LLM_MODEL_NAME } (Ollama) at {OLLAMA_BASE_URL}...")
        llm = Ollama(model=LLM_MODEL_NAME, base_url=OLLAMA_BASE_URL, temperature=0.6, top_p=0.8, repeat_penalty=1.05, top_k=20)

        try:
            llm.invoke("Hi") 
            print("LLM initialized and responsive.")
        except Exception as e:
            print(f"Error connecting to Ollama LLM: {e}. Is `ollama serve` running and accessible at {OLLAMA_BASE_URL}? Is the model '{LLM_MODEL_NAME}' pulled?")
            raise

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a JAMB assistant. Answer the user's question ONLY using the following context. "
                "If the answer is not directly inferable or found within the context, clearly state 'The information is not available in the provided documents.' "
                "Be concise and directly address the question. Do NOT add any conversational filler or make up information.\n\nContext:\n{context}"
            )),
            ("human", "{input}"),
        ])

        document_chain = create_stuff_documents_chain(llm, prompt_template)

        rag_chain = create_retrieval_chain(retriever, document_chain)
        print("RAG pipeline setup complete.")

    except Exception as e:
        print(f"Error during API startup: {e}")
        raise

    yield

    print("--- Shutting down JAMB AI Assistant API ---")
    if mongo_client:
        mongo_client.close() 
        print("MongoDB client closed.")


app = FastAPI(
    title="JAMB AI Assistant API",
    description="An AI assistant powered by RAG to answer questions based on JAMB documents.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    custom_intro: Optional[str] = None

class AnswerResponse(BaseModel):
    answer: str

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Receives a question and returns an AI-generated answer, optionally with a custom introduction.
    """
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="AI Assistant not initialized. Please check server logs for startup errors.")

    try:
        if request.question.lower().strip() in ["who are you?", "what are you?"]:
            return AnswerResponse(answer="I am your JAMB Assistant, an AI designed to provide information based on JAMB documents.")

        response = rag_chain.invoke({"input": request.question})

        answer = response.get("answer", "No answer found.")
        if request.custom_intro:
            answer = request.custom_intro + "\n\n" + answer

        return AnswerResponse(answer=answer)
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while processing your request: {e}")

@app.get("/health")
async def health_check():
    """
    Checks the health of the API and its components.
    """
    status = {"api_status": "ok"}
    if rag_chain:
        status["rag_pipeline_status"] = "initialized"
    else:
        status["rag_pipeline_status"] = "not_initialized"
    if mongo_client and mongo_client.admin.command('ping'):
        status["mongodb_status"] = "connected"
    else:
        status["mongodb_status"] = "disconnected"
    return status