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
import yt as yt
import json
import requests
import webbrowser
import base64
from io import StringIO
import numpy as np
import pandas as pd
import altair as alt
import os
import duckdb

LOGGER = get_logger(__name__)

def run():
    st.set_page_config(page_title="TCCL Finance Dashboard")

    st.title("Trinity Church Central London Finance Dashboard")

    st.markdown("<br>", unsafe_allow_html=True)

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

    if st.checkbox('Refresh Data'):

        # if st.checkbox('Authorize and Download'):
        webbrowser.open_new(auth_url)
        auth_res_url = st.text_input('Enter the response URL:')
        if len(auth_res_url)==0:
            st.stop()

        old_tokens = yt.XeroFirstAuth(auth_res_url,b64_id_secret,redirect_url)
        st.write(old_tokens[1])
        #old_refresh_token = yt.XeroRefreshToken(old_tokens[1])
        with st.status("Downloading Transactions from the Xero API"):
            json_df = yt.DownloadXeroData(old_tokens[1],b64_id_secret)
        mapping = pd.read_csv('ChartOfAccounts.csv')
        mapping['*Code'] = pd.to_numeric(mapping['*Code'],errors='coerce')
        s = json_df['BankTransactions']
        df = pd.DataFrame(s.values.tolist(), index=s.index)
        df = df[df.Status!='DELETED']
        df = df[(df.Type!='SPEND-TRANSFER') & (df.Type!='RECEIVE-TRANSFER')]
        df['BankAccountName'] = [x['Name'] for x in df['BankAccount']]
        df['BankAccountID'] = [x['AccountID'] for x in df['BankAccount']]
        df['ContactID'] = df['Contact'].apply(lambda x: x['ContactID'])
        df['Name'] = df['Contact'].apply(lambda x: x['Name'])
        df['Date'] = pd.to_datetime(df['DateString'])
        df['AccountCode'] = df['LineItems'].apply(lambda x: x[0]['AccountCode'])
        df['AccountCode'] = pd.to_numeric(df['AccountCode'],errors='coerce')
        df = df[df['AccountCode']!=150] # remove bank account transfers
        df = pd.merge(df,mapping,left_on=['AccountCode'],right_on=['*Code'],how='left')
        df['AccountCode'] = pd.to_numeric(df['AccountCode'],errors='raise')
        df['Year'] = df.Date.dt.year
        df['Quarter'] = df.Date.dt.to_period('Q')
        s = df['AccountCode']
        df['Classification'] = np.where(s<300,'Income','Expenses')
        df['Classification_sign'] = np.where(s<300,1,-1)
        df['Directional_Total'] = df['Total'] * df['Classification_sign']
        df.to_parquet('xero_data.parquet')
        st.session_state['xero_data'] = df

    if os.path.exists('xero_data.parquet'):    
        st.session_state['xero_data'] = pd.read_parquet('xero_data.parquet')
    else:
        st.write("No local data, please push Refresh to download")
    
if __name__ == "__main__":
    run()
