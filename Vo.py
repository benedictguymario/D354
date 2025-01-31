from typing import Literal
import chainlit as cl
from langchain.vectorstores import Chroma
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
from dotenv import load_dotenv 
load_dotenv()
from typing import Optional
import sqlite3
port = int(os.getenv("PORT", 8000))

conn = sqlite3.connect("users.db")
cursor = conn.cursor()


# Configuration de l'API GenAI
API_KEY = os.getenv("GENAI_API_KEY")
genai.configure(api_key=API_KEY)
## foction de achage
# cursor.execute(
#     """
#     CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         userEmail TEXT UNIQUE NOT NULL,
#         password TEXT NOT NULL
#     )
#     """
# )
# conn.commit()
# conn.close()


# Modèle d'embedding
class SentenceTransformerEmbeddings:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        return self.model.encode(texts, convert_to_tensor=True).tolist()

    def embed_query(self, text):
        return self.model.encode(text, convert_to_tensor=True).tolist()


def Creat_prompt(question: str, reponse: str) -> str:
    prompt = f"""Utilisez les éléments de contexte suivants pour répondre à la question de l'utilisateur avec clarter un plus de detaille comme un expert  et formatez votre réponse **en Markdown**. 
si tu constate que la question est dans une autre langue autre que le français, veuillez répondre dans cette langue.
Si les informations du contexte ne permettent pas de répondre de manière précise, vous pouvez fournir une réponse générale ou suggérer des pistes de réflexion en lien avec le sujet.
Mais signaler clairement que la réponse est générale ou incertaine. 

Contexte : {reponse}
Question : {question}

Si la réponse à la question est insuffisante ou absente, suggérez à l'utilisateur des questions liées, comme :
- « Souhaitez-vous en savoir plus sur un autre sujet ? »
- « Peut-être pouvez-vous poser une question plus précise sur ce sujet ? »
- si vous avez des questions sur un autre sujet, n'hésitez pas à les poser.
NB: si la reponse de l'utilisateur est a ta question est une affirmation alos tu peux developper la reponse en donnant plus de detaille.

Ne renvoyez que la réponse utile ci-dessous et rien d'autre.
Réponse utile : 
"""          
    return prompt


# def decoupe(text, chunk_size=5):
#     words = text.split()
#     return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)] 

# Chargement de la base de données
def Obtenir_db(chroma_db_path, fonc_embed):
    try:
        db = Chroma(persist_directory=chroma_db_path, embedding_function=fonc_embed)
    except Exception as e:
        return None, f"Erreur : Impossible d'accéder à la collection. Détail : {str(e)}"
    return db, None


# Recherche de contexte dans la base
def Obtenir_contexte(db, question, fonc_embed, k=1):
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
    return contexte,sources


# Génération de réponse
def Reponse(chatbot, sources, prompt):
    try:
        response = chatbot.generate_content(prompt)
        final_response = response.text
    except Exception as e:
        return f"Erreur lors de la génération de la réponse : {str(e)}"
    if sources:
        final_response += f"\n\nSources : {', '.join(sources)}"
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
    await cl.Message(
            "salut je suis Ecofin.\n Un assistant  qui vous aides prendre connaissance des articles sur le site *Ecofine*.\n De quel article allons parler aujourd'hui ?"
        ).send()


@cl.on_message
async def on_message(message: str):
    db = cl.user_session.get("db")
    fonc_embed = cl.user_session.get("fonc_embed")
    if not db or not fonc_embed:
        await cl.Message(content="Erreur : Base de données non disponible.").send()
        return
    
    question = message.content

    contexte,source= Obtenir_contexte(db, question, fonc_embed)
    prompt = Creat_prompt(question, contexte)
    response = Reponse(genai.GenerativeModel("gemini-2.0-flash-exp"),source, prompt)
    await cl.Message(content=response).send()
    res = await cl.AskActionMessage(
        content="Etes vous satisfait de la reponse ?",
        actions=[
            cl.Action(name="Merci pour votre remarque", payload={"value": "continue"}, label="✅ OUI"),
            cl.Action(name="Desole prochainement je essayer de faire mieux", payload={"value": "cancel"}, label="❌ NON"),
        ],
    ).send()

    if res and res.get("payload").get("value") == "continue":
        await cl.Message(
            content="Merci pour votre remarque",
        ).send()
    else:
        await cl.Message(
            content="Desole prochainement je essayer de faire mieux",
        ).send()

def verifier_user(userEmail: str, password: str) -> Optional[cl.User]:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE userEmail = ? AND password = ?", (userEmail, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return cl.User(identifier=userEmail, metadata={"role": "user", "provider": "database"})
    return None


@cl.password_auth_callback
async def auth_callback(userEmail: str, password: str) -> Optional[cl.User]:
    
    return verifier_user(userEmail, password)
if __name__ =='__main__':
    cl.run()













