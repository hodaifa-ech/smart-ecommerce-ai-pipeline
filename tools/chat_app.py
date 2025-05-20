import streamlit as st
import utils.chat as chat
import utils.ali_express as ali_express

st.set_page_config(page_title="Application Chatbot", page_icon="💬") # MODIFIED
st.title("💬 Assistant Chatbot") # MODIFIED

def initialize_or_reset_chat(custom_greeting=None):
    """Initializes or resets the chat messages in session_state."""
    default_greeting = "Bonjour! Comment puis-je vous aider à analyser vos données produits aujourd'hui?"
    greeting = custom_greeting if custom_greeting else default_greeting
    st.session_state.messages = [{"role": "assistant", "content": greeting}]


initialize_or_reset_chat()

with st.sidebar:
    st.sidebar.markdown("## Nouvelles Données ?") # MODIFIED
    if st.button("Lancer un nouveau scraping"): # MODIFIED
        with st.spinner("Scraping des articles les plus vendus sur AliExpress..."): # MODIFIED
            ali_express.scrape_aliexpress_top_selling()
        st.success("Scraping terminé !") # MODIFIED
    st.sidebar.markdown("---")





# Chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Tapez votre message...") # MODIFIED

if user_input:
    # Show user's message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get model response
    with st.chat_message("assistant"):
        with st.spinner("Réflexion en cours..."): # MODIFIED
            response = chat.completion(st.session_state.messages)
            st.markdown(response)

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})