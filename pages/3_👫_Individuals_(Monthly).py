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
import utils as utils

def individuals_monthly():

    st.session_state["currency_choice"] = st.sidebar.radio("Choose Currency:",['GBP','USD'],horizontal=True,index=['GBP','USD'].index(st.session_state["currency_choice"]))

    utils.convert_gbpusd(st.session_state["currency_choice"])

    view = st.radio('Choose View:',['Table','Chart'],horizontal=True)

    # Retrive Individual summed data from session_state
    input_data = st.session_state.data

    # Sum by Year - Month
    df = input_data.groupby(['Renamer','Month']).sum().reset_index()
    df['Month'] = df['Month'].astype(str)
    df['Month'] = df['Month'].str.replace('-','')
    df['Month'] = df['Month'].apply(lambda x: datetime.strptime(x,"%Y%m").date())

    output = df.pivot(index='Renamer',columns='Month',values='Credit Amount').reset_index().fillna(0)

    # Cast to Wide and flip order: https://www.geeksforgeeks.org/how-to-reverse-the-column-order-of-the-pandas-dataframe/
    values = output.iloc[:,1:]  
    output = pd.concat([output['Renamer'],values[values.columns[::-1]]],axis=1)

    # Calculate Total column to rank table by
    total = df[['Renamer','Credit Amount']].groupby(['Renamer']).sum().reset_index()
    total.columns = ['Renamer','Total']
    output.insert(1,"Total",total['Total'])
    output = output.sort_values(by='Total',ascending=False)

    output.columns = output.columns.astype(str)

    if view == 'Table':

        utils.AgGrid_default(output,output.columns[output.columns.isin(['Renamer'])==False],['Renamer','Total'])

        # Possible future To-Do: load chart from interactive chart
        # Example: https://share.streamlit.io/pablocfonseca/streamlit-aggrid/main/examples/example.py
    
    else:
   
        # Multiselect Donors: https://docs.streamlit.io/library/api-reference/widgets/st.multiselect
        Donors = st.multiselect('Select Donors:',output['Renamer'].tolist(),output['Renamer'].tolist()[0:3])

        # Slider select daterange
        date_range = st.date_input("Date Range:",value=[datetime.strptime('20190101',"%Y%m%d").date(),max(df['Month'])],
        min_value=min(df['Month']), 
        max_value=max(df['Month']))

        plot_df = df[(df['Month']>=date_range[0]) & (df['Month']<=date_range[1])].pivot(index='Month',columns='Renamer',values='Credit Amount').fillna(0)

        fig = px.bar(plot_df[Donors], facet_row="Renamer", facet_row_spacing=0.02, text_auto='.2s', height=550)

        # hide and lock down axes and remove facet/subplot labels
        fig.update_xaxes(autorange="reversed")
        fig.update_yaxes(title="",matches=None)
        fig.update_layout(annotations=[], overwrite=True)
        fig.update_layout(legend=dict(x=-0.15),margin=dict(r=10,l=10,t=20,b=20))

        # disable the modebar for such a small plot
        st.plotly_chart(fig,use_container_width=True)

st.set_page_config(page_title="Individuals (Monthly)", page_icon="👫",layout='wide')

st.title('Individuals Monthly')

if 'auth' in st.session_state:
    individuals_monthly()
else:
    st.subheader('Error: Go to Home to download data')