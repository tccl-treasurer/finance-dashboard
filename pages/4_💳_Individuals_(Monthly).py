import numpy as np
import pandas as pd
import streamlit as st
import math
import plotly.express as px
from re import sub
from decimal import Decimal
# from st_aggrid import AgGrid
# from st_aggrid.grid_options_builder import GridOptionsBuilder
import time 
from datetime import datetime
import utils as utils

def individuals_monthly():

    st.session_state["payslips"] = st.sidebar.radio("Use Payslips:",['Yes','No'],horizontal=True,index=['Yes','No'].index(st.session_state["payslips"]))
    st.session_state["giftaid_choice"] = st.sidebar.radio("Giftaid Choice:",['Accrual','Cash'],horizontal=True)
    utils.giftaid_toggle(st.session_state["giftaid_choice"])

    view = st.radio('Choose View:',['Table','Chart'],horizontal=True)

    # Retrive Individual summed data from session_state
    input_data = st.session_state.income
    input_data['Month'] = pd.to_datetime(input_data['Transaction_Date']).dt.to_period('M')

    # Sum by Year - Month
    df = input_data.groupby(['Name','Month'])['Credit_Amount'].sum().reset_index()
    df['Month'] = df['Month'].astype(str)
    df['Month'] = df['Month'].str.replace('-','')
    df['Month'] = df['Month'].apply(lambda x: datetime.strptime(x,"%Y%m").date())

    output = df.pivot(index='Name',columns='Month',values='Credit_Amount').reset_index().fillna(0)

    # Cast to Wide and flip order: https://www.geeksforgeeks.org/how-to-reverse-the-column-order-of-the-pandas-dataframe/
    values = output.iloc[:,1:]  
    output = pd.concat([output['Name'],values[values.columns[::-1]]],axis=1)

    # Calculate Total column to rank table by
    total = df[['Name','Credit_Amount']].groupby(['Name']).sum().reset_index()
    total.columns = ['Name','Total']
    output.insert(1,"Total",total['Total'])
    output = output.sort_values(by='Total',ascending=False)

    output.columns = output.columns.astype(str)

    if view == 'Table':

        st.dataframe(output.style.format(precision=0,thousands=','))
        #utils.AgGrid_default(output,output.columns[output.columns.isin(['Name'])==False],['Name','Total'])

        # Possible future To-Do: load chart from interactive chart
        # Example: https://share.streamlit.io/pablocfonseca/streamlit-aggrid/main/examples/example.py
    
    else:
   
        # Multiselect Donors: https://docs.streamlit.io/library/api-reference/widgets/st.multiselect
        Donors = st.multiselect('Select Donors:',output['Name'].tolist(),output['Name'].tolist()[0:3])

        # Slider select daterange
        date_range = st.date_input("Date Range:",value=[datetime.strptime('20190101',"%Y%m%d").date(),max(df['Month'])],
        min_value=min(df['Month']), 
        max_value=max(df['Month']))

        plot_df = df[(df['Month']>=date_range[0]) & (df['Month']<=date_range[1])].pivot(index='Month',columns='Name',values='Credit_Amount').fillna(0)

        fig = px.bar(plot_df[Donors], facet_row="Name", facet_row_spacing=0.02, text_auto='.2s', height=550)

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