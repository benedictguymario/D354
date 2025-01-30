# import streamlit as st
# import requests

# st.set_page_config(page_title="Athentification",page_icon=":lock:",layout="centered",initial_sidebar_state="expanded")
# st.title(':lock: Bienvenue sur la page d\'authentification')

# choix = st.radio("que voulez vous faire ?",["Se connecter","S'inscrire"])

# if choix == "Se connecter":
#     if st.button("Se connecter"):
#         st.success("connectez-vous")
#         st.markdown("<meta http-equiv='refresh' content='1;URL=http://localhost:8000'>",unsafe_allow_html=True)
# elif choix == "S'inscrire":
#     st.subheader(":pencil: Créer un compte")
#     with st.form("register"):
#         userEmail = st.text_input("mail de l'utilisateur")
#         password = st.text_input("Mot de passe", type="password")
#         submit = st.form_submit_button("S'inscrire")
#         if submit:
#             if userEmail and password:
#                 response = requests.post("http://localhost:5000/register", data={"userEmail": userEmail, "password": password})
#                 if response.status_code == 303:
#                     st.success("Inscription réussie ! Vous pouvez maintenant vous connecter.")
#                     st.markdown("<meta http-equiv='refresh' content='1;URL=http://localhost:8000'>",unsafe_allow_html=True)
#                 else:
#                     st.error("utilisateur exist deja, essayez un autre.")
#             else:
#                 st.warning(" Veuillez remplir tous les champs")


import streamlit as st
import requests

st.set_page_config(page_title="Authentification", page_icon=":lock:", layout="centered")

st.title(':lock: Bienvenue sur la page d\'authentification')

choix = st.radio("Que voulez-vous faire ?", ["Se connecter", "S'inscrire"])

if choix == "Se connecter":
    if st.button("Se connecter"):
        st.success("Connectez-vous")
        st.markdown("<meta http-equiv='refresh' content='1;URL=http://localhost:8000'>", unsafe_allow_html=True)

elif choix == "S'inscrire":
    st.subheader(":pencil: Créer un compte")
    with st.form("register"):
        userEmail = st.text_input("Mail de l'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("S'inscrire")

        if submit:
            if userEmail and password:
                response = requests.post("http://localhost:5000/register", data={"userEmail": userEmail, "password": password})

                if response.status_code == 201:  # Inscription réussie
                    st.success("Inscription réussie ! Vous allez être redirigé...")
                    st.markdown("<meta http-equiv='refresh' content='2;URL=http://localhost:8000'>", unsafe_allow_html=True)
                elif response.status_code == 400:  # Utilisateur déjà existant
                    st.error("L'utilisateur existe déjà, essayez un autre email.")
                else:
                    st.error("Une erreur est survenue lors de l'inscription.")
            else:
                st.warning("Veuillez remplir tous les champs.")

