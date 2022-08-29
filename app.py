#from pickle import FALSE
import google_auth_httplib2
import httplib2
import numpy as np
import pandas as pd
import streamlit as st
import math
import plotly.express as px
from google.oauth2 import service_account
from gsheetsdb import connect
from re import sub
from decimal import Decimal
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from PIL import Image
import time
from datetime import datetime
from anonymizedf.anonymizedf import anonymize
#import pandas_datareader as dr
import sys
import utils as utils

#Googlesheets data obtained using the methodology below:
#https://docs.streamlit.io/knowledge-base/tutorials/databases/private-gsheet

#settings
SCOPE = "https://www.googleapis.com/auth/spreadsheets"
sheet_url_income = st.secrets["private_gsheets_url"] + st.secrets["income"]
sheet_url_expenses = st.secrets["private_gsheets_url"] + st.secrets["expenses"]

# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],scopes=[SCOPE])
conn = connect(credentials=credentials)

# Uses st.cache to only rerun when the query changes or after 10 min.
#@st.cache(ttl=600)
def run_query(query):
    df = pd.DataFrame(conn.execute(query, headers=1).fetchall())
    return df

def run():
    if st.experimental_user['email'] is not None:
        allow_access = True
    else:
        allow_access = utils.check_password()
    
    if allow_access:

        # Password check used in other pages
        if 'auth' not in st.session_state:
            st.session_state.auth = 'correct'

        #st.sidebar.success("Select a page above")

        # if 'currency_choice' not in st.session_state:
        #     st.session_state["currency_choice"] = st.sidebar.radio("Choose Currency:",['GBP','USD'],horizontal=True)
        # else:
        #     st.session_state["currency_choice"] = st.sidebar.radio("Choose Currency:",['GBP','USD'],horizontal=True,index=['GBP','USD'].index(st.session_state["currency_choice"]))

        st.title('TCCL Finances')

        # Session state documentation: https://docs.streamlit.io/library/advanced-features/session-state
            
        # Make success disappear after 2 seconds using st.empty()
        # https://docs.streamlit.io/library/api-reference/layout/st.empty

        placeholder = st.empty()

        # Spinner while downloading: https://docs.streamlit.io/library/api-reference/status/st.spinner        
        with st.spinner('Downloading Data from Google Sheet. Please Wait...'):  

            t1 = datetime.now()

            # Download all Bank Data
            if 'income' not in st.session_state:
                tmp = run_query(f'SELECT * FROM "{sheet_url_income}"')
                tmp['Academic_Year'] = tmp['Transaction_Date'].map(lambda d: d.year + 1 if d.month > 8 else d.year)
                tmp['Giftaid_Amount'] = tmp['Credit_Amount'] * tmp['Giftaid']
                st.session_state["income"] = tmp
            if 'expenses' not in st.session_state:
                tmp2 = run_query(f'SELECT * FROM "{sheet_url_expenses}"')
                tmp2['Academic_Year'] = tmp2['Transaction_Date'].map(lambda d: d.year + 1 if d.month > 8 else d.year)
                st.session_state["expenses"] = tmp2

            t2 = datetime.now()
            time_delta = t2 - t1 

        placeholder.success(f'Success! Downloaded and filtered in {round(time_delta.total_seconds(),2)} seconds')

        #Markdown documentation: https://docs.streamlit.io/library/api-reference/text/st.markdown

        st.markdown(f"This Streamlit app interacts with the [TCCL Finances Google Sheet]({sheet_url_income}) to produce useful analytics.")

        st.markdown("Select **Overall** for a view of the overall financial picture.")

        st.markdown("Select **Individuals** to analyze donations from specific individuals.")

        st.markdown("Select **Tier Report** to group donors by size category and attribute overall giving to each category.")

        st.markdown("Select **Donor Comparison** to view each individual's change in donations each year.")

        st.markdown("This App was originally designed by <a href='mailto:claytongillespie116@gmail.com'>Clayton Gillespie</a> and is maintained by the TCCL Team.", unsafe_allow_html=True)

        st.markdown(f"Data last updated {str(st.session_state.income[['Transaction_Date']].iloc[-1,:][0])[0:10]}. You are logged in as {st.experimental_user['email']}.")

        st.markdown("_Soli Deo Gloria_")

        # Image documentation: https://docs.streamlit.io/library/api-reference/media/st.image
        image = Image.open('tccl_service.jpg') #added to GitHub
        st.image(image)

        time.sleep(0.7)

        placeholder.empty()

        #utils.convert_gbpusd(st.session_state["currency_choice"])

st.set_page_config(layout='centered')

run()

#useless comment to make a commit for backup