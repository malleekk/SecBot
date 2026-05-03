import streamlit as st
import os
from ingest import charger_base, charger_documents, decouper_texte, creer_embeddings
from chatbot import creer_secbot, poser_question

st.set_page_config(
    page_title="SecBot",
    page_icon="🛡️",
    layout="wide"
)

with st.sidebar:
    st.title("🛡️ SecBot")
    st.caption("Assistant Cybersécurité")
    st.divider()

    if st.button("📂 Indexer les PDFs", use_container_width=True):
        with st.spinner("Indexation en cours..."):
            docs = charger_documents()
            chunks = decouper_texte(docs)
            creer_embeddings(chunks)
            st.session_state.chatbot = None
            st.success(f"✅ {len(docs)} page(s) indexée(s) !")

    st.divider()

    if st.button("🗑️ Effacer conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chatbot = None
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chatbot" not in st.session_state:
    st.session_state.chatbot = None

if os.path.exists("faiss_index") and st.session_state.chatbot is None:
    with st.spinner("Chargement de SecBot..."):
        db = charger_base()
        st.session_state.chatbot = creer_secbot(db)

st.title("🛡️ SecBot — Assistant Cybersécurité")
st.caption("Basé sur OWASP, NIST et les meilleures références sécurité")
st.divider()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("Posez votre question de cybersécurité...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        if not os.path.exists("faiss_index"):
            st.error("❌ Indexez d'abord les PDFs (bouton à gauche) !")
        else:
            with st.spinner("SecBot analyse les sources..."):
                reponse, sources = poser_question(st.session_state.chatbot, question)
                st.write(reponse)

                if sources:
                    with st.expander("📎 Sources consultées"):
                        for s in sources:
                            st.markdown(f"- **{s['source']}** — page {s['page']}")
                            st.caption(s['extrait'])

                st.session_state.messages.append(
                    {"role": "assistant", "content": reponse}
                )