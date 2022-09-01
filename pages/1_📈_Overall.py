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

    #st.session_state["currency_choice"] = st.sidebar.radio("Choose Currency:",['GBP','USD'],horizontal=True,index=['GBP','USD'].index(st.session_state["currency_choice"]))

    #utils.convert_gbpusd(st.session_state["currency_choice"])

    page_view = st.radio('Choose View:',['Income & Expenditure','Income by Source Type','Income by Regularity','Expenditure by Source Type'],horizontal=True) #'Expenditure by Reference'

    # Retrive data from session_state
    income = st.session_state.income
    expenses = st.session_state.expenses

    if page_view=='Income & Expenditure':

        #Define Years
        annual_income = income[['Academic_Year','Giftaid_Amount']].groupby(['Academic_Year']).sum()
        annual_income = annual_income.rename(columns={'Giftaid_Amount':'Income'})

        annual_expenses = expenses[['Academic_Year','Debit_Amount']].groupby(['Academic_Year']).sum()
        annual_expenses = annual_expenses.rename(columns={'Debit_Amount':'Expenses'})

        annual_data = annual_income.join(annual_expenses).reset_index()
        annual_data_melt = pd.melt(annual_data, id_vars = ['Academic_Year'], var_name='Group')
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(annual_data_melt, x="Academic_Year", y="value", color='Group', barmode='group', labels={
                     "value": "Income / Expenditure (£)"},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))
        
        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(annual_data,['Income','Expenses'],['Academic_Year'])

    elif page_view=='Income by Source Type':

        # Calculate Income by Year & Source Type
        income_type = income[['Academic_Year','Source','Giftaid_Amount']].groupby(['Source','Academic_Year']).sum().reset_index()

        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(income_type, x="Academic_Year", y="Giftaid_Amount", color='Source', labels={
                     "Giftaid_Amount": "Income"},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

        income_type_pivot = income_type.pivot(index='Source',columns='Academic_Year',values='Giftaid_Amount').reset_index().fillna(0)
        income_type_pivot = utils.reindex_pivot(income_type_pivot,income_type.Academic_Year.unique().tolist())
        income_type_pivot.columns = income_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(income_type_pivot,income_type_pivot.columns[income_type_pivot.columns!='Source'],['Source'])

    elif page_view=='Income by Regularity':

        # Calculate Income by Year & Source Type
        income_type = income[['Month','Regularity','Giftaid_Amount']].groupby(['Regularity','Month']).sum().reset_index()
        income_type['Month'] = income_type['Month'].astype(str)

        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(income_type, x="Month", y="Giftaid_Amount", color='Regularity', labels={
                     "Giftaid_Amount": "Income"},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

        income_type_pivot = income_type.pivot(index='Regularity',columns='Month',values='Giftaid_Amount').reset_index().fillna(0)
        income_type_pivot = utils.reindex_pivot(income_type_pivot,income_type.Month.astype(str).unique().tolist())
        income_type_pivot.columns = income_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(income_type_pivot,income_type_pivot.columns[income_type_pivot.columns!='Regularity'],['Regularity'])

    elif page_view=='Expenditure by Source Type':

        # Calculate Income by Year & Source Type
        expenses_type = expenses[['Academic_Year','Category','Debit_Amount']].groupby(['Category','Academic_Year']).sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(expenses_type, x="Academic_Year", y="Debit_Amount", color='Category', labels={
                     "Debit_Amount": "Expenses"},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

        expenses_type_pivot = expenses_type.pivot(index='Category',columns='Academic_Year',values='Debit_Amount').reset_index().fillna(0)
        expenses_type_pivot = utils.reindex_pivot(expenses_type_pivot,expenses_type.Academic_Year.unique().tolist())
        expenses_type_pivot.columns = expenses_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(expenses_type_pivot,expenses_type_pivot.columns[expenses_type_pivot.columns!='Category'],['Category'])

    # elif page_view=='Expenditure by Reference':

    #     # Calculate Income by Year & Source Type
    #     expenses_type = expenses[['Academic_Year','Reference','Debit_Amount']].groupby(['Reference','Academic_Year']).sum().reset_index()
        
    #     # Plotly bar chart: https://plotly.com/python/bar-charts/
    #     fig = px.bar(expenses_type, x="Academic_Year", y="Debit_Amount", color='Reference', labels={
    #                  "Debit_Amount": "Expenses"},height=400)
        
    #     # Legend positioning: https://plotly.com/python/legend/
    #     fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

    #     expenses_type_pivot = expenses_type.pivot(index='Reference',columns='Academic_Year',values='Debit_Amount').reset_index().fillna(0)
    #     expenses_type_pivot = utils.reindex_pivot(expenses_type_pivot,expenses_type.Academic_Year.unique().tolist())
    #     expenses_type_pivot.columns = expenses_type_pivot.columns.astype(str)

    #     st.plotly_chart(fig, use_container_width=True)
    #     utils.AgGrid_default(expenses_type_pivot,expenses_type_pivot.columns[expenses_type_pivot.columns!='Reference'],['Reference'])

st.set_page_config(page_title="Overall", page_icon="📈",layout='centered')

st.title('Overall')

if 'auth' in st.session_state:
    overall_page()
else:
    st.subheader('Error: Go to Home to download data')
