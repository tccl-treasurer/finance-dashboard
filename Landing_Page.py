# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit.logger import get_logger
import utils
import requests
import webbrowser
import base64
from io import StringIO
import numpy as np
import pandas as pd
import altair as alt
import os
import time

LOGGER = get_logger(__name__)

def run():
    st.set_page_config(page_title="TC Finance Dashboard")

    st.title("TC Church Finances")

    st.markdown(""" 
    This is a <a href="https://www.streamlit.io">__streamlit__</a> dashboard, designed to help manage the finances of Trinity Church Central London. 
    
    It is built to connect to TC's <a href="https://www.Xero.com"> __Xero__</a> account and builds from classifications and contacts there. 
    
    To access the dashboard's functionality, follow the steps below:
                
        1. Click on the checkbox below. You will be taken to a new tab.
        2. Login to Xero. Click the blue button to "Allow access".
        3. When the next page has loaded, copy the new URL and enter it in the box below.
        4. This will open a 3rd tab, where you will need to push "Allow access" again.
        5. You should now see a progress bar appear below the box.
        6. When it finishes, after 1-2mins, a success message should appear. 
        7. The dashboard is now ready to use. Select one of the pages from the sidebar. 
                       
    So far, there are 5 pages, which can be accessed using the sidebar on the left.      
                
                """,unsafe_allow_html=True)

    #st.markdown("<br>", unsafe_allow_html=True)

    client_id = st.secrets.client_id
    client_secret = st.secrets.client_secret 
    redirect_url = st.secrets.redirect_url 
    scope = st.secrets.scope
    b64_id_secret = base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8')).decode('utf-8')
    df = pd.DataFrame()
    auth_url = ('''https://login.xero.com/identity/connect/authorize?response_type=code''' +
            '''&client_id=''' + client_id + '''&redirect_uri=''' + redirect_url +
            '''&scope=''' + scope + '''&state=123''')
    
    #button to refresh 
    #else load from parquet
    #else error with need to refresh

    if st.checkbox('Download Data'):

        # if st.checkbox('Authorize and Download'):
        webbrowser.open_new(auth_url)
        auth_res_url = st.text_input('Enter the response URL:')
        if len(auth_res_url)==0:
            st.stop()

        old_tokens = utils.XeroFirstAuth(auth_res_url,b64_id_secret,redirect_url)
        #old_refresh_token = utils.XeroRefreshToken(old_tokens[1])
        #with st.status("Downloading Transactions from the Xero API"):
        json_df = utils.DownloadXeroData(old_tokens[1],b64_id_secret)
        success_containter = st.empty()
        with success_containter:
            st.success("Transactions Successfully Downloaded")
            time.sleep(0.5)
        success_containter.empty()
        mapping = pd.read_csv('ChartOfAccounts.csv')
        s = json_df['BankTransactions']
        df = pd.DataFrame(s.values.tolist(), index=s.index)
        df = df[df.Status!='DELETED']
        df = df[df.Contact.notnull()]
        df['BankAccountName'] = [x['Name'] for x in df['BankAccount']]
        df['BankAccountID'] = [x['AccountID'] for x in df['BankAccount']]
        df['ContactID'] = df['Contact'].apply(lambda x: x['ContactID'])
        df['Name'] = df['Contact'].apply(lambda x: x['Name'])
        df['Date'] = pd.to_datetime(df['DateString'])
        df['AccountCode'] = df['LineItems'].apply(lambda x: x[0]['AccountCode'])
        df = pd.merge(df,mapping,left_on=['AccountCode'],right_on=['*Code'])
        df['AccountCode'] = pd.to_numeric(df['AccountCode'],errors='raise')
        df['Year'] = df.Date.dt.year
        df['Quarter'] = df.Date.dt.to_period('Q')
        df['Tax_Year'] = utils.year_definition(df['Date'],option='tax')
        df['Academic_Year'] = utils.year_definition(df['Date'],option='academic')
        df = df[df.AccountCode!=150]
        df['Giftaid_Multiplier'] = np.where(df.AccountCode<125,1.25,1)
        df['Total'] = df['Total'] * df['Giftaid_Multiplier']
        s = df['AccountCode']
        df['Classification'] = np.where(s<300,'Income','Expenses')
        df['Classification_sign'] = np.where(s<300,1,-1)
        df['Directional_Total'] = df['Total'] * df['Classification_sign']
        #df.to_parquet('xero_data.parquet')
        st.session_state['xero_data'] = df

    if os.path.exists('xero_data.parquet'):    
        st.session_state['xero_data'] = pd.read_parquet('xero_data.parquet')
    else:
        st.write("No local data, please push Refresh to download")
    
if __name__ == "__main__":
    run()
