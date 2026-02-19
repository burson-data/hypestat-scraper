import streamlit as st
from urllib.parse import urlparse
import pandas as pd
import requests
from bs4 import BeautifulSoup
from streamlit_option_menu import option_menu
import io
import time

# ================================
# FUNCTION ZONE
# ================================

def scrape_hypestat(website_url):
    hypestat_url = f"https://hypestat.com/info/{website_url}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

try:
    response = requests.get(hypestat_url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    dailyvisitor_element = soup.select_one('#traffic > dl:nth-child(4) > dd:nth-child(2)')
    dailyvisitor = dailyvisitor_element.text.strip() if dailyvisitor_element else "0"
    dailyvisitor = "0" if dailyvisitor.lower() == "n/a" else dailyvisitor

    dailyview_element = soup.select_one('#traffic > dl:nth-child(4) > dd:nth-child(8)')
    dailyview = dailyview_element.text.strip() if dailyview_element else "0"
    dailyview = "0" if dailyview.lower() == "n/a" else dailyview

    monthlyvisitsem_element = soup.select_one('#traffic > dl:nth-child(4) > dd:nth-child(4)')
    monthlyvisitsem = monthlyvisitsem_element.text.strip() if monthlyvisitsem_element else "0"
    monthlyvisitsem = "0" if monthlyvisitsem.lower() == "n/a" else monthlyvisitsem

    return {
        'Website': website_url,
        'Est. Reach': dailyvisitor,
        'Est. Impressions': dailyview,
        'Monthly Visitors': monthlyvisitsem,
        'Status': "OK"
    }

except Exception as e:
    err_msg = str(e)
    print(f"Failed processing {website_url}: {err_msg}")
    return {
        'Website': website_url,
        'Est. Reach': None,
        'Est. Impressions': None,
        'Monthly Visitors': None,
        'Status': f"ERROR: {err_msg[:80]}"
    }

st.set_page_config(page_title="Burson Hypestat Scraper", layout="centered")

with st.sidebar:
    menu = option_menu(
    menu_title="Main Menu",
    options=["How to use", "Hypestat Scraper", "About"],
    icons=["question-circle-fill", "search", "diagram-3"],
    menu_icon="cast",
    default_index=1,
    styles={
        "icon": {"color": "orange"},
        "nav-link": {"--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "green"},
    },
)

if menu == "Hypestat Scraper":
    st.title("Hypestat Scraper")
    st.markdown("Pilih metode input dan isi dengan URL website media yang diinginkan. Contoh: 'google.com'")
    st.markdown("Apabila menggunakan metode input excel, harap pastikan ada kolom dengan nama 'Link'")

with st.container(border=True):
    input_method = st.radio(
        "Select Input Method:",
        options=["Excel File", "Text Input"],
        horizontal=True
    )

    df = None

    if input_method == "Excel File":
        uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                with st.expander("Preview File", expanded=False):
                    st.write(df.head())
                if 'Link' not in df.columns:
                    st.error("'Link' column not found in the Excel file.")
                    df = None
            except Exception as e:
                st.error(f"Error loading file: {e}")
                df = None
    else:
        url_input = st.text_area("Enter website URLs (one per line):", height=200)
        if url_input:
            website_urls = [url.strip() for url in url_input.splitlines() if url.strip()]
            df = pd.DataFrame({'Link': website_urls})
        else:
            df = None

    st.divider()

    run_scraper = False
    if df is not None:
        run_scraper = st.button("Jalankan")

if df is not None and run_scraper:
    if 'Link' not in df.columns:
        st.error("'Link' column is required.")
    else:
        results = []
        progress_bar = st.progress(0)
        total_sites = len(df)
        error_count = 0

        for i, row in df.iterrows():
            website_url = row['Link']
            progress_percent = (i + 1) / total_sites
            progress_bar.progress(progress_percent)
            result = scrape_hypestat(website_url)
            results.append(result)
            if result['Status'].startswith("ERROR"):
                error_count += 1
            time.sleep(2)

        results_df = pd.DataFrame(results)
        st.dataframe(results_df)
        progress_bar.empty()

        if error_count > 0:
            st.warning(f"Scraping selesai. {error_count} dari {total_sites} media gagal diproses.")
        else:
            st.success("Scraping selesai tanpa kesalahan.")

        to_download = io.BytesIO()
        results_df.to_excel(to_download, index=False)
        to_download.seek(0)

        st.download_button(
            "Download Excel",
            data=to_download,
            file_name="hypestat_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif menu == "How to use":
st.title("How to Use")
st.markdown("""
### Petunjuk Penggunaan

1. Pilih metode input:
*   **Excel File:** Upload file Excel yang berisi link-link media. Pastikan ada kolom bernama 'Link'.
*   **Text Input:** Masukkan link-link media, satu link per baris.
2. Klik **Jalankan**, tunggu hingga proses selesai.
3. Jika berhasil, hasil scraping bisa langsung diunduh dalam format **Excel**.
""")

elif menu == "About":
st.title("About")
st.markdown("""
### Burson Hypestat Scraper v0.0.2

**Release Note:**
- Basic scraping untuk data Hypestat
- Fix 403 Forbidden error dengan headers

**Made by**: Jay and Naomi
""")
