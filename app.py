import streamlit as st
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import streamlit as st
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from dotenv import load_dotenv
import os
import ollama


def extract_text_from_pdf(uploaded_file):
    """Extracts and returns full text from a PDF file-like object.

    Returns a single string (joined pages)."""
    reader = PdfReader(uploaded_file)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def chunk_text(text, chunk_size=800, overlap=100):
    """Split `text` into fixed-size chunks with overlap.

    Returns list of text chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def create_embeddings_and_index(chunks, model_name="all-MiniLM-L6-v2"):
    """Load embedding model, compute embeddings for `chunks`, and build a FAISS index.

    Returns (model, embeddings_array, index).
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode(chunks)
    embeddings = np.array(embeddings).astype("float32")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return model, embeddings, index


def retrieve_relevant_chunks(question, model, index, chunks, k=3):
    """Return the concatenated relevant chunks and the indices for a `question`."""
    q_emb = model.encode([question])
    q_emb = np.array(q_emb).astype("float32")
    distances, indices = index.search(q_emb, k=k)
    relevant_chunks = "\n\n".join(chunks[i] for i in indices[0])
    return relevant_chunks, indices


def build_prompt(relevant_chunks, question):
    """Create a user-facing prompt to send to the LLM."""
    return f"""
Use the PDF content below to answer the question.PdfReader

PDF Content: 
{relevant_chunks}

Question: {question}

Answer in simple student-friendly language.
"""


st.title("AI Study Assistant")
if "messages" not in st.session_state:
    st.session_state.messages = []

uploaded_file = st.file_uploader("Upload your lecture PDF", type="pdf")

if uploaded_file:
    # Extract and chunk
    text = extract_text_from_pdf(uploaded_file)
    chunks = chunk_text(text)

    # Build embeddings and index (this can be cached later)
    with st.spinner("Creating embeddings..."):
        model, embeddings, index = create_embeddings_and_index(chunks)

    question = st.text_input("Ask a question about your PDF content")
    if question:
        st.subheader("Your Question")
        st.write(question)

        relevant_chunks, indices = retrieve_relevant_chunks(question, model, index, chunks, k=3)

        prompt = build_prompt(relevant_chunks, question)

        with st.spinner("Generating answer..."):
            response = ollama.chat(
                model="llama3",
                messages=[{"role": "user", "content": prompt}],
            )

        st.subheader("AI Answer")
        st.write(response["message"]["content"])
        answer = response["message"]["content"]

        st.session_state.messages.append({"question": question, "answer": answer})

        st.subheader("Sources Used")
        for i in indices[0]:
            st.write(f"Source: chunks[{i}]")
            st.write("---")

        st.subheader("Chat History")
        for msg in st.session_state.messages:
            st.write(f"Q: {msg['question']}")
            st.write(f"A: {msg['answer']}")
            st.write("---")





