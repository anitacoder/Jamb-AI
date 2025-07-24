import os
from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_text_file(filepath, chunk_size=1000, chunk_overlap=200, output_dir="Extracted-Data/chunk-text"):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True, 
    )
    chunks = text_splitter.create_documents([text]) 

    base_filename = os.path.basename(filepath).replace(".txt", "")
    chunk_output_dir = os.path.join(output_dir, base_filename)
    os.makedirs(chunk_output_dir, exist_ok=True)

    for i, chunk in enumerate(chunks):
        chunk_filename = os.path.join(chunk_output_dir, f"{base_filename}_chunk_{i+1}.txt")
        with open(chunk_filename, "w", encoding="utf-8") as f:
            f.write(chunk.page_content) 

    print(f"Chunked {filepath} into {len(chunks)} parts in {chunk_output_dir}")
    return chunks

def process_and_chunk_all_texts(input_dir="Extracted-Data/extracted_pdfs", final_output_base_dir="Extracted-Data/chunk"):
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(input_dir, filename)
            chunk_text_file(filepath, output_dir=final_output_base_dir)

if __name__ == "__main__":
    print("Starting text chunking...")
    process_and_chunk_all_texts()
    print("Text chunking complete.")