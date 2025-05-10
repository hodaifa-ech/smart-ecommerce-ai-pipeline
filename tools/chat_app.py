import streamlit as st
import utils.chat as chat
import utils.ali_express as ali_express

st.set_page_config(page_title="Chatbot App", page_icon="💬")
st.title("💬 Chatbot Assistant")



with st.sidebar:
    st.sidebar.markdown("## New Data ?")
    if st.button("Scrap new data"):
        with st.spinner("Scraping top selling items from AliExpress..."):
            ali_express.scrape_aliexpress_top_selling()
        st.success("Scraping completed!")
    st.sidebar.markdown("---")





# Chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Type your message...")

if user_input:
    # Show user's message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get model response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chat.completion(st.session_state.messages)
            st.markdown(response)

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
