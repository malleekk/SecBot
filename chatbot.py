import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

# Historique de conversation
chat_history = []

def formater_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def creer_secbot(db):
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1
    )

    retriever = db.as_retriever(search_kwargs={"k": 4})

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Tu es SecBot, un assistant expert en cybersécurité.
Tu réponds UNIQUEMENT en te basant sur le contexte fourni.

RÈGLES :
1. Si l'info n'est pas dans le contexte, dis : "Je n'ai pas cette information dans ma base SecBot."
2. Cite toujours la source. Exemple : "Selon l'OWASP Top 10..."
3. Structure ta réponse :
   📌 Définition : ...
   ⚠️ Risque : ...
   🛡️ Protection : ...
   💡 Exemple : ...
4. Réponds toujours en français.
5. Ne donne JAMAIS d'aide pour mener des attaques.

CONTEXTE :
{context}"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])

    chain = prompt | llm | StrOutputParser()

    return {"chain": chain, "retriever": retriever}


def poser_question(chatbot, question):
    global chat_history

    # Chercher les documents pertinents
    docs = chatbot["retriever"].invoke(question)
    context = formater_docs(docs)

    # Générer la réponse
    reponse = chatbot["chain"].invoke({
        "context": context,
        "chat_history": chat_history,
        "question": question
    })

    # Mettre à jour l'historique
    chat_history.append(HumanMessage(content=question))
    chat_history.append(AIMessage(content=reponse))

    # Garder seulement les 10 derniers messages
    if len(chat_history) > 10:
        chat_history = chat_history[-10:]

    # Extraire les sources
    sources = []
    for doc in docs:
        sources.append({
            "source": doc.metadata.get("source", "Document inconnu"),
            "page": doc.metadata.get("page", "?"),
            "extrait": doc.page_content[:300]
        })

    return reponse, sources