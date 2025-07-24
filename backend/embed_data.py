import os
from pydantic import BaseModel
from typing import Optional
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from dotenv import load_dotenv
from extract_data import load_and_extract_pdfs

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "jamb_rag_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "jamb_documents")
MONGO_VECTOR_INDEX_NAME = os.getenv("MONGO_VECTOR_INDEX_NAME", "vector_index")

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

PDF_INPUT_DIR = "../Data" 
EXTRACTED_TEXT_OUTPUT_DIR = "../Extracted-Data/extracted_pdfs"

JAMB_CONTENT = {
    "jamb_overview_mandate.txt": """
**Overview of JAMB**

The Joint Admissions and Matriculation Board (JAMB) is a Nigerian entrance examination board for tertiary-level institutions. It is a federal government agency responsible for overseeing and conducting the admission process into higher education institutions in Nigeria, including universities, polytechnics, colleges of education, and monotechnics. JAMB's headquarters are located in Bwari, Abuja.

**Mandate and Core Functions**

JAMB was established in 1978 to standardize and streamline admissions. Its main responsibilities include:
1. Conducting the Unified Tertiary Matriculation Examination (UTME).
2. Setting admission guidelines in collaboration with institutions.
3. Managing admissions using the Central Admissions Processing System (CAPS).
4. Issuing official admission letters.
5. Disseminating admissions-related information.
6. Maintaining uniform academic standards.
7. Promoting access to education across regions.
8. Assisting in policy formulation.
9. Conducting educational research.

**Establishment Details**
JAMB was founded under the leadership of **General Olusegun Obasanjo**, who served as the Head of State during its establishment and was instrumental in its creation.
    """,

"jamb_history_evolution.txt": """
**History of JAMB**

The Joint Admissions and Matriculation Board (JAMB) was officially established by Act (No. 2 of 1978) of the Federal Military Government on February 13, 1978. It was founded under the leadership of **General Olusegun Obasanjo**, who served as the Head of State during its establishment and was instrumental in its creation. The primary objective was to centralize and standardize the fragmented admission processes previously handled individually by each Nigerian university.

**Notable Registrars:**
- Michael Saidu Angulu (1978–1986): Pioneer registrar.
- Prof. Bello Salim: Introduced e-registration.
- Prof. Dibu Ojerinde (2007–2016): Spearheaded digital transformation.
- **Professor Ishaq Oloyede is the current Registrar of JAMB, having been appointed in 2016.** He is renowned for strengthening reforms and transparency.
""",

    "jamb_examination_structure.txt": """
**UTME Structure and Marking**

JAMB's UTME is a computer-based test consisting of 4 subjects (English is mandatory) and 160 questions in total. The exam lasts 2 hours.

Subject examples:
- **Medicine:** English, Biology, Chemistry, Physics.
- **Engineering:** English, Mathematics, Physics, Chemistry.
- **Law:** English, Literature, Government, CRS or IRS.

Each question carries one mark. No negative marking. Score scale:
- 360–400: Excellent
- 320–359: Very Good
- 280–319: Good
- 240–279: Average
- 200–239: Below Average
- 160–199: Poor
- 0–159: Very Poor

UTME score is combined with O’Level and sometimes Post-UTME for admission.
    """,

    "jamb_admission_process.txt": """
**Admission Process and Requirements**

Eligibility:
- Candidates must be at least **16 years old** by September 30 of the admission year.
- Must possess a valid **NIN** (National Identification Number).
- Must have completed secondary school or equivalent.

Steps:
1. Send NIN to 55019/66019 via SMS to get JAMB profile code.
2. Purchase JAMB ePIN using the code.
3. Complete registration at an accredited CBT center (biometric capture inclusive).
4. Collect registration slip, syllabus, reading text.
5. Print exam slip showing venue, date, time.

Registration Fees (2025):
- UTME with Mock: ₦8,700
- UTME without Mock: ₦7,200
- Direct Entry (DE): ₦5,700

**Direct Entry (DE):**
- For holders of NCE, ND, HND, A’Levels.
- Admission into 200-level.
- Cannot register for UTME in same year.

**O'Level Result Upload:**
- Must upload result via JAMB portal (CAPS) or risk disqualification.

**Post-UTME:**
- Some institutions conduct further screening.
- Aggregate score may combine UTME, Post-UTME, and O'Level.

**CAPS:**
- Monitor status (Admitted, Not Admitted, etc.).
- Accept/reject admission.
- Handle institution or course change offers.

**JAMB Regularization:**
- For candidates who got admission without going through JAMB.
    """,

    "jamb_latest_updates_2025.txt": """
**Latest JAMB Updates (2025)**

1.  **Mop-Up Exam (June 28, 2025):**
    * Over 98,000 candidates eligible due to technical issues during main UTME.
    * Very low turnout (~12%).

2.  **Malpractice Watch:**
    * Many impersonation cases flagged (e.g. false albino claims to bypass facial recognition).
    * Security agencies tracking offenders using NIN, phone numbers.

3.  **Direct Entry Forgery:**
    * 14 DE applicants caught with forged certificates (esp. from 2017–2020).
    * JAMB warns institutions about validating results.

4.  **Result Release:**
    * Mop-up exam results were expected same day but delayed to June 30 for extra fraud screening.

Registrar Oloyede emphasized a zero-tolerance stance on impersonation, forgery, and poor integrity practices in admission processes.
    """
}

def load_documents_from_memory():
    """Loads text content from the in-memory JAMB_CONTENT dictionary."""
    documents = []
    for filename, content in JAMB_CONTENT.items():
        documents.append(Document(page_content=content.strip(), metadata={"source": filename}))
    print(f"Loaded {len(documents)} document(s) from in-memory content.")
    return documents

def ingest_data_to_mongodb():
    """
    Handles the process of loading, chunking, embedding, and ingesting documents
    into MongoDB Atlas Vector Search.
    """
    print("--- Starting JAMB content embedding and MongoDB ingestion ---")

    if not MONGO_URI:
        print("Error: MONGO_URI environment variable not set. Please set it in your .env file or environment.")
        return

    documents = load_documents_from_memory()

    if not documents:
        print("No documents to embed.")
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")

    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    print("Embedding model loaded.")

    print(f"Connecting to MongoDB at {MONGO_URI}...")
    mongo_client = None
    try:
        mongo_client = MongoClient(MONGO_URI)
        collection = mongo_client[MONGO_DB_NAME][MONGO_COLLECTION_NAME]
        print(f"Connected to MongoDB. Using database '{MONGO_DB_NAME}' and collection '{MONGO_COLLECTION_NAME}'.")
        MongoDBAtlasVectorSearch.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection=collection,
            index_name=MONGO_VECTOR_INDEX_NAME, 
        )
        print("Documents embedded and ingested into MongoDB Atlas Vector Search.")

    except Exception as e:
        print(f"Error during MongoDB ingestion: {e}")
        print("Please ensure:")
        print(f"  1. Your MONGO_URI is correct and has access to '{MONGO_DB_NAME}'.")
        print(f"  2. MongoDB server is running and accessible (if local).")
        print(f"  3. Your Atlas Vector Search index '{MONGO_VECTOR_INDEX_NAME}' is correctly configured for the collection '{MONGO_COLLECTION_NAME}' and has the correct `numDimensions` (384 for {EMBEDDING_MODEL_NAME}).")
        return

    finally:
        if mongo_client:
            mongo_client.close()
            print("MongoDB client closed.")

    print("--- Embedding and MongoDB ingestion complete ---")

if __name__ == "__main__":
    ingest_data_to_mongodb()