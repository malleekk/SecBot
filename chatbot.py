import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import tool

load_dotenv()

# Variable globale temporaire pour stocker les sources récupérées par l'outil RAG
LATEST_SOURCES = []

def formater_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# ------------------------------------------------------------------
# LES OUTILS DE L'AGENT (Comme dans le TP du prof)
# ------------------------------------------------------------------

def configurer_outils(db):
    """Crée les outils en leur donnant accès à la base de données vectorielle."""
    
    @tool
    def chercher_dans_owasp(question_securite: str) -> str:
        """Cherche des informations et des guides de protection dans la documentation officielle de l'OWASP Top 10."""
        global LATEST_SOURCES
        LATEST_SOURCES = [] # Réinitialiser
        
        # On utilise le retriever de FAISS caché dans cet outil
        retriever = db.as_retriever(search_kwargs={"k": 3})
        docs = retriever.invoke(question_securite)
        
        # On garde de côté les sources pour Streamlit
        for doc in docs:
            LATEST_SOURCES.append({
                "source": doc.metadata.get("source", "OWASP Doc"),
                "page": doc.metadata.get("page", "?"),
                "extrait": doc.page_content[:300]
            })
            
        return formater_docs(docs)

    @tool
    def calculer_score_risque_cvss(impact: float, exploitabilite: float) -> str:
        """Calcule un score de risque simplifié (CVSS) entre 0.0 et 10.0 à partir de l'impact et de l'exploitabilité."""
        try:
            if not (0 <= impact <= 5) or not (0 <= exploitabilite <= 5):
                return "Erreur : L'impact et l'exploitabilité doivent être des notes entre 0 et 5."
            
            # Formule factice et ultra-simple pour le TP
            score = (impact + exploitabilite) * 1.0
            score = min(score, 10.0)
            
            if score >= 9.0: niveau = "CRITIQUE 🔴"
            elif score >= 7.0: niveau = "ÉLEVÉ 🟠"
            elif score >= 4.0: niveau = "MOYEN 🟡"
            else: niveau = "FAIBLE 🟢"
            
            return f"Score de risque calculé : {score:.1f}/10.0 (Niveau : {niveau})"
        except Exception as e:
            return f"Erreur de calcul : {e}"

    # Liste des outils
    TOOLS = [chercher_dans_owasp, calculer_score_risque_cvss]
    TOOLS_BY_NAME = {tool_.name: tool_ for tool_ in TOOLS}
    
    return TOOLS, TOOLS_BY_NAME


# ------------------------------------------------------------------
# LOGIQUE DE L'AGENT
# ------------------------------------------------------------------

def creer_secbot(db):
    """Initialise l'agent avec ses outils configurés."""
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
    )
    
    tools, tools_by_name = configurer_outils(db)
    llm_with_tools = llm.bind_tools(tools)
    
    return {
        "llm_with_tools": llm_with_tools,
        "tools_by_name": tools_by_name
    }


def poser_question(chatbot, question, st_chat_history):
    global LATEST_SOURCES
    LATEST_SOURCES = [] # Reset au début de la question
    
    # 1. Reconstruire l'historique pour LangChain
    messages = [
        SystemMessage(content="""Tu es SecBot, un assistant agentique expert en cybersécurité.
Tu possèdes des outils pour chercher dans la documentation OWASP et pour calculer des scores de risques.

RÈGLES STRICTES :
1. Si l'utilisateur pose une question théorique sur une faille, utilise TOUJOURS l'outil 'chercher_dans_les_notes_owasp'.
2. S'il te donne des notes d'impact, utilise l'outil de calcul.
3. Structure TOUJOURS ta réponse finale ainsi :
   📌 Définition : ...
   ⚠️ Risque : ...
   🛡️ Protection : ...
   💡 Exemple : ...
4. Réponds toujours en français.""")
    ]
    
    for msg in st_chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
            
    # Ajouter la nouvelle question
    messages.append(HumanMessage(content=question))
    
    # 2. Premier appel au LLM pour décider de l'action (Tool Calling)
    first_response = chatbot["llm_with_tools"].invoke(messages)
    messages.append(first_response)
    
    # 3. Si le LLM veut utiliser un outil (comme dans le TP du prof)
    if first_response.tool_calls:
        for tool_call in first_response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Exécuter l'outil sélectionné par l'IA
            selected_tool = chatbot["tools_by_name"][tool_name]
            tool_output = selected_tool.invoke(tool_args)
            
            messages.append(
                ToolMessage(content=tool_output, tool_call_id=tool_call["id"])
            )
            
        # Deuxième appel pour générer la réponse finale avec le résultat de l'outil
        final_response = chatbot["llm_with_tools"].invoke(messages)
        return final_response.content, LATEST_SOURCES
        
    return first_response.content, LATEST_SOURCES