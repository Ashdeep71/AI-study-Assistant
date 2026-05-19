import streamlit as st
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from dotenv import load_dotenv
import os
import ollama




def chunk_text(text, chunk_size=800, overlap=100):
    chunks= []
    start= 0
    while start < len(text):
        end= start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
    

st.title("AI Study Assistant")

uploaded_file= st.file_uploader("Upload your lecture PDF", type= "pdf")

if uploaded_file:
    reader = PdfReader(uploaded_file)
    text= ""

    for page in reader.pages:
        text+= page.extract_text() or ""

    chunks = chunk_text(text)
    
    st.subheader("Chunks Created")
    st.write(f"Total chunks: {len(chunks)}")

    st.subheader("First Chunk Preview")
    st.write(chunks[0])

    model= SentenceTransformer("all-MiniLM-L6-v2")
    embeddings= model.encode(chunks)

    embeddings= np.array(embeddings).astype("float32")

    index= faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    st.subheader("Embeddings Created")
    st.write(f"Number of chunks: {len(chunks)}")
    st.write(f"Embedding shape: {embeddings.shape}")

    question= st.text_input("Ask a question about your PDF content")
    if question: 
        st.subheader("Your Question")
        st.write(question)
        question_embedding= model.encode([question])
        question_embedding= np.array(question_embedding).astype("float32")

        distances, indices= index.search(question_embedding, k=3)
        st.subheader("Most Relevant Chunks")

        for i in indices[0]:
            st.write(chunks[i])
            st.write("---")
        
        relevant_chunks= "\n\n".join(chunks[i] for i in indices[0])

        prompt= f"""
Use the PDF content below to answer the question.PdfReader

PDF Content: 
{relevant_chunks}

Question: {question}

Answer in simple student-friendly language.
"""
        response= ollama.chat(
            model= "llama3",
            messages=[{'role': 'user', 'content': prompt}]
        )

        st.subheader("AI Answer")
        st.write(response['message']['content'])
      



