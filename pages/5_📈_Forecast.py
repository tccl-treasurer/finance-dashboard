import numpy as np
import pandas as pd
import streamlit as st
import math
import plotly.express as px
import plotly.graph_objects as go
from re import sub
from decimal import Decimal
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
import time 
from datetime import datetime
import utils as utils

def forecast_page():

    givers = st.session_state['givers']
    costs = st.session_state['costs']
    
    recipients = st.multiselect('View Analysis for:',givers.Recipient.unique().tolist(),['General'])

    col1, col2 = st.columns(2)

    with col1:
        income_group = st.selectbox('Group Income by:',['Source','Recipient','Regularity','Name'])
    
    with col2:
        expense_group = st.selectbox('Group Expenses by:',['Category','Recipient','Regularity','Reference'])
    
    income = givers[givers.Recipient.isin(recipients)].groupby([income_group])['Annual_Amount'].sum().reset_index()
    income.columns = ['Group','Amount']
    income['bar'] = 'Income'
    expenses = costs[costs.Recipient.isin(recipients)].groupby([expense_group])['Annual_Amount'].sum().reset_index()
    expenses.columns = ['Group','Amount']
    expenses['bar'] = 'Costs'

    df = pd.concat([income,expenses])

    fig = px.bar(df,x="bar",y="Amount",color="Group",text="Amount")
    fig.update_xaxes(title="")
    fig.update_traces(texttemplate="%{value:,.0f}")
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    fig.update_layout(legend=dict(orientation='h',yanchor="bottom",xanchor="center",y=-0.2,x=0.5))

    surplus = income.Amount.sum() - expenses.Amount.sum()
    if surplus>0:
        st.title(f"Surplus of £ {surplus:,.0f} forecast")
    else:
        st.title(f"Deficit of £ {surplus:,.0f} forecast")
        
    st.plotly_chart(fig)


    col3, col4 = st.columns(2)

    with col3:
        if st.checkbox('Show Income Breakdown by Name'):
            #st.header('Income')
            st.dataframe(givers[givers.Recipient.isin(recipients)][['Name','Annual_Amount']].sort_values('Annual_Amount',ascending=False))
    with col4:
        if st.checkbox('Show Expense Breakdown by Cost'):
            #st.header('Expenses')
            st.dataframe(costs[costs.Recipient.isin(recipients)][['Reference','Annual_Amount']].sort_values('Annual_Amount',ascending=False))

st.set_page_config(page_title="Forecast", page_icon="📊",layout='centered')

st.title('Budget Forecast')

if 'auth' in st.session_state:
    forecast_page()
else:
    st.subheader('Error: Go to Home to download data')