import numpy as np
import pandas as pd
import streamlit as st
import math
import plotly.express as px
from re import sub
from decimal import Decimal
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
import time 
from datetime import datetime

def AgGrid_default(DF,curreny_cols=[],pinned_cols=[],min_height=600):
        gb = GridOptionsBuilder.from_dataframe(DF)
        gb.configure_grid_options(enableRangeSelection=True)
        
        for col in curreny_cols:
                # if st.session_state["currency_choice"]=='GBP':
                gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="£", aggFunc='max')
                # elif st.session_state["currency_choice"]=='USD':
                #     gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="$", aggFunc='max')
        
        for col in pinned_cols:
                    gb.configure_column(col,pinned=True)

        out = AgGrid(DF,
        gridOptions=gb.build(),
        fill_columns_on_grid_load=True,
        height=min(min_height,36*(len(DF)+1)),
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True
        )

        return out

def reindex_pivot(df,years):
    df3 = pd.DataFrame()
    cols_reversed = df.columns.tolist()
    cols_reversed.reverse()
    for i in cols_reversed:
        if i in years:
            df3[i] = df[i] 
        else:
            df3.insert(0,i,df[i])
    return df3

# Convert to USD/GBP
def convert_gbpusd(curr): 

    tmp = st.session_state["data"]

    if curr=='USD':
        tmp['Credit Amount'] = tmp['Credit Amount USD']
        tmp['Debit Amount'] = tmp['Debit Amount USD']
    elif curr=='GBP':
        tmp['Credit Amount'] = tmp['Credit Amount GBP']
        tmp['Debit Amount'] = tmp['Debit Amount GBP']

    st.session_state["data"] = tmp

    # Choice flows through into DM and TRD
    DM = tmp[['Renamer','Source Type','Y','Credit Amount','Debit Amount']].groupby(['Renamer','Source Type','Y']).sum().reset_index()
    st.session_state["DM"] = DM
    try: 
        st.session_state["TRD"] = DM[DM['Renamer']!=st.session_state["giftaid_fake_name"]]           
    except:
        st.session_state["TRD"] = DM[DM['Renamer']!='Gift Aid (HMRC Charities)']

#password check
#using Option 2 here: https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
        st.session_state["username"] in st.secrets["passwords"]
        and st.session_state["password"]
        == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            #del st.session_state["username"] # store username for anon check

        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Username", key="username") #on_change=password_entered,
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", key="username") #on_change=password_entered,
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True

# If guest account, anonymize names:
# https://towardsdatascience.com/how-to-quickly-anonymize-personal-names-in-python-6e78115a125b
# https://pypi.org/project/anonymizedf/

# if st.experimental_user['email'] is not None:
#     st.session_state["data"] = tmp
# elif st.session_state["username"]=="admin":
#     st.session_state["data"] = tmp
# else:    
#     an = anonymize(tmp)
#     an.fake_names("Renamer")
#     tmp['Renamer'] = tmp['Fake_Renamer']
#     st.session_state["data"] = tmp
