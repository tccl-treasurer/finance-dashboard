import inspect
import textwrap
import streamlit as st
import numpy as np
import pandas as pd
import streamlit as st
import math
from re import sub
from decimal import Decimal
import time 
from datetime import datetime
import requests
import json
import webbrowser
import base64
from io import StringIO
import altair as alt

def expense_category1():
    return {
    320:'Salaries',
    479:'Salaries',
    418:'Donations to Churches',
    4115:'Equipment, Books & Fliers',
    4108:'Kids & Youth Work',
    4114:'Food',
    482:'Salaries',
    4105:'Events',
    4116:'Hardship Fund',
    4106:'Kids & Youth Work',
    401:'Admin',
    4101:'Equipment, Books & Fliers',
    4112:'Equipment, Books & Fliers',
    4113:'Ministry Training',
    4103:'Events',
    4111:'General',
    429:'General',
    4119:'Equipment, Books & Fliers',
    4109:'Ministry Training',
    4117:'Equipment, Books & Fliers',
    720:'Equipment, Books & Fliers',
    4102:'Events',
    425:'Admin',
    4104:'Events',
    430:'Admin',
    433:'Admin',
    463:'Equipment, Books & Fliers'
}

def expense_category2():
    return {
    320:'Salaries',
    479:'Salaries',
    418:'Donations to Other Churches',
    4115:'Church Equipment',
    4108:'Kids & Youth Work',
    4114:'Food',
    482:'Salaries',
    4105:'Revive',
    4116:'Hardship Fund',
    4106:'Kids & Youth Work',
    401:'Accounting/Finance',
    4101:'Books',
    4112:'Music',
    4113:'Ministry Training',
    4103:'Events',
    4111:'Other Staff Expenses',
    429:'General',
    4119:'Venue costs',
    4109:'Ministry Training',
    4117:'Fliers & Advertising',
    720:'Church Equipment',
    4102:'Events',
    425:'Admin',
    4104:'Events',
    430:'Admin',
    433:'Insurance',
    463:'Tech'
}

#%%

def year_definition(df, option=None):
    
    if option=='tax':
        ret = []
        for i in df:
            if (i.month > 4) | ((i.month==4) & (i.day>5)):
                ret.append(i.year+1)
            else:
                ret.append(i.year)
        return ret
    elif option=='academic':
        ret = []
        for i in df:
            if i.month > 8: 
                ret.append(i.year+1)
            else:
                ret.append(i.year)
        return ret
    else:
        return df

# def download_xero(df,income_flag):
#     #download from google sheet tab
#     xero = download_gsheet_values("Xero","A:H")
#     xero['Date'] = pd.to_datetime(xero['Date'],format="%d %b %Y")

#     if income_flag:
#         #code
#         return xero

#     else:

#         category_dict = {
#             430:'Expenses',
#             433:'Expenses',
#             401:'Expenses',
#             463:'Expenses',
#             4105:'Expenses',
#             4110:'Expenses',
#             4112:'Expenses',
#             4114:'Expenses',
#             480:'Expenses',
#             4102:'Expenses',
#             470:'Housing',
#             4106:'Expenses',
#             4120:'Expenses',
#             4105:'Weekend Away',
#             858:'Salaries',
#             4111:'Expenses',
#             477:'Salaries',
#             493:'Expenses'
#         }
#         return xero

def report_table(report_df,sign):

    df = report_df[report_df.Classification_sign==sign].groupby(
        ['Calendar_Year','AccountCode','*Name'])['Total'].sum(
        ).to_frame('Total'
        ).sort_values(by='Calendar_Year',ascending=False
        ).pivot_table(index=['AccountCode','*Name'],columns='Calendar_Year',values='Total',sort=False
        ).sort_values(by='AccountCode'
        ).fillna(0
        ).reset_index().set_index('AccountCode')
    
    df.loc['Total']= df.sum()
    df.loc[df.index[-1], '*Name'] = ''

    height = len(df) * 37

    df_styled = df.style.set_properties(**{'text-align': 'center'})
    df_styled = df_styled.format(subset=[x for x in report_df['Calendar_Year'].unique()], formatter="£{:,.2f}")

    return df_styled, height, df

def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')


def XeroFirstAuth(auth_res_url,b64_id_secret,redirect_url):
    
    # b64_id_secret = base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8')).decode('utf-8')
    # auth_res_url = input('What is the response URL? ')

    #http://localhost:5000/?code=GeNwsDe-doWJbAIwelU6xgRzkgN9JbDbO2uddQwFbz0&scope=accounting.transactions.read%20offline_access&state=123
    #auth_res_url = "http://localhost:5000/?code=QbCn4Z2-uyo_Nr2mSKt9r2Ef__jB2cHzDfAxbG1NgSc&scope=accounting.transactions.read%20offline_access&state=123"
    start_number = auth_res_url.find('code=') + len('code=')
    end_number = auth_res_url.find('&scope')
    auth_code = auth_res_url[start_number:end_number]
    #print(auth_code)
    #print('\n')

    # 3. Exchange the code
    exchange_code_url = 'https://identity.xero.com/connect/token'
    response = requests.post(exchange_code_url, 
                            headers = {
                                'Authorization': 'Basic ' + b64_id_secret
                            },
                            data = {
                                'grant_type': 'authorization_code',
                                'code': auth_code,
                                'redirect_uri': redirect_url
                            })
    json_response = response.json()
    #st.write(json_response)
    #print(json_response)
    #print('\n')
    return [json_response['access_token'], json_response['refresh_token']]

# %%
# 5. Check the full set of tenants you've been authorized to access
def XeroTenants(access_token):
    connections_url = 'https://api.xero.com/connections'
    response = requests.get(connections_url,
                           headers = {
                               'Authorization': 'Bearer ' + access_token,
                               'Content-Type': 'application/json'
                           })
    json_response = response.json()
    #print(json_response)
    
    for tenants in json_response:
        json_dict = tenants
    return json_dict['tenantId']

# %%
def XeroRefreshToken(refresh_token,b64_id_secret):
    token_refresh_url = 'https://identity.xero.com/connect/token'
    response = requests.post(token_refresh_url,
                            headers = {
                                'Authorization' : 'Basic ' + b64_id_secret,
                                'Content-Type': 'application/x-www-form-urlencoded'
                            },
                            data = {
                                'grant_type' : 'refresh_token',
                                'refresh_token' : refresh_token
                            })
    json_response = response.json()
    #print(json_response)
    
    new_refresh_token = json_response['refresh_token']
    #rt_file = open('refresh_token.txt', 'w')
    #rt_file.write(new_refresh_token)
    #rt_file.close()
    
    return [json_response['access_token'], json_response['refresh_token']]

#XeroRefreshToken(json_response['refresh_token'])

# %%

@st.cache_data(show_spinner=False)
def DownloadXeroData(old_refresh_token,b64_id_secret):
    #old_refresh_token = open('refresh_token.txt', 'r').read()
    new_tokens = XeroRefreshToken(old_refresh_token,b64_id_secret)
    xero_tenant_id = XeroTenants(new_tokens[0]) 

    out = {}
    response_length = 1_000
    progress_text = "Downloading Transactions from the Xero API"
    response = requests.get("""https://api.xero.com/api.xro/2.0/TrackingCategories""",
                        headers = {
                            'Authorization': 'Bearer ' + new_tokens[0],
                            'Xero-tenant-id': xero_tenant_id,
                            'Accept': 'application/json'
                        })
    my_bar = st.progress(0, text=progress_text)
    p = 1
    while response_length >= 170: 
        get_url = f'https://api.xero.com/api.xro/2.0/BankTransactions?page={p}'
        response = requests.get(get_url,
                            headers = {
                                'Authorization': 'Bearer ' + new_tokens[0],
                                'Xero-tenant-id': xero_tenant_id,
                                'Accept': 'application/json'
                            })
        out[p] = json.dumps(response.json())
        response_length = len(out[p])
        #print(f'Page {p}, length = {response_length}')
        #st.write(f'Page {p}, length = {response_length}')
        p += 1
        if p<22:
            my_bar.progress(5*(p-1), text=progress_text)
        
    my_bar.progress(100, text=progress_text)   
    json_response = {}
    for k,v in out.items():
        json_response[k] = pd.read_json(StringIO(v))
    json_response = pd.concat(json_response.values()).reset_index(drop=True)

    my_bar.empty()

    return json_response

#%%

def altair_bar(plot_df,x,y,color,xOffset=None,stack='zero',text=True,sort_list=None,text_stack=None):
            
    fig = alt.Chart(plot_df).mark_bar().encode(
    x=alt.X(f'{x}:N',sort=sort_list,axis=alt.Axis(labelAngle=0)).title(f'{x.replace("_"," ")}'),
    y=alt.Y(f'{y}:Q',stack=stack),
    color=alt.Color(f'{color}:N',sort=sort_list) #.legend(orient="top",direction='horizontal',labelAlign ='left',padding=0)
    )
    text_offset = 0

    if xOffset is not None:
        fig = alt.Chart(plot_df).mark_bar().encode(
        x=alt.X(f'{x}:N',axis=alt.Axis(labelAngle=0)).title(f'{x.replace("_"," ")}'),
        y=alt.Y(f'{y}:Q',stack=stack),
        color=alt.Color(f'{color}:N',sort=sort_list),
        xOffset=alt.XOffset(field=xOffset,sort=sort_list)
        )
        text_offset = 6
    
    if text:
        text = fig.mark_text(dx=text_offset,dy=8,fontSize=14
                            ).encode(y=alt.Y(f'{y}:Q',stack=text_stack), #stack
                                    text=alt.Text(f'{y}',format=',.0f'),
                                    color=alt.value("white")
                                    )
    
        st.markdown('# ')
        st.altair_chart(fig + text,use_container_width=True)
    else:
    
        st.markdown('# ')
        st.altair_chart(fig,use_container_width=True)
