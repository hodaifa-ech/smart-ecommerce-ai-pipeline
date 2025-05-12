import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import subprocess # <-- Import subprocess
import sys        # <-- Import sys to get python executable

# --- Page Configuration ---
st.set_page_config(
    page_title="Shopify Product Analysis Dashboard",
    page_icon="📊",
    layout="wide" # Use wide layout for more space
)

# --- Constants ---
CSV_FILENAME = "utils/products_data.csv" # Assumes CSV is in the root directory relative to where streamlit is run
# More robust path handling might be needed depending on execution context
# For example, if running from the root project dir:
# CSV_FILENAME = os.path.join(os.path.dirname(__file__), "..", "products_data.csv")
# Or ensure the fetch script always saves to the root. Let's assume root for now.


# --- Helper Functions ---
@st.cache_data # Cache the data loading to improve performance
def load_data(filename):
    """Loads data from the CSV file."""
    absolute_csv_path = os.path.abspath(filename) # Get absolute path for clarity
    if not os.path.exists(absolute_csv_path):
        st.error(f"Error: Data file not found at expected location: {absolute_csv_path}. Please run the scraper first.")
        return None
    try:
        df = pd.read_csv(absolute_csv_path) # Load using absolute path
        # --- Basic Data Cleaning & Type Conversion ---
        # Convert price columns to numeric, coercing errors to NaN
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['compare_at_price'] = pd.to_numeric(df['compare_at_price'], errors='coerce')

        # Convert relevant columns to datetime objects
        for col in ['created_at', 'updated_at', 'published_at', 'variant_created_at', 'variant_updated_at']:
             if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce') # Coerce errors if format is inconsistent

        # Ensure 'available' is boolean (handle potential string representations)
        if 'available' in df.columns:
             df['available'] = df['available'].apply(lambda x: True if str(x).lower() == 'true' else (False if str(x).lower() == 'false' else None))
             df['available'] = df['available'].astype('boolean') # Use pandas nullable boolean type

        # Handle potential missing values in key categorical columns
        for col in ['vendor', 'product_type', 'store_domain']:
            if col in df.columns:
                df[col].fillna('Unknown', inplace=True)

        return df
    except pd.errors.EmptyDataError:
        st.error(f"Error: {absolute_csv_path} is empty. Please ensure the fetch script ran successfully and generated data.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading or processing the CSV ({absolute_csv_path}): {e}")
        return None

# --- Function to run the scraper script ---
def run_scraper(script_path):
    """Runs the external Python script using subprocess."""
    absolute_script_path = os.path.abspath(script_path)
    script_dir = os.path.dirname(absolute_script_path) # Get directory of the script

    st.info(f"Attempting to run scraper: {absolute_script_path}")
    if not os.path.exists(absolute_script_path):
         st.error(f"Scraper script not found at: {absolute_script_path}")
         return False

    try:
        # Run the script using the same Python interpreter that runs Streamlit
        # Run it with the script's directory as the current working directory
        # This helps if the script uses relative paths for its own operations (like logging)
        process = subprocess.run(
            [sys.executable, absolute_script_path],
            capture_output=True,  # Capture stdout and stderr
            text=True,            # Decode output as text
            check=False,          # Don't raise exception on non-zero exit, check manually
            cwd=script_dir        # Set working directory
        )
        st.info("Scraper script execution finished.")

        # Display output/errors from the script in expanders for debugging
        with st.expander("Show Scraper Output (stdout)"):
            st.text(process.stdout if process.stdout else "No standard output.")
        if process.stderr:
             with st.expander("Show Scraper Errors (stderr)", expanded=True): # Expand if errors exist
                st.text(process.stderr)

        if process.returncode == 0:
            st.success("Data scraping completed successfully!")
            return True
        else:
            st.error(f"Data scraping script failed with exit code {process.returncode}. Check errors above.")
            return False
    except Exception as e:
        st.error(f"An error occurred while trying to run the scraper process: {e}")
        return False

# --- Main Application ---
st.title("📊 Shopify Product Data Dashboard")
st.markdown("Analyze product data fetched from various Shopify stores via their `/products.json` endpoints.")


# --- Sidebar ---
st.sidebar.header("Actions")

# --- Button to trigger scraping ---
# Construct the path to the scraper script relative to *this* dashboard script
# dashboard.py is in tools/, fetch_shopify_product_data.py is in utils/
# So we need to go up one level from tools/ and then down into utils/
dashboard_dir = os.path.dirname(__file__)
scraper_script_path = os.path.join(dashboard_dir, "..", "utils", "fetch_shopify_product_data.py")

if st.sidebar.button("🔄 Scrape New Shopify Data"):
    # Use a spinner to indicate activity
    with st.spinner(f"Running Shopify data scraper... Please wait. This might take a while."):
        success = run_scraper(scraper_script_path)
        if success:
            # IMPORTANT: Clear the cache so load_data runs again
            st.cache_data.clear()
            st.success("Cache cleared. Rerunning the app to load fresh data...")
            # Rerun the app immediately to reflect the newly scraped data
            st.experimental_rerun()
        else:
            st.warning("Scraping process failed or encountered errors. Data might not be up-to-date.")

st.sidebar.markdown("---") # Separator before filters
st.sidebar.header("Filters")

# --- Load Data ---
# Load data *after* the button logic, so rerun works correctly
# Use the CSV_FILENAME constant (ensure it points correctly relative to execution dir or use absolute)
# Let's try resolving the path relative to the dashboard script's parent directory (project root)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
absolute_csv_path = os.path.join(project_root, CSV_FILENAME)
data = load_data(absolute_csv_path)


# --- Dashboard Content (Only if data loaded successfully) ---
if data is not None and not data.empty:

    # Filter data based on domain selection (using the already loaded 'data' DataFrame)
    all_domains = ['All'] + sorted(data['store_domain'].unique().tolist())
    selected_domain = st.sidebar.selectbox("Select Store Domain", all_domains)

    if selected_domain != 'All':
        filtered_data = data[data['store_domain'] == selected_domain].copy()
    else:
        filtered_data = data.copy()

    # --- Dynamic Filters based on current selection ---
    if not filtered_data.empty:
        # Filter by Vendor
        all_vendors = ['All'] + sorted(filtered_data['vendor'].unique().tolist())
        selected_vendor = st.sidebar.selectbox("Select Vendor", all_vendors)
        if selected_vendor != 'All':
            filtered_data = filtered_data[filtered_data['vendor'] == selected_vendor].copy()

        # Filter by Product Type
        all_product_types = ['All'] + sorted(filtered_data['product_type'].unique().tolist())
        selected_product_type = st.sidebar.selectbox("Select Product Type", all_product_types)
        if selected_product_type != 'All':
            filtered_data = filtered_data[filtered_data['product_type'] == selected_product_type].copy()

        # Filter by Price Range
        # Ensure price column exists and has valid numbers before calculating min/max
        if 'price' in filtered_data.columns and not filtered_data['price'].isnull().all():
            min_price_val = float(filtered_data['price'].min())
            max_price_val = float(filtered_data['price'].max())
            # Handle case where min and max are the same for the slider
            if min_price_val == max_price_val:
                max_price_val += 1.0
            # Set default range for slider
            default_price_range = (min_price_val, max_price_val)
        else:
             # Default values if price data is missing or invalid
             min_price_val = 0.0
             max_price_val = 1.0
             default_price_range = (0.0, 1.0)
             st.sidebar.warning("Price data missing or invalid for range slider.")


        price_range = st.sidebar.slider(
            "Select Price Range ($)",
            min_value=min_price_val,
            max_value=max_price_val,
            value=default_price_range, # Use calculated default range
            step=0.01
        )
        # Apply price filter only if price column exists
        if 'price' in filtered_data.columns:
            filtered_data = filtered_data[
                (filtered_data['price'] >= price_range[0]) &
                (filtered_data['price'] <= price_range[1])
            ].copy()


         # Filter by Availability
        if 'available' in filtered_data.columns:
            availability_options = {'All': None, 'Available': True, 'Unavailable': False}
            selected_availability_str = st.sidebar.radio(
                "Filter by Availability",
                options=list(availability_options.keys()),
                index=0 # Default to 'All'
            )
            selected_availability_bool = availability_options[selected_availability_str]
            if selected_availability_bool is not None:
                filtered_data = filtered_data[filtered_data['available'] == selected_availability_bool].copy()
        else:
            st.sidebar.warning("Availability data column not found.")

    else:
        st.sidebar.warning("No data matches the current domain filter.")


    # --- Main Dashboard Area (Only if filtered_data is not empty) ---
    if not filtered_data.empty:
        st.header("📈 Key Performance Indicators (KPIs)")
        st.markdown("Overview metrics for the selected data.")

        # --- Calculate KPIs (Safely handle potential missing columns/data) ---
        total_unique_products = filtered_data['product_id'].nunique() if 'product_id' in filtered_data else 0
        total_variants = len(filtered_data)

        available_variants = 0
        if 'available' in filtered_data.columns:
            # Ensure we handle potential Pandas <NA> boolean type correctly
             available_variants = filtered_data[filtered_data['available'].eq(True)].shape[0]

        unavailable_variants = total_variants - available_variants

        average_price = filtered_data['price'].mean() if 'price' in filtered_data.columns else None
        median_price = filtered_data['price'].median() if 'price' in filtered_data.columns else None

        num_vendors = filtered_data['vendor'].nunique() if 'vendor' in filtered_data else 0
        num_product_types = filtered_data['product_type'].nunique() if 'product_type' in filtered_data else 0

        # Display KPIs in columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Unique Products", f"{total_unique_products:,}")
            st.metric("Total Variants", f"{total_variants:,}")
        with col2:
            st.metric("Available Variants", f"{available_variants:,}")
            st.metric("Unavailable Variants", f"{unavailable_variants:,}")
        with col3:
            st.metric("Average Variant Price", f"${average_price:,.2f}" if pd.notna(average_price) else "N/A")
            st.metric("Median Variant Price", f"${median_price:,.2f}" if pd.notna(median_price) else "N/A")
        with col4:
            st.metric("Number of Vendors", f"{num_vendors:,}")
            st.metric("Number of Product Types", f"{num_product_types:,}")

        st.markdown("---") # Divider

        # --- Data Visualizations ---
        st.header("📊 Data Visualizations")
        st.markdown("Interactive charts exploring the product data.")

        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            # Price Distribution Histogram
            st.subheader("Variant Price Distribution")
            if 'price' in filtered_data.columns and not filtered_data['price'].isnull().all():
                fig_price_hist = px.histogram(
                    filtered_data.dropna(subset=['price']),
                    x="price",
                    nbins=50,
                    title="Distribution of Variant Prices",
                    labels={'price': 'Price ($)'},
                    color_discrete_sequence=px.colors.sequential.Viridis
                )
                fig_price_hist.update_layout(bargap=0.1)
                st.plotly_chart(fig_price_hist, use_container_width=True)
            else:
                st.warning("No valid price data available for the current selection to display distribution.")

            # Product Count per Vendor Bar Chart
            st.subheader("Product Count per Vendor")
            if 'vendor' in filtered_data.columns and 'product_id' in filtered_data.columns:
                vendor_product_counts = filtered_data.groupby('vendor')['product_id'].nunique().sort_values(ascending=False).reset_index()
                vendor_product_counts.columns = ['Vendor', 'Unique Product Count'] # Rename columns for clarity
                if not vendor_product_counts.empty:
                    top_n = 20
                    display_counts = vendor_product_counts.head(top_n)
                    if len(vendor_product_counts) > top_n:
                         st.caption(f"Showing Top {top_n} Vendors by Product Count")

                    fig_vendor_bar = px.bar(
                        display_counts, # Use the limited df for the plot
                        x="Vendor",
                        y="Unique Product Count",
                        title="Unique Products per Vendor",
                        labels={'Unique Product Count': 'Number of Unique Products'},
                        color='Vendor',
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_vendor_bar.update_layout(xaxis_tickangle=-45, showlegend=False)
                    st.plotly_chart(fig_vendor_bar, use_container_width=True)
                else:
                    st.warning("No vendor data available for the current selection.")
            else:
                 st.warning("Vendor or Product ID data missing for this chart.")


        with viz_col2:
             # Variant Availability Pie Chart
            st.subheader("Variant Availability")
            if 'available' in filtered_data.columns:
                availability_counts = filtered_data['available'].value_counts().reset_index()
                availability_counts.columns = ['Available', 'Count']
                # Map boolean/None to readable strings safely
                availability_counts['Available'] = availability_counts['Available'].apply(
                    lambda x: 'Available' if x is True else ('Unavailable' if x is False else 'Unknown')
                )


                if not availability_counts.empty:
                    fig_avail_pie = px.pie(
                        availability_counts,
                        names='Available',
                        values='Count',
                        title='Availability Status of Variants',
                        hole=0.3, # Make it a donut chart
                        color_discrete_map={'Available':'#2ca02c', 'Unavailable':'#d62728', 'Unknown':'#7f7f7f'}
                    )
                    fig_avail_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_avail_pie, use_container_width=True)
                else:
                    st.warning("No availability data available for the current selection.")
            else:
                st.warning("Availability data column not found for pie chart.")

            # Product Count per Type Bar Chart
            st.subheader("Product Count per Product Type")
            if 'product_type' in filtered_data.columns and 'product_id' in filtered_data.columns:
                type_product_counts = filtered_data.groupby('product_type')['product_id'].nunique().sort_values(ascending=False).reset_index()
                type_product_counts.columns = ['Product Type', 'Unique Product Count'] # Rename columns
                if not type_product_counts.empty:
                    top_n_type = 20
                    display_type_counts = type_product_counts.head(top_n_type)
                    if len(type_product_counts) > top_n_type:
                         st.caption(f"Showing Top {top_n_type} Product Types by Product Count")

                    fig_type_bar = px.bar(
                        display_type_counts, # Use the limited df
                        x="Product Type",
                        y="Unique Product Count",
                        title="Unique Products per Type",
                        labels={'Unique Product Count': 'Number of Unique Products'},
                        color='Product Type',
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_type_bar.update_layout(xaxis_tickangle=-45, showlegend=False)
                    st.plotly_chart(fig_type_bar, use_container_width=True)
                else:
                    st.warning("No product type data available for the current selection.")
            else:
                 st.warning("Product Type or Product ID data missing for this chart.")

        st.markdown("---")

        # --- Data Storytelling & Insights ---
        st.header("🔍 Data Storytelling & Insights")

        # Storytelling Example 1: Availability Issues
        if 'available' in filtered_data.columns and unavailable_variants > 0:
            percent_unavailable = (unavailable_variants / total_variants) * 100 if total_variants > 0 else 0
            st.subheader("Stock Availability Concerns")
            st.markdown(f"""
            Based on the current selection, **{unavailable_variants:,}** product variants ({percent_unavailable:.1f}%) are marked as **unavailable**.
            This could indicate potential stock issues or items that are intentionally not for sale.
            """)
            # List some unavailable products/variants
            unavailable_sample_cols = ['title', 'variant_title', 'vendor', 'store_domain']
            # Check if required columns exist before trying to display
            if all(col in filtered_data.columns for col in unavailable_sample_cols):
                 unavailable_sample = filtered_data[filtered_data['available'] == False][unavailable_sample_cols].drop_duplicates().head(10)
                 if not unavailable_sample.empty:
                     with st.expander("View Sample of Unavailable Variants"):
                         st.dataframe(unavailable_sample, use_container_width=True)
            else:
                 st.caption("Cannot display unavailable sample - one or more required columns (title, variant_title, vendor, store_domain) are missing.")


        # Storytelling Example 2: Price Analysis
        st.subheader("Price Point Analysis")
        if 'price' in filtered_data.columns and pd.notna(average_price):
            st.markdown(f"""
            The average price for a variant in the selected dataset is **${average_price:,.2f}**, with the median price at **${median_price:,.2f}**.
            The distribution chart above shows how prices are spread across the selection. Any significant peaks might indicate common price points.
            """)
            # Highlight most expensive items
            expensive_cols = ['title', 'vendor', 'price', 'store_domain']
            if all(col in filtered_data.columns for col in expensive_cols):
                most_expensive = filtered_data.sort_values('price', ascending=False).drop_duplicates(subset=['product_id']).head(5)
                if not most_expensive.empty:
                     with st.expander("Top 5 Most Expensive Products (based on highest variant price)"):
                        st.dataframe(most_expensive[expensive_cols], use_container_width=True)
            else:
                 st.caption("Cannot display most expensive products - required columns are missing.")
        else:
             st.markdown("Price analysis is limited due to missing or invalid price data in the current selection.")

        # Storytelling Example 3: Vendor Dominance (if applicable)
        if 'vendor' in filtered_data.columns and 'product_id' in filtered_data.columns and num_vendors > 1:
             vendor_counts = filtered_data.groupby('vendor')['product_id'].nunique().sort_values(ascending=False)
             if not vendor_counts.empty:
                top_vendor = vendor_counts.index[0]
                top_vendor_count = vendor_counts.iloc[0]
                total_prods_for_vendors = vendor_counts.sum()
                top_vendor_share = (top_vendor_count / total_prods_for_vendors) * 100 if total_prods_for_vendors > 0 else 0

                if top_vendor_share > 40: # Only highlight if one vendor is somewhat dominant
                    st.subheader("Vendor Focus")
                    st.markdown(f"""
                    The vendor **'{top_vendor}'** accounts for **{top_vendor_count:,}** unique products, representing approximately **{top_vendor_share:.1f}%** of the products
                    from known vendors in the current selection. This suggests a significant presence or a large catalog from this vendor compared to others in the filtered data.
                    """)


        st.markdown("---")

        # --- Raw Data Exploration ---
        st.header(" Raw Data")
        st.markdown("Explore the filtered data used for the analysis above.")
        with st.expander("Show Filtered Data Table"):
            # Show a limited number of columns by default for better readability
            default_columns_to_show = ['store_domain', 'vendor', 'title', 'product_type', 'variant_title', 'price', 'available', 'updated_at']
            # Filter to only columns that actually exist in the dataframe
            columns_to_show = [col for col in default_columns_to_show if col in filtered_data.columns]
            if columns_to_show:
                display_df = filtered_data[columns_to_show].copy()
                st.dataframe(display_df, use_container_width=True)
                st.caption(f"Displaying {len(filtered_data)} rows matching the current filters. Selected columns shown.")
            else:
                st.warning("No columns available to display in the raw data table.")


    elif data is not None: # Original data was loaded, but filtered result is empty
        st.warning("No data matches the selected filters. Try adjusting the filter criteria in the sidebar.")
    # else: Handled by the initial load_data check


else:
    # This message is shown if load_data returned None or empty DataFrame initially
    st.warning("Could not load or process product data. Please ensure the data file exists and contains valid data, or use the 'Scrape New Shopify Data' button.")

# Add footer or additional info if needed
st.sidebar.markdown("---")
st.sidebar.info("Dashboard developed to analyze Shopify product data.")