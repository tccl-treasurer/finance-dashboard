#%%
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
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
import google_auth_httplib2
import httplib2


#%%

Scope = "https://www.googleapis.com/auth/spreadsheets"

def download_gsheet_values(SHEET_NAME,Cols,SCOPE=Scope):
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

def num_mult(a,b):
    tmp_a = pd.to_numeric(a,errors='coerce')
    tmp_b = pd.to_numeric(b,errors='coerce')
    return tmp_a * tmp_b

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

def giftaid_toggle(giftaid_choice): 

    tmp = st.session_state["income"]

    if giftaid_choice=='On-going':
        tmp['Income_Amount'] = tmp['Giftaid_Amount']
    elif giftaid_choice=='Lump-sum':
        tmp['Income_Amount'] = tmp['Credit_Amount']

    tmp['Income_Amount'] = pd.to_numeric(tmp['Income_Amount'])

    st.session_state["income"] = tmp

def format_plotly(fig,x=1/3,y=-0.2,background='#7c98cb',font_color='white'):
        fig = fig.update_layout(legend=dict(orientation="h", y=y, x=x))
        fig = fig.update_layout({'plot_bgcolor': background, 'paper_bgcolor': background,})
        fig = fig.update_layout(font_color=font_color,title_font_color=font_color,legend_title_font_color=font_color)
        return fig

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

def download_xero(df,income_flag):
    #download from google sheet tab
    xero = download_gsheet_values("Xero","A:N")
    xero['Date'] = pd.to_datetime(xero['Date'],format="%d %b %Y")
    xero['Account Code'] = pd.to_numeric(xero['Account Code'],errors='coerce')
    xero['Credit'] = pd.to_numeric(xero['Credit'],errors='coerce')
    xero['Debit'] = pd.to_numeric(xero['Debit'],errors='coerce')
    xero = xero[xero['Account Code'].isin([600,800])==False]
    cols = df.columns

    if income_flag:
        xero = xero[xero.Credit>0]
        xero['TD'] = 'xero'
        xero['Ref'] = 'xero'
        xero['Source'] = 'xero'
        xero['Regularity'] = ['Regular' if 'Regular' in x else 'One-off' for x in xero.Account]
        xero['Giftaid'] = [1 if 'non gift aided' in x else 1.25 for x in xero.Account]
        return_cols = ['TD','Credit','Date','Ref','Contact','Source','Congregation','Regularity','Giftaid']
        xero = xero[return_cols]
        xero.columns = cols
        df = pd.concat([df,xero],axis=0)
        return df

    else:

        category_dict = {
            430:'Expenses',
            433:'Expenses',
            401:'Expenses',
            463:'Expenses',
            4110:'Expenses',
            4114:'Expenses',
            480:'Expenses',
            4102:'Expenses',
            470:'Housing',
            4106:'Expenses',
            4120:'Expenses',
            4105:'Weekend Away',
            858:'Salaries',
            4111:'Expenses',
            477:'Expenses',
            493:'Expenses'
        }
        cat_df = pd.DataFrame.from_dict(category_dict,orient='index').reset_index()
        cat_df.columns = ['Account Code','Category']

        xero = xero[xero.Debit>0]
        xero['TD'] = 'xero'
        xero['Ref'] = 'xero'
        xero['Source'] = 'xero'
        xero['Regularity'] = ['Regular' if 'Regular' in x else 'One-off' for x in xero.Account]
        xero = pd.merge(xero,cat_df,how='left',on='Account Code')
        return_cols = ['Date','Account','Debit','Account','Category','Congregation']
        xero = xero[return_cols]
        xero.columns = cols
        df = pd.concat([df,xero],axis=0)
        return df

    
    #partition into income/expenses
    #relabel columns
    #recategorize
    #return
    #toggle for academic, calendar and tax year


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

# Payslip processing
# Using format of saved file
# df = pd.read_csv('Payslips_2019_202209.csv')
# df.Date = df.Date.ffill()
# df = df[~df['Employee Name'].isin(['Process Date:','Employee\nName'])]
# df
# %%
