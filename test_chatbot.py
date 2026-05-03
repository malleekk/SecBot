from ingest import charger_base
from chatbot import creer_secbot, poser_question

print("🛡️  Démarrage de SecBot...")

db = charger_base()
secbot = creer_secbot(db)

print("✅ SecBot prêt ! Tapez 'quit' pour quitter.\n")

while True:
    question = input("Vous : ")

    if question.lower() == "quit":
        break

    reponse, sources = poser_question(secbot, question)

    print(f"\n🤖 SecBot : {reponse}")

    if sources:
        print("\n📎 Sources :")
        for s in sources:
            print(f"   - {s['source']} (page {s['page']})")

    print("\n" + "─"*50 + "\n")