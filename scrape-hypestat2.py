import streamlit as st
from urllib.parse import urlparse
import pandas as pd
import requests
from bs4 import BeautifulSoup
from streamlit_option_menu import option_menu
import io
import time

from tqdm import tqdm
import types
import torch

# Prevent Streamlit from scanning torch.classes
if isinstance(torch.classes, types.ModuleType):
    torch.classes.__path__ = []
## ONLINE STREAMLIT DEPENDENCIES ###

# Read media database
# URL='https://docs.google.com/spreadsheets/d/e/2PACX-1vQwxy1jmenWfyv49wzEwrp3gYE__u5JdhvVjn1c0zMUxDL6DTaU_t4Yo03qRlS4JaJWE3nK9_dIQMYZ/pub?output=csv'.format()
# media_db=pd.read_csv(URL).fillna(0)

# ================================
# FUNCTION ZONE
# ================================

# Download article & analyze sentiment
def scrape_hypestat(website_url):
    hypestat_url = f"https://hypestat.com/info/{website_url}"
    try:
        response = requests.get(hypestat_url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        soup = BeautifulSoup(response.content, 'html.parser')

        # Get unique visitor
        dailyvisitor_element = soup.select_one('#traffic > dl:nth-child(4) > dd:nth-child(2)')
        dailyvisitor = dailyvisitor_element.text.strip() if dailyvisitor_element else None

        # Get page view
        dailyview_element = soup.select_one('#traffic > dl:nth-child(4) > dd:nth-child(8)')
        dailyview = dailyview_element.text.strip() if dailyview_element else None

        # Get monthly unique visitor semrush
        monthlyvisitsem_element = soup.select_one('#traffic > dl:nth-child(7) > dd:nth-child(10)')
        monthlyvisitsem = monthlyvisitsem_element.text.strip() if monthlyvisitsem_element else None

        return {
            'Website': website_url,
            'Est. Reach': dailyvisitor,
            'Est. Impressions': dailyview,
            'Monthly Unique Visitors': monthlyvisitsem,
            'Status': "OK"  # Add status to the result
        }

    except Exception as e:
        err_msg = str(e)
        print(f"❌ Failed processing {website_url}: {err_msg}")
        return {
            'Website': website_url,
            'Est. Reach': None,
            'Est. Impressions': None,
            'Monthly Unique Visitors': None,
            'Status': f"ERROR: {err_msg[:80]}"  # Add error status
        }

# ================================
# STREAMLIT UI
# ================================
st.set_page_config(page_title="Burson Hypestat Scraper", layout="centered")

# Sidebar Navigation
with st.sidebar:
    menu = option_menu(
        menu_title="Main Menu",
        options=["How to use", "Hypestat Scraper", "About"],
        icons=["question-circle-fill", "search", "diagram-3"],
        menu_icon="cast",  # optional
        default_index=1,  # optional
        styles={
            "icon": {"color": "orange"},
            "nav-link": {
                "--hover-color": "#eee",
            },
            "nav-link-selected": {"background-color": "green"},
        },
    )

# NEW: Separate NLP Processor
if menu == "Hypestat Scraper":
    st.title("Hypestat Scraper")
    st.markdown("Pilih metode input dan isi dengan URL website media yang diinginkan. Contoh: 'google.com'")
    st.markdown(  "Apabila menggunakan metode input excel, harap pastikan ada kolom dengan nama 'Link'") 

    with st.container(border=True):
        input_method = st.radio(
            "Select Input Method:",
            options=["Excel File", "Text Input"],
            horizontal=True
        )

        df = None  # Initialize df to None

        if input_method == "Excel File":
            uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

            if uploaded_file is not None:
                try:
                    df = pd.read_excel(uploaded_file)
                    with st.expander("📂 Preview File", expanded=False):
                        st.write(df.head())
                    if 'Link' not in df.columns:
                        st.error("❌ 'Link' column not found in the Excel file.")
                        df = None  # Set df to None if 'Link' column is missing
                except Exception as e:
                    st.error(f"❌ Error loading file: {e}")
                    df = None
        else:  # input_method == "Text Input"
            url_input = st.text_area("Enter website URLs (one per line):", height=200)
            if url_input:
                website_urls = [url.strip() for url in url_input.splitlines() if url.strip()]
                df = pd.DataFrame({'Link': website_urls})  # Create DataFrame from text input
            else:
                df = None

        st.divider()

        run_scraper = False
        if df is not None:
            run_scraper = st.button("Jalankan")

    # Process and display results if button was clicked
    if df is not None and run_scraper:
        # Ensure 'Link' column exists, even if created from text input
        if 'Link' not in df.columns:
            st.error("❌ 'Link' column is required. Please provide URLs with a 'Link' column (Excel) or in the text input.")
        else:
            # Scrape data for each URL
            results = []
            progress_bar = st.progress(0)
            total_sites = len(df)
            error_count = 0  # Initialize error count

            for i, row in df.iterrows():
                website_url = row['Link']
                progress_percent = (i + 1) / total_sites
                progress_bar.progress(progress_percent)
                result = scrape_hypestat(website_url)
                results.append(result)
                if result['Status'].startswith("ERROR"):
                    error_count += 1
                time.sleep(2)  # Be polite!

            # Create a DataFrame from the results
            results_df = pd.DataFrame(results)

            # Display the DataFrame
            st.dataframe(results_df)

            # Clear the progress bar
            progress_bar.empty()

            # Display success/warning message
            if error_count > 0:
                st.warning(f"⚠️ Scraping selesai. {error_count} dari {total_sites} media gagal diproses.")
            else:
                st.success("✅ Scraping selesai tanpa kesalahan.")

            # Provide a download button
            to_download = io.BytesIO()
            results_df.to_excel(to_download, index=False)
            to_download.seek(0)

            st.download_button(
                "📥 Download Excel",
                data=to_download,
                file_name="hypestat_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

elif menu == "How to use":
    st.title("📖 How to Use")
    st.markdown("""
    ### Petunjuk Penggunaan

    1. Pilih metode input:
    *   **Excel File:** Upload file Excel yang berisi link-link media yang ingin diambil statnya. Pastikan ada kolom bernama 'Link'.
    *   **Text Input:** Masukkan link-link media yang ingin diambil statnya, satu link per baris.
    2. Klik **Jalankan**, tunggu hingga proses selesai.
    3. Jika berhasil, hasil scraping bisa langsung diunduh dalam format **Excel**.
    """)

elif menu == "About":
    st.title("ℹ️ About")
    st.markdown("""
    ### Burson Hypestat Scraper v0.0.1

    **Release Note:**
    - ✅ Basic scraping untuk data Hypestat

    **Made by**: Jay and Naomi ✨
    """)