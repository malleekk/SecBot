import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

def charger_documents():
    print("📂 Chargement des PDFs...")
    loader = PyPDFDirectoryLoader("docs/")
    documents = loader.load()
    print(f"✅ {len(documents)} page(s) chargée(s)")
    return documents

def decouper_texte(documents):
    print("✂️  Découpage du texte...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    print(f"✅ {len(chunks)} morceaux créés")
    return chunks

def creer_embeddings(chunks):
    print("🧠 Création des embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local("faiss_index")
    print("✅ Base vectorielle sauvegardée !")
    return db

def charger_base():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    db = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )
    return db

if __name__ == "__main__":
    docs = charger_documents()
    chunks = decouper_texte(docs)
    creer_embeddings(chunks)
    print("\n🎉 Indexation terminée !")