from typing import Literal
import asyncio
import chainlit as cl
from langchain.vectorstores import Chroma
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
from langchain.schema import Document
from dotenv import load_dotenv 
load_dotenv()

GENAI_API_KEY="AIzaSyAoAiS83AwyF7RhlRdWxzneByP-FLnJydA" 
# Détection du changement de sujet
def detect_changement(anc_question, nouv_question):
    encient_motcle = anc_question.split()
    nouveau_motcle = nouv_question.split()

    mot_unique_anc = set([mot.lower() for mot in encient_motcle[0].page_content.split()])
    mot_unique_nouv = set([mot.lower() for mot in nouveau_motcle[0].page_content.split()])

    mot_commun = mot_unique_anc & mot_unique_nouv
    return len(mot_commun) == 0

# Configuration de l'API GenAI
API_KEY = os.getenv("GENAI_API_KEY",GENAI_API_KEY)
genai.configure(api_key=API_KEY)

def decoupe(text, chunk_size=5):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]


# Modèle d'embedding
class SentenceTransformerEmbeddings:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        return self.model.encode(texts, convert_to_tensor=True).tolist()

    def embed_query(self, text):
        return self.model.encode(text, convert_to_tensor=True).tolist()


# Fonction pour créer un prompt
def Creat_prompt(question: str, reponse: str) -> str:
    prompt = f"""Utilisez les éléments de contexte suivants pour répondre à la question de l'utilisateur avec clarter un plus de detaille comme un expert  et formatez votre réponse **en Markdown**². 
si tu constate que la question est dans une autre langue autre que le français, veuillez répondre dans cette langue.
Si les informations du contexte ne permettent pas de répondre de manière précise, vous pouvez fournir une réponse générale ou suggérer des pistes de réflexion en lien avec le sujet.
Mais signaler clairement que la réponse est générale ou incertaine.  

Contexte : {reponse}
Question : {question}

Si la réponse à la question est insuffisante ou absente, suggérez à l'utilisateur des questions liées, comme :
- « Souhaitez-vous en savoir plus sur un autre sujet ? »
- « Peut-être pouvez-vous poser une question plus précise sur ce sujet ? »

Ne renvoyez que la réponse utile ci-dessous et rien d'autre.
Réponse utile : 
"""          
    return prompt 


# Chargement de la base de données
def Obtenir_db(chroma_db_path, fonc_embed):
    try:
        db = Chroma(persist_directory=chroma_db_path, embedding_function=fonc_embed)
    except Exception as e:
        return None, f"Erreur : Impossible d'accéder à la collection. Détail : {str(e)}"
    return db, None


# Recherche de contexte dans la base
def Obtenir_contexte(db, question, fonc_embed, k=2):
    try:
        query_embedding = fonc_embed.embed_query(question)
        results = db.similarity_search_by_vector(query_embedding, k=k)
        if not results:
            return "Aucun contexte trouvé.", []
        docs = [result.page_content for result in results]
        sources = [result.metadata.get('source', 'Inconnu') for result in results]
        contexte = "\n".join(docs)
    except Exception as e:
        return f"Erreur lors de la récupération du contexte : {str(e)}", []
    return contexte, sources


# Génération de réponse
def Reponse(chatbot, sources, prompt):
    try:
        response = chatbot.generate_content(prompt)
        final_response = response.text
    except Exception as e:
        return f"Erreur lors de la génération de la réponse : {str(e)}"
    
    return final_response


# Gestionnaire d'événements Chainlit
@cl.on_chat_start
async def chat_start():
    fonc_embed = SentenceTransformerEmbeddings()
    db, error = Obtenir_db("Chromadb", fonc_embed)
    if error:
        await cl.Message(content=f"Erreur lors du chargement de la base de données : {error}").send()
        return
    cl.user_session.set("db", db)
    cl.user_session.set("fonc_embed", fonc_embed)
    cl.user_session.set("chat_history", [])

    
    await cl.Message(content="Bonjour !je suis un assistant virtuel prêt à répondre aux questions sur les articles de ECOFIN  .").send()


# Fonction de gestion de la conversation
@cl.on_message
async def on_message(message: str):
    db = cl.user_session.get("db")
    fonc_embed = cl.user_session.get("fonc_embed")
    chat_history = cl.user_session.get("chat_history")
    
    if not db or not fonc_embed:
        await cl.Message(content="Erreur : Base de données non disponible.").send()
        return

    question = message.content

    # Vérifier le changement de sujet
    if chat_history:
        anc_question = chat_history[-1]["content"]
        if detect_changement(anc_question, question):
            context, sources = Obtenir_contexte(db, question, fonc_embed)
        else:
            context, sources = Obtenir_contexte(db, anc_question, fonc_embed)
    else:
        context, sources = Obtenir_contexte(db, question, fonc_embed)

    prompt = Creat_prompt(question, context)
    chatbot = genai.GenerativeModel("gemini-2.0-flash-exp")
    reponse = Reponse(chatbot, sources, prompt)

    # Sauvegarder l'historique des messages
    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": reponse})

    # Mettre à jour l'historique dans la session
    cl.user_session.set("chat_history", chat_history)

    # Créer un message système pour indiquer que la réponse va être envoyée
    system_message = {
        "role": "system",
        "content": "Le système a généré une réponse à la question de l'utilisateur."
    }
    
    # Diviser la réponse en morceaux pour un affichage fluide
    chunks = decoupe(reponse, chunk_size=5)
    response_message = cl.Message(content="")
    await response_message.send()

    # Envoyer chaque chunk avec un délai
    for chunk in chunks:
        response_message.content += f" {chunk}"
        await response_message.update()
        await asyncio.sleep(0.02)  # Pause de 20 ms entre les chunks

    try:
        # Ajouter les sources à la fin
        response_message.content += f"\n\n---\n**Sources :** {', '.join(sources) if sources else 'Aucune source disponible.'}"
        await response_message.update()
    except Exception as e:
        await cl.Message(content=f"Erreur : {str(e)}").send()

