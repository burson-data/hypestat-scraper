import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from streamlit_option_menu import option_menu
import io
import time


def scrape_hypestat(website_url):
    hypestat_url = f"https://hypestat.com/info/{website_url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(hypestat_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        dailyvisitor_element = soup.select_one(
            "#traffic > dl:nth-child(4) > dd:nth-child(2)"
        )
        dailyvisitor = (
            dailyvisitor_element.text.strip() if dailyvisitor_element else "0"
        )
        dailyvisitor = "0" if dailyvisitor.lower() == "n/a" else dailyvisitor

        dailyview_element = soup.select_one(
            "#traffic > dl:nth-child(4) > dd:nth-child(8)"
        )
        dailyview = dailyview_element.text.strip() if dailyview_element else "0"
        dailyview = "0" if dailyview.lower() == "n/a" else dailyview

        monthlyvisitsem_element = soup.select_one(
            "#traffic > dl:nth-child(4) > dd:nth-child(4)"
        )
        monthlyvisitsem = (
            monthlyvisitsem_element.text.strip()
            if monthlyvisitsem_element
            else "0"
        )
        monthlyvisitsem = (
            "0" if monthlyvisitsem.lower() == "n/a" else monthlyvisitsem
        )

        return {
            "Website": website_url,
            "Est. Reach": dailyvisitor,
            "Est. Impressions": dailyview,
            "Monthly Visitors": monthlyvisitsem,
            "Status": "OK",
        }

    except Exception as e:
        err_msg = str(e)
        return {
            "Website": website_url,
            "Est. Reach": None,
            "Est. Impressions": None,
            "Monthly Visitors": None,
            "Status": f"ERROR: {err_msg[:80]}",
        }


st.set_page_config(
    page_title="Burson Hypestat Scraper",
    layout="centered",
)

with st.sidebar:
    menu = option_menu(
        menu_title="Main Menu",
        options=["How to use", "Hypestat Scraper", "About"],
        icons=["question-circle-fill", "search", "diagram-3"],
        menu_icon="cast",
        default_index=1,
    )


if menu == "Hypestat Scraper":
    st.title("Hypestat Scraper")
    st.markdown(
        "Pilih metode input dan isi dengan URL website media. "
        "Contoh: 'google.com'"
    )

    input_method = st.radio(
        "Select Input Method:",
        options=["Excel File", "Text Input"],
        horizontal=True,
    )

    df = None

    if input_method == "Excel File":
        uploaded_file = st.file_uploader(
            "Upload Excel file",
            type=["xlsx"],
        )

        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.write(df.head())

                if "Link" not in df.columns:
                    st.error("'Link' column not found.")
                    df = None

            except Exception as e:
                st.error(f"Error: {e}")
                df = None

    else:
        url_input = st.text_area(
            "Enter website URLs (one per line):",
            height=200,
        )

        if url_input:
            website_urls = [
                url.strip()
                for url in url_input.splitlines()
                if url.strip()
            ]
            df = pd.DataFrame({"Link": website_urls})

    run_scraper = st.button("Jalankan") if df is not None else False

    if df is not None and run_scraper:
        results = []
        progress_bar = st.progress(0)
        total_sites = len(df)
        error_count = 0

        for i, row in df.iterrows():
            website_url = row["Link"]
            progress_bar.progress((i + 1) / total_sites)

            result = scrape_hypestat(website_url)
            results.append(result)

            if result["Status"].startswith("ERROR"):
                error_count += 1

            time.sleep(2)

        results_df = pd.DataFrame(results)
        st.dataframe(results_df)

        progress_bar.empty()

        if error_count > 0:
            st.warning(
                f"Scraping selesai. {error_count} dari "
                f"{total_sites} gagal."
            )
        else:
            st.success("Scraping selesai tanpa kesalahan.")

        to_download = io.BytesIO()
        results_df.to_excel(to_download, index=False)
        to_download.seek(0)

        st.download_button(
            "Download Excel",
            data=to_download,
            file_name="hypestat_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


elif menu == "How to use":
    st.title("How to Use")
    st.markdown(
        "1. Pilih Excel File atau Text Input\n"
        "2. Klik Jalankan\n"
        "3. Download hasil"
    )


elif menu == "About":
    st.title("About")
    st.markdown(
        "Burson Hypestat Scraper v0.0.2\n\n"
        "Made by: Jay and Naomi"
    )
