# tools/chat_shopify_app.py
import os 
import streamlit as st
import utils.chat_shopify as chat # This will load chat.df
import utils.ali_express as ali_express # Assuming this file exists and function is defined

st.set_page_config(page_title="Application Chatbot", page_icon="💬")
st.title("💬 Assistant Chatbot pour Shopify Insights") # MODIFIED for clarity



def initialize_or_reset_chat(custom_greeting=None):
    """Initializes or resets the chat messages in session_state."""
    default_greeting = "Bonjour! Comment puis-je vous aider à analyser vos données produits aujourd'hui?"
    greeting = custom_greeting if custom_greeting else default_greeting
    st.session_state.messages = [{"role": "assistant", "content": greeting}]


initialize_or_reset_chat()


# --- Data Loading Check ---
# The df is loaded when utils.chat_shopify is imported
# We can add a check here to inform the user if data loading failed.
if chat.df.empty:
    st.error(
        "Le fichier de données produits (`utils/products_data.csv`) n'a pas pu être chargé ou est vide. "
        "Les fonctionnalités de RAG seront limitées ou indisponibles. "
        "Veuillez vérifier la console pour les messages d'erreur."
    )
    # Optionally, disable chat input if df is essential
    # chat_disabled = True
# else:
#    chat_disabled = False

# --- Sidebar ---
with st.sidebar:
    st.sidebar.markdown("## Nouvelles Données AliExpress?")
    if st.button("Lancer un nouveau scraping AliExpress"):
        if chat.df.empty: # Or some other logic if scraping populates chat.df
            st.warning("Attention: Le fichier CSV principal n'est pas chargé. Le scraping peut continuer mais les données ne seront pas immédiatement combinées.")
        with st.spinner("Scraping des articles les plus vendus sur AliExpress..."):
            try:
                # Assuming scrape_aliexpress_top_selling updates or creates products_data.csv
                # And we might need to reload chat.df after this
                ali_express.scrape_aliexpress_top_selling()
                st.success("Scraping terminé ! Veuillez recharger la page ou redémarrer l'application pour utiliser les nouvelles données.")
                # For a more dynamic update, you'd need to reload chat.df here
                # and potentially clear chat history or notify user to restart chat.
                # e.g. chat.df = pd.read_csv(chat.FILENAME) # simplified reload
            except Exception as e:
                st.error(f"Erreur durant le scraping : {e}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("Modèle LLM: `llama3-70b-8192` (via Groq)")
    st.sidebar.markdown(f"Produits chargés: {len(chat.df)} (depuis `{chat.FILENAME}`)")


# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Bonjour! Comment puis-je vous aider à analyser vos données produits aujourd'hui?"}]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Posez votre question sur les produits..." ) #, disabled=chat_disabled)

if user_input:
    # Show user's message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get model response
    with st.chat_message("assistant"):
        with st.spinner("Réflexion en cours..."):
            # CORE FIX: Pass user_input and the loaded dataframe (chat.df)
            if chat.df.empty:
                response = "Je ne peux pas répondre car les données produits ne sont pas chargées."
            elif not os.environ.get("GROQ_API_KEY"):
                 response = "La clé API GROQ n'est pas configurée. Je ne peux pas contacter le modèle IA."
            else:
                response = chat.generate_rag_completion(user_input, chat.df)
            
            st.markdown(response)

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})