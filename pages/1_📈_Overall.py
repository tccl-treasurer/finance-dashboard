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

def overall_page():

    st.session_state["currency_choice"] = st.sidebar.radio("Choose Currency:",['GBP','USD'],horizontal=True,index=['GBP','USD'].index(st.session_state["currency_choice"]))

    utils.convert_gbpusd(st.session_state["currency_choice"])

    page_view = st.radio('Choose View:',['Income & Expenditure','Income by Source Type','Income by Core Vs Project','Expenditure by Source Type'],horizontal=True)

    # Retrive data from session_state
    data = st.session_state.data

    if page_view=='Income & Expenditure':

        # Calculate Overall Income and Expenditure by Year         
        df2 = data[['Y','Credit Amount','Debit Amount']].groupby(['Y']).sum().reset_index()
        df3 = df2.rename(columns={'Credit Amount':'Income','Debit Amount':'Expenditure'})
        df3 = pd.melt(df3, id_vars = ['Y'], var_name='Group')
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(df3, x="Y", y="value", color='Group', barmode='group', labels={
                     "value": str(page_view + " (" + st.session_state["currency_choice"] + ")")},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))
        
        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(df2,['Credit Amount','Debit Amount'],'Y')

    elif page_view=='Income by Source Type':

        # Calculate Income by Year & Source Type
        df4 = data[['Y','Credit Amount','Source Type']].groupby(['Y','Source Type']).sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(df4, x="Y", y="Credit Amount", color='Source Type', labels={
                     "Credit Amount": str("Income" + " (" + st.session_state["currency_choice"] + ")")},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

        df2 = df4.pivot(index='Source Type',columns='Y',values='Credit Amount').reset_index().fillna(0)
        df2 = utils.reindex_pivot(df2,df4.Y.unique().tolist())
        df2.columns = df2.columns.astype(str)

        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(df2,df2.columns[df2.columns!='Source Type'],['Source Type'])

    elif page_view=='Expenditure by Source Type':

        # Calculate Income by Year & Source Type
        df6 = data[['Y','Debit Amount','Source Type']].groupby(['Y','Source Type']).sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(df6, x="Y", y="Debit Amount", color='Source Type', labels={
                     "Debit Amount": str("Expenditure" + " (" + st.session_state["currency_choice"] + ")")},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

        df2 = df6.pivot(index='Source Type',columns='Y',values='Debit Amount').reset_index().fillna(0)
        df2 = utils.reindex_pivot(df2,df6.Y.unique().tolist())
        df2.columns = df2.columns.astype(str)
        
        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(df2,df2.columns[df2.columns!='Source Type'],['Source Type'])

    elif page_view=='Income by Core Vs Project':

        # Calculate Income by Year & Core/Project
        df8 = data[['Y','Credit Amount','Core/Project']].groupby(['Y','Core/Project']).sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(df8, x="Y", y="Credit Amount", color='Core/Project',  labels={
                     "Credit Amount": str("Income" + " (" + st.session_state["currency_choice"] + ")")},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

        df2 = df8.pivot(index='Core/Project',columns='Y',values='Credit Amount').reset_index().fillna(0)
        df2 = utils.reindex_pivot(df2,df8.Y.unique().tolist())
        df2.columns = df2.columns.astype(str)

        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(df2,df2.columns[df2.columns!='Core/Project'],['Core/Project'])

st.set_page_config(page_title="Overall", page_icon="📈",layout='centered')

st.title('Overall')

if 'auth' in st.session_state:
    overall_page()
else:
    st.subheader('Error: Go to Home to download data')
