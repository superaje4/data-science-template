import streamlit as st
import pandas as pd
import time
from selenium.webdriver.common.keys import Keys#untuk tekan tekan
from selenium.webdriver.common.by import By#untuk nyari element
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime,timedelta
import numpy as np
import json
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import streamlit as st
from selenium.webdriver.chrome.options import Options
import os

@st.cache_data
def preprocess_data(df):
    df["Date"] = [i.strip()[:10] for i in df["Date"]]
    df["Date"] = pd.to_datetime(df["Date"])

    df["Close"] = df["Close"].astype(str)
    df["Close"] = df["Close"].replace("unk", np.nan)
    df["Close"] = df["Close"].astype(float)
    
    # Pastikan bahwa kolom 'Date' adalah tipe datetime jika belum
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Sortir DataFrame berdasarkan 'Date' untuk memastikan urutan yang benar
    df.sort_values(by=['Date'], inplace=True)
    
    # Pastikan bahwa kolom 'Date' adalah tipe datetime jika belum
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Sortir DataFrame berdasarkan 'Date' untuk memastikan urutan yang benar
    df.sort_values(by=['Date'], inplace=True)
    
    def fill_group(group):
        # Set indeks grup menjadi 'Date' untuk interpolasi berbasis waktu
        group = group.set_index('Date')
        
        # Lakukan interpolasi berbasis waktu, lalu forward fill dan backward fill
        group['Close'] = group['Close'].interpolate(method='time').ffill().bfill()
        
        # Kembalikan indeks ke kolom sebelumnya untuk menghindari pengubahan struktur DataFrame asli
        group = group.reset_index()
        return group
    
    df = df.groupby('StockCode').apply(fill_group).reset_index(drop=True)
    return df



# # Fungsi untuk menginstal dan mengatur geckodriver
# @st.cache_resource
# def install_geckodriver():
#     os.system('sbase install geckodriver')
#     os.system('ln -s /home/appuser/venv/lib/python3.9/site-packages/seleniumbase/drivers/geckodriver /home/appuser/venv/bin/geckodriver')

# # Pastikan geckodriver terinstal
# _ = install_geckodriver()

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager




# Fungsi untuk scraping data tambahan
@st.cache_data
def scrap_tambahan(perusahaan):
    stock_code = pd.read_csv("data/processed/clean_database.csv")["StockCode"].unique()
    start_date = '2024-03-02'
    now = datetime.now()
    one_day_before = now - timedelta(days=1)
    end_date = one_day_before.strftime("%Y-%m-%d")
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    formatted_dates = [str(date).split()[0].replace("-", "") for date in dates]  # Memperbaiki format tanggal
    
    try:
        tmp = pd.DataFrame(columns=["Date", "StockCode", "Close"])
        
        # Pengaturan FirefoxOptions untuk menjalankan dalam mode headless
        firefoxOptions = Options()
        firefoxOptions.add_argument("--headless")
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(
            options=firefoxOptions,
            service=service,
)
        
        for i in formatted_dates:
            url = f"https://www.idx.co.id/primary/TradingSummary/GetStockSummary?length=9999&start=0&date={i}"
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > pre")))
            time.sleep(0.2)
            
            page_source = driver.page_source
            if 'recordsTotal":0' in page_source:
                df = pd.DataFrame({"Date": [i[:4] + '-' + i[4:6] + '-' + i[6:] for _ in range(len(stock_code))],
                                   "StockCode": list(stock_code),
                                   "Close": ["unk" for _ in stock_code]})
                tmp = pd.concat([tmp, df], ignore_index=True)
            else:
                data = json.loads(driver.find_element(By.TAG_NAME, 'pre').text)
                df = pd.DataFrame(data["data"])
                df = df[["Date", "StockCode", "Close"]]
                tmp = pd.concat([tmp, df], ignore_index=True)

    finally:
        driver.quit()
        # Anda harus mendefinisikan fungsi preprocess_data di tempat lain
        tmp = preprocess_data(tmp)  # Pastikan fungsi ini ada dan berfungsi dengan benar
        tmp=tmp.loc[tmp['StockCode'] == perusahaan]
        return tmp


input=st.text_input('Masukkan kode saham')
if input:
    data=scrap_tambahan(input)
    st.write(data)