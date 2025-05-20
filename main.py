import streamlit as st
import utils.ali_express as ali_express
pages = {
    "🔴 Ali-Express": [
        st.Page("tools/dashboard.py", title="Dashboard"),
        st.Page("tools/products.py", title="Products"),
        st.Page("tools/machine_learning.py", title="Classifier (attractivness)"),
        st.Page("tools/chat_app.py", title="Chat Bot"),
    ],
    "🟢 Shopify": [
        st.Page("tools/shopify.py", title="Dashboard"),
        st.Page("tools/chat_shopify_app.py", title="Chat Bot"),
    ]

}


pg = st.navigation(pages)
pg.run()
