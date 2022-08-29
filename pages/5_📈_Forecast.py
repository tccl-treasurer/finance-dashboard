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
    
    recipients = st.multiselect('View Analysis for:',givers.Recipient.unique().tolist(),['General','Associate Pastor'])
    income_group = st.selectbox('Group Income by:',['Source','Recipient','Regularity','Name'])
    expense_group = st.selectbox('Group Expenses by:',['Category','Recipient','Regularity','Reference'])
    
    income = givers[givers.Recipient.isin(recipients)].groupby([income_group])['Annual_Amount'].sum().reset_index()
    income.columns = ['Group','Amount']
    income['bar'] = 'Income'
    expenses = costs[costs.Recipient.isin(recipients)].groupby([expense_group])['Annual_Amount'].sum().reset_index()
    expenses.columns = ['Group','Amount']
    expenses['bar'] = 'Costs'

    df = pd.concat([income,expenses])

    fig = px.bar(df,x="bar",y="Amount",color="Group")

    st.plotly_chart(fig)

    st.dataframe(df)

st.set_page_config(page_title="Forecast", page_icon="📊",layout='centered')

st.title('Budget Forecast')

if 'auth' in st.session_state:
    forecast_page()
else:
    st.subheader('Error: Go to Home to download data')