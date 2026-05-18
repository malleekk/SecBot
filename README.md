# 🛡️ SecBot — Assistant Cybersécurité RAG

Chatbot intelligent basé sur RAG (Retrieval-Augmented Generation)
qui répond aux questions de cybersécurité en s'appuyant sur
des sources officielles (OWASP, NIST).

## Membres
- Membre 1 : [malek laamiri]
- Membre 2 : [malek marouani]  
- Membre 3 : [sarra ouereghemi]

## Installation
pip install -r requirements.txt

## Configuration
Créez un fichier .env :
GROQ_API_KEY=votre_cle_groq

## Lancement
python ingest.py
streamlit run app.py

## Technologies utilisées
- LangChain
- FAISS
- Groq (LLaMA3)
- Streamlit
- HuggingFace Embeddings

## Sources de données
- OWASP Top 10 2021
- OWASP API Security
- NIST Cybersecurity Framework