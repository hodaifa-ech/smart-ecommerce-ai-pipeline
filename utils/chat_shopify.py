# utils/chat_shopify.py
import os
from groq import Groq
import pandas as pd
import re # For simple query parsing

# --- Configuration ---
FILENAME = "utils/products_data.csv"
# Ensure your GROQ_API_KEY is set in your environment variables
# e.g., export GROQ_API_KEY='your_actual_api_key'
# If you don't have it set, you can uncomment and fill the line below for quick testing
# os.environ['GROQ_API_KEY'] = "YOUR_GROQ_API_KEY_HERE" 
if not os.environ.get("GROQ_API_KEY"):
    print("Warning: GROQ_API_KEY environment variable not set. API calls will fail.")
    # exit() # You might want to exit if the key is essential for the app to run

# --- 1. Load Data (Knowledge Base) ---
df = pd.DataFrame() # Initialize df to prevent errors if loading fails
try:
    df = pd.read_csv(FILENAME)
    print(f"Successfully loaded {FILENAME} with {len(df)} rows.")
    print(f"Columns: {df.columns.tolist()}")
except FileNotFoundError:
    print(f"Error: The file {FILENAME} was not found. Please check the path.")
    # Don't exit here if the app might run without it, or handle it in the app
except pd.errors.EmptyDataError:
    print(f"Error: The file {FILENAME} is empty.")
except Exception as e:
    print(f"An error occurred while loading the CSV: {e}")

# --- 2. Retriever Function ---
def retrieve_relevant_products(dataframe, user_query, category=None, top_n=5):
    """
    Retrieves relevant products from the dataframe based on the user query and category.
    """
    if dataframe.empty:
        print("Warning: Product dataframe is empty. Cannot retrieve products.")
        return pd.DataFrame()

    # Columns to search for general keywords
    search_columns = ['title', 'tags', 'body_html', 'product_type', 'vendor']
    
    # Filter by category if provided
    filtered_df = dataframe.copy()
    if category:
        try:
            # Case-insensitive search for category within product_type
            # Ensure 'product_type' is string, handle NaN by replacing with empty string
            if 'product_type' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['product_type'].fillna('').astype(str).str.contains(category, case=False, na=False)
                ]
            else:
                 print(f"Warning: 'product_type' column not found for category filtering. Skipping category filter.")
        except KeyError: # Should be caught by 'in filtered_df.columns' but as a safeguard
            print(f"Warning: 'product_type' column not found for category filtering. Skipping category filter.")

    if filtered_df.empty and category:
        print(f"No products found for category: {category}")
        # Return empty df, let generate_rag_completion handle 'no products found' message
        return pd.DataFrame() 
    
    # Simple keyword extraction from the query
    # Removed 'clothing', 'category' as they are handled by category filter or are too generic
    common_words_to_exclude = [
        'what', 'is', 'the', 'a', 'to', 'for', 'best', 'sell', 'nowadays', 'show', 'me', 
        'products', 'product', 'some', 'good', 'from', 'preferably'
    ]
    query_words = [
        word.lower() for word in re.split(r'\W+', user_query) 
        if word.lower() not in common_words_to_exclude and len(word) > 2
    ]
    
    if not query_words:
        if not filtered_df.empty:
            print("No specific keywords to search for, returning based on category or general data.")
            return filtered_df.head(top_n)
        else:
            print("No specific keywords and no category match. Cannot retrieve relevant products.")
            return pd.DataFrame()

    # Create a relevance score
    filtered_df['relevance_score'] = 0
    
    for col in search_columns:
        if col in filtered_df.columns:
            # Ensure the column is string type before using .str methods
            # Fill NaN with empty string to prevent errors with .str.contains
            col_as_str = filtered_df[col].fillna('').astype(str)
            for word in query_words:
                filtered_df['relevance_score'] += col_as_str.str.contains(word, case=False, na=False).astype(int)

    # Sort by relevance and get top_n
    relevant_df = filtered_df.sort_values(by='relevance_score', ascending=False)
    
    # Only return rows with a score > 0
    # If query_words was not empty, we expect some score.
    # If query_words was empty, this condition won't filter out category-only matches returned earlier.
    if query_words: # Only apply score filter if we actually searched for keywords
        relevant_df = relevant_df[relevant_df['relevance_score'] > 0]

    relevant_df = relevant_df.head(top_n) # Apply top_n after score filtering

    if relevant_df.empty and not query_words and not filtered_df.empty: # fallback if only category was provided
        return filtered_df.head(top_n)
        
    return relevant_df.drop(columns=['relevance_score'], errors='ignore')


# --- 3. Augment & 4. Generate Function (using Groq) ---
def generate_rag_completion(user_query: str, product_df: pd.DataFrame, model="llama3-70b-8192", max_context_rows=5): # Reduced max_context_rows for conciseness
    """
    Retrieves context, builds a prompt, and gets completion from Groq.
    """
    if product_df.empty:
        print("Product data is empty. Cannot perform RAG.")
        return "I'm sorry, but I don't have any product data loaded to answer your question. Please try loading data first."

    # Simple category extraction (can be improved with NLP)
    # Looks for patterns like "in X", "for X", "category X", "type X"
    category_match = re.search(r"(?:in|for|category|type)\s+([a-zA-Z\s\-]+)(?:\s|$)", user_query, re.IGNORECASE)
    category = None
    cleaned_query = user_query # Start with the full query

    if category_match:
        category = category_match.group(1).strip()
        # Optional: Remove category phrase from query to avoid redundant search on these exact words by retriever
        # cleaned_query = user_query.replace(category_match.group(0), "").strip()
        # If cleaned_query becomes empty, revert to user_query to avoid issues
        # if not cleaned_query:
        #     cleaned_query = user_query
        print(f"Extracted category: {category} (from query: '{user_query}')")
    else:
        print(f"No category explicitly extracted from query: '{user_query}'")


    # Retrieve relevant products
    # Pass the original user_query to the retriever, as it has its own keyword extraction.
    # Or pass cleaned_query if you are confident in the category removal. Let's stick to user_query for now.
    retrieved_context_df = retrieve_relevant_products(product_df, user_query, category=category, top_n=max_context_rows)

    context_for_llm = ""
    if not retrieved_context_df.empty:
        display_columns = ['title', 'vendor', 'product_type', 'price', 'compare_at_price', 'available', 'tags'] 
        if 'variant_title' in retrieved_context_df.columns: display_columns.append('variant_title')
        if 'sku' in retrieved_context_df.columns: display_columns.append('sku')
        
        actual_display_columns = [col for col in display_columns if col in retrieved_context_df.columns]
        
        # Limit the length of long string columns like 'tags' or 'body_html' if included
        # For example, to show only first 100 chars of tags:
        # temp_df = retrieved_context_df[actual_display_columns].copy()
        # if 'tags' in temp_df.columns:
        #     temp_df['tags'] = temp_df['tags'].astype(str).str.slice(0, 100) + '...'
        # context_for_llm = "Here are some products from our dataset that seem relevant:\n\n"
        # context_for_llm += temp_df.to_markdown(index=False)

        context_for_llm = "Here are some products from our dataset that seem relevant to your query:\n\n"
        context_for_llm += retrieved_context_df[actual_display_columns].to_markdown(index=False)

    else:
        if category:
            context_for_llm = f"No specific products matching your query for category '{category}' were found in our dataset. I can still try to answer generally if appropriate, or you can try a broader query."
        else:
            context_for_llm = "No specific products matching your query were found in our dataset. Please try a broader query or check your spelling. I can still try to answer generally if appropriate."

    # --- Refined Prompting Strategy ---
    system_message_content = """You are an intelligent eCommerce analytics assistant.
Your goal is to help users make informed decisions by analyzing product trends, prices, availability, and other features based on the provided data.
Respond as if you're talking to an eCommerce entrepreneur looking for guidance.

ALWAYS use the provided product data snippets (if any) to answer the user's question.
If the provided data is insufficient or no relevant products are found, clearly state that.
Do NOT make up products or information not present in the provided snippets.
Format output clearly using bullet points or concise paragraphs.
Be helpful and conversational.
If no products are found, still try to be helpful based on the query if possible, but clearly state data limitations.
"""

    user_prompt_template = f"""
Context from product data:
{context_for_llm}

User Question:
{user_query}

Based *only* on the provided context above (and not any external knowledge), please answer the user's question.
If the context is empty or does not contain the answer, state that you cannot answer based on the provided information.
Answer:
"""

    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        if not client.api_key:
            return "Error: GROQ_API_KEY is not configured. Cannot contact the AI model."

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_message_content
                },
                {
                    "role": "user",
                    "content": user_prompt_template,
                }
            ],
            model=model,
            temperature=0.2 # Lower temperature for more factual, less creative answers
        )
        res = chat_completion.choices[0].message.content
        return res
    except Exception as e:
        return f"Error communicating with Groq API: {e}"

# --- Test the RAG system ---
if __name__ == "__main__":
    if 'df' in globals() and not df.empty:
        print("\n--- RAG System Test ---")
        
        test_queries = [
            "what are some good t-shirts to sell from Allbirds, preferably merino?",
            "show me some womens apparel",
            "are there any smartwatches with advanced sleep tracking?",
            "what the best product to sell nowadays, categorie clothing",
            "any recommendations for summer dresses?",
            "Tell me about products in the 'Shoes' category",
            "what is the price of the 'Example Product Title'?" # Add a known product title if you have one
        ]

        for i, query in enumerate(test_queries):
            print(f"\n--- Test Query {i+1}: {query} ---")
            response = generate_rag_completion(query, df, model="llama3-8b-8192") # Using 8b for faster testing
            print("\nLLM Response:")
            print(response)
            print("-" * 30)
    else:
        print("DataFrame 'df' not loaded or is empty. Cannot run tests.")
        print("Please ensure 'utils/products_data.csv' exists and is not empty, and GROQ_API_KEY is set.")