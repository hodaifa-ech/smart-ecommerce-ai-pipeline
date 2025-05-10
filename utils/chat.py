import os
from groq import Groq
import pandas as pd

filename = "aliexpress_multi_page_firefox.csv"  

df = pd.read_csv(filename)
# print(df)



def completion(user_query, data="aliexpress_multi_page_firefox.csv", model="llama-3.3-70b-versatile"): 


    SYSTEM_PROMPT = f"""
You are an intelligent eCommerce analytics assistant.

You have access to a structured product dataset scraped from AliExpress. Your goal is to help users make informed decisions by analyzing product trends, prices, ratings, and discounts. Use your reasoning and data understanding to generate helpful, concise, and actionable insights.

Respond as if you're talking to an eCommerce entrepreneur looking for guidance.

Dataset Preview:
{df.head(20).to_markdown(index=False)}

User Question:
{user_query}

Instructions:
- Use evidence from the dataset to support your insights.
- Mention product names, prices, discounts, and ratings where relevant.
- Recommend only if data supports it (don't hallucinate).
- Format output clearly using bullet points, tables, or markdown when appropriate.

Answer:
"""



    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""{SYSTEM_PROMPT}""",
            }
        ],
        model=model,
    )

    res = ""
    res = chat_completion.choices[0].message.content
    # print(res)

    return res 


# test = completion(df,"what the best product to sell nowadays, categorie clothing ")
# print(test)