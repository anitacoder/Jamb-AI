import os
from pypdf import PdfReader
from langchain.docstore.document import Document

def extract_text_from_pdf(pdf_path):
    """Extracts text from a single PDF and returns it."""
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    return None

def load_and_extract_pdfs(input_dir="Data", output_dir="Extracted-Data/extracted_pdfs"):
    """
    Processes all PDFs in input_dir, extracts text, saves to output_dir,
    and returns a list of LangChain Document objects.
    """
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    base_project_dir = os.path.dirname(current_script_dir) 

    actual_input_dir = os.path.join(base_project_dir, input_dir)
    actual_output_dir = os.path.join(base_project_dir, output_dir)


    os.makedirs(actual_output_dir, exist_ok=True)

    extracted_documents = []

    print(f"Searching for PDFs in: {actual_input_dir}")
    if not os.path.exists(actual_input_dir):
        print(f"Warning: Input directory '{actual_input_dir}' does not exist.")
        return [] 

    for filename in os.listdir(actual_input_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(actual_input_dir, filename)
            print(f"Extracting text from: {pdf_path}")
            extracted_text = extract_text_from_pdf(pdf_path)

            if extracted_text:
                text_filename = os.path.splitext(filename)[0] + ".txt"
                output_path = os.path.join(actual_output_dir, text_filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)
                print(f"Saved extracted text to: {output_path}")

                extracted_documents.append(Document(page_content=extracted_text, metadata={"source": filename}))
            else:
                print(f"Skipped {filename} due to extraction error or empty content.")
    return extracted_documents

if __name__ == "__main__":
  
    print("Running extract_data.py directly...")
    extracted_docs = load_and_extract_pdfs(input_dir="Data", output_dir="Extracted-Data/extracted_pdfs")
    print(f"Total documents extracted: {len(extracted_docs)}")