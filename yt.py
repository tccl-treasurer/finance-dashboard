#%%
import json
import requests
import webbrowser
import base64
from io import StringIO
import pandas as pd
import streamlit as st

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

@st.cache_data #(suppress_st_warning=True)
def DownloadXeroData(old_refresh_token,b64_id_secret):
    #old_refresh_token = open('refresh_token.txt', 'r').read()
    new_tokens = XeroRefreshToken(old_refresh_token,b64_id_secret)
    xero_tenant_id = XeroTenants(new_tokens[0]) 

    out = {}
    response_length = 1_000
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
        st.write(f'Page {p}, length = {response_length}')
        p += 1
        
    json_response = {}
    for k,v in out.items():
        json_response[k] = pd.read_json(StringIO(v))
    json_response = pd.concat(json_response.values()).reset_index(drop=True)

    return json_response

#%%

# old_tokens = XeroFirstAuth()
# XeroRefreshToken(old_tokens[1])

# # %%

# json_df = XeroRequests()    
# mapping = pd.read_csv('ChartOfAccounts_v2.csv')
# s = json_df['BankTransactions']
# df = pd.DataFrame(s.values.tolist(), index=s.index)
# df = df[df.Status!='DELETED']
# df['ContactID'] = df['Contact'].apply(lambda x: x['ContactID'])
# df['Name'] = df['Contact'].apply(lambda x: x['Name'])
# df['Date'] = pd.to_datetime(df['DateString'])
# df['AccountCode'] = df['LineItems'].apply(lambda x: x[0]['AccountCode'])
# df = pd.merge(df,mapping,left_on=['AccountCode'],right_on=['*Code'])
# df.head()

#%%