import streamlit as st
import utils.ali_express as ali_express
pages = {
    "Tools": [
        st.Page("tools/dashboard.py", title="Dashboard"),
        st.Page("tools/products.py", title="Products"),
        st.Page("tools/chat_app.py", title="Chat"),
    ]
}


pg = st.navigation(pages)
pg.run()
