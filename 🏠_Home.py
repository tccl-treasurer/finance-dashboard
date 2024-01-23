#%%
# #from pickle import FALSE
import numpy as np
import pandas as pd
import streamlit as st
import math
import plotly.express as px
from re import sub
from decimal import Decimal
# from st_aggrid import AgGrid
# from st_aggrid.grid_options_builder import GridOptionsBuilder
from PIL import Image
import time
from datetime import datetime
import sys
import utils as utils

#%%

#Googlesheets data obtained using the methodology below:
#https://docs.streamlit.io/knowledge-base/tutorials/databases/private-gsheet

#settings
sheet_url_income = st.secrets["private_gsheets_url"] + st.secrets["income"]
sheet_url_givers = st.secrets["private_gsheets_url"] + st.secrets["givers"]
sheet_url_expenses = st.secrets["private_gsheets_url"] + st.secrets["expenses"]
sheet_url_costs = st.secrets["private_gsheets_url"] + st.secrets["costs"]
sheet_url_xero = st.secrets["private_gsheets_url"] + st.secrets["xero"]

#%%

def run():

    with st.sidebar:
        payslip_choice = st.radio("Use Payslips:",['Yes','No'],horizontal=True)
        giftaid_choice = st.sidebar.radio("Giftaid Choice:",['Accrual','Cash'],horizontal=True)

    if 'payslips' not in st.session_state:
        st.session_state["payslips"] = payslip_choice
    else:
        st.session_state["payslips"] = payslip_choice

    if 'giftaid_choice' not in st.session_state:
        st.session_state["giftaid_choice"] = giftaid_choice
    else:
        st.session_state["giftaid_choice"] = giftaid_choice

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
                tmp = utils.download_gsheet_values("Income","A:I")
                num_cols = ['Credit_Amount','Giftaid']
                tmp[num_cols] = tmp[num_cols].apply(lambda x: pd.to_numeric(x.astype(str)
                                                .str.replace(',',''), errors='raise'))
                tmp['Transaction_Date'] = pd.to_datetime(tmp['Transaction_Date'],format="%d/%m/%Y")
                tmp = utils.download_xero(tmp,income_flag=True)
                #tmp['Academic_Year'] = tmp['Transaction_Date'].map(lambda d: d.year + 1 if d.month > 8 else d.year)
                tmp['Academic_Year'] = utils.academic_year(tmp['Transaction_Date'])
                tmp['Tax_Year'] = utils.tax_year(tmp['Transaction_Date'])
                tmp['Calendar_Year'] = tmp['Transaction_Date'].apply(lambda x: x.year)
                #tmp['Month'] = tmp['Transaction_Date'].dt.to_period('M')
                tmp['Giftaid_Amount'] = utils.num_mult(tmp['Credit_Amount'],tmp['Giftaid'])
                tmp['Recipient'] = ['International' if x=='Morgan' else x for x in tmp['Recipient']]
                tmp['Recipient'] = ['International' if x=='General' else x for x in tmp['Recipient']]
                tmp['Source'] = tmp['Source'].fillna('Internal')
                tmp = tmp.drop_duplicates()
                #tmp = tmp[tmp.Recipient!='House'] #remove house donations
                st.session_state["income"] = tmp

            if 'expenses' not in st.session_state:
                tmp2 = utils.download_gsheet_values("Expenses","A:F")
                num_cols = ['Debit_Amount']
                tmp2[num_cols] = tmp2[num_cols].apply(lambda x: pd.to_numeric(x.astype(str)
                                                .str.replace(',',''), errors='raise'))
                tmp2['Transaction_Date'] = pd.to_datetime(tmp2['Transaction_Date'],format="%d/%m/%Y")
                tmp2['Debit_Amount'] = pd.to_numeric(tmp2['Debit_Amount'],errors='coerce')
                tmp2 = utils.download_xero(tmp2,income_flag=False)
                #tmp2['Academic_Year'] = tmp2['Transaction_Date'].map(lambda d: d.year + 1 if d.month > 8 else d.year)
                tmp2['Academic_Year'] = utils.academic_year(tmp2['Transaction_Date'])
                tmp2['Tax_Year'] = utils.tax_year(tmp2['Transaction_Date'])
                tmp2['Calendar_Year'] = tmp2['Transaction_Date'].dt.year
                tmp2['Recipient'] = ['International' if x=='General' else x for x in tmp2['Recipient']]
                tmp2['Category'] = tmp2['Category'].fillna('Expenses')
                st.session_state["expenses"] = tmp2
                
            if 'givers' not in st.session_state:
                givers = utils.download_gsheet_values("Givers","A:F")
                givers['Giftaid_Amount'] = pd.to_numeric(givers['Amount']) * pd.to_numeric(givers['Giftaid'])
                givers['Annual_Multiplier'] = [12 if x=='Monthly' else 1 for x in givers['Regularity']]
                givers['Annual_Amount'] = utils.num_mult(givers['Annual_Multiplier'],givers['Giftaid_Amount'])
                st.session_state["givers"] = givers

            if 'costs' not in st.session_state:
                costs = utils.download_gsheet_values("Costs","A:E")
                costs['Annual_Multiplier'] = [12 if x=='Monthly' else 1 for x in costs['Regularity']]
                costs['Annual_Amount'] = utils.num_mult(costs['Annual_Multiplier'],costs['Amount'])
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

        utils.giftaid_toggle(st.session_state["giftaid_choice"])

st.set_page_config(layout='centered')

run()

#st.dataframe(st.session_state['income'])

#useless comment to make a commit for backup