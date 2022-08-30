#from pickle import FALSE
import google_auth_httplib2
import httplib2
import numpy as np
import pandas as pd
import streamlit as st
import math
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
from re import sub
from decimal import Decimal
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from PIL import Image
import time
from datetime import datetime
import sys
import utils as utils

#Googlesheets data obtained using the methodology below:
#https://docs.streamlit.io/knowledge-base/tutorials/databases/private-gsheet

#settings
SCOPE = "https://www.googleapis.com/auth/spreadsheets"
sheet_url_income = st.secrets["private_gsheets_url"] + st.secrets["income"]
sheet_url_givers = st.secrets["private_gsheets_url"] + st.secrets["givers"]
sheet_url_expenses = st.secrets["private_gsheets_url"] + st.secrets["expenses"]
sheet_url_costs = st.secrets["private_gsheets_url"] + st.secrets["costs"]

def download_gsheet_values(SHEET_NAME,Cols):
    # Create a connection object.
    credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],scopes=[SCOPE])

    def build_request(http, *args, **kwargs):
        new_http = google_auth_httplib2.AuthorizedHttp(
            credentials, http=httplib2.Http()
        )
        return HttpRequest(new_http, *args, **kwargs)

    authorized_http = google_auth_httplib2.AuthorizedHttp(credentials, http=httplib2.Http())
    service = build("sheets","v4",requestBuilder=build_request,http=authorized_http,cache_discovery=False)
    gsheet_connector = service.spreadsheets()

    values = (gsheet_connector.values()
        .get(spreadsheetId=st.secrets["sheet_id"],range=f"{SHEET_NAME}!{Cols}")
        .execute()
    )
    df = pd.DataFrame(values["values"])
    df.columns = df.iloc[0,:]
    df = df[1:]    
    return df  

def run():

    st.write(st.experimental_user['email'])

    if st.experimental_user['email'] is not None:
        allow_access = True
    else:
        allow_access = utils.check_password()
    
    if allow_access:

        # Password check used in other pages
        if 'auth' not in st.session_state:
            st.session_state.auth = 'correct'

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
                tmp = download_gsheet_values("Income","A:I")
                tmp['Transaction_Date'] = pd.to_datetime(tmp['Transaction_Date'],format="%d/%m/%Y")
                tmp['Academic_Year'] = tmp['Transaction_Date'].map(lambda d: d.year + 1 if d.month > 8 else d.year)
                tmp['Month'] = tmp['Transaction_Date'].dt.to_period('M')
                tmp['Giftaid_Amount'] = pd.to_numeric(tmp['Credit_Amount']) * pd.to_numeric(tmp['Giftaid'])
                st.session_state["income"] = tmp
            if 'expenses' not in st.session_state:
                tmp2 = download_gsheet_values("Expenses","A:I")
                tmp2['Transaction_Date'] = pd.to_datetime(tmp2['Transaction_Date'],format="%d/%m/%Y")
                tmp2['Debit_Amount'] = pd.to_numeric(tmp2['Debit_Amount'])
                tmp2['Academic_Year'] = tmp2['Transaction_Date'].map(lambda d: d.year + 1 if d.month > 8 else d.year)
                st.session_state["expenses"] = tmp2
            if 'givers' not in st.session_state:
                givers = download_gsheet_values("Givers","A:F")
                givers['Giftaid_Amount'] = pd.to_numeric(givers['Amount']) * pd.to_numeric(givers['Giftaid'])
                givers['Annual_Multiplier'] = [12 if x=='Monthly' else 1 for x in givers['Regularity']]
                givers['Annual_Amount'] = pd.to_numeric(givers['Annual_Multiplier']) * pd.to_numeric(givers['Giftaid_Amount'])
                st.session_state["givers"] = givers
            if 'costs' not in st.session_state:
                costs = download_gsheet_values("Costs","A:E")
                costs['Annual_Multiplier'] = [12 if x=='Monthly' else 1 for x in costs['Regularity']]
                costs['Annual_Amount'] = pd.to_numeric(costs['Annual_Multiplier']) * pd.to_numeric(costs['Amount'])
                st.session_state["costs"] = costs

            t2 = datetime.now()
            time_delta = t2 - t1 

        placeholder.success(f'Success! Downloaded and filtered in {round(time_delta.total_seconds(),1)} seconds')

        #Markdown documentation: https://docs.streamlit.io/library/api-reference/text/st.markdown

        st.markdown(f"This Streamlit app interacts with the [TCCL Finances Google Sheet]({sheet_url_income}) to produce useful analytics.")

        st.markdown("Select **Overall** for a view of the overall financial picture.")

        st.markdown("Select **Individuals** to analyze donations from specific individuals.")

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