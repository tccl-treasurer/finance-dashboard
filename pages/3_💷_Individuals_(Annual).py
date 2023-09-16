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

def individuals_annual():

    st.session_state["payslips"] = st.sidebar.radio("Use Payslips:",['Yes','No'],horizontal=True,index=['Yes','No'].index(st.session_state["payslips"]))
    st.session_state["giftaid_choice"] = st.sidebar.radio("Giftaid Choice:",['Accrual','Cash'],horizontal=True)
    utils.giftaid_toggle(st.session_state["giftaid_choice"])

    view = st.radio('Choose View:',['Table','Chart'],horizontal=True)

    # Retrive Individual summed data from session_state
    input_data = st.session_state.income

    # Sum by Year
    df = input_data.groupby(['Name','Academic_Year'])['Credit_Amount'].sum().reset_index()
    df['Academic_Year'] = df['Academic_Year'].astype(int)

    output = df.pivot(index='Name',columns='Academic_Year',values='Credit_Amount').reset_index().fillna(0)

    output = utils.reindex_pivot(output,df.Academic_Year.unique().tolist())

    # Cast to Wide and flip order: https://www.geeksforgeeks.org/how-to-reverse-the-column-order-of-the-pandas-dataframe/
    #values = output.iloc[:,1:]  
    #output = pd.concat([output['Renamer'],values[values.columns[::-1]]],axis=1)

    # Calculate Total column to rank table by
    total = df[['Name','Credit_Amount']].groupby(['Name']).sum().reset_index()
    total.columns = ['Name','Total']
    output.insert(1,"Total",total['Total'])
    output = output.sort_values(by='Total',ascending=False)

    output.columns = output.columns.astype(str)

    if view == 'Table':

        st.dataframe(output.style.format(precision=0,thousands=','))
        
        #utils.AgGrid_default(output,output.columns[output.columns.isin(['Name','Y'])==False],['Name','Total'])

        # Possible future To-Do: load chart from interactive chart
        # Example: https://share.streamlit.io/pablocfonseca/streamlit-aggrid/main/examples/example.py
    
    else:
   
        # Multiselect Donors: https://docs.streamlit.io/library/api-reference/widgets/st.multiselect
        Donors = st.multiselect('Select Donors:',output['Name'].tolist(),output['Name'].tolist()[0:3])

        # Slider select daterange
        # date_range = st.date_input("Date Range:",value=[datetime.strptime('20160101',"%Y%m%d").date(),max(df['Year'])],
        # min_value=min(df['Year']), 
        # max_value=max(df['Year']))

        # Whole year daterange
        date_range = st.slider('', min_value=min(df['Academic_Year']), max_value=max(df['Academic_Year']), value=[min(df['Academic_Year']),max(df['Academic_Year'])], step=1)

        plot_df = df[(df['Academic_Year']>=date_range[0]) & (df['Academic_Year']<=date_range[1])].pivot(index='Academic_Year',columns='Name',values='Credit_Amount').fillna(0)

        fig = px.bar(plot_df[Donors], facet_row="Name", facet_row_spacing=0.02, text_auto='.2s', height=550)

        # hide and lock down axes and remove facet/subplot labels
        fig.update_xaxes(autorange="reversed")
        fig.update_yaxes(title="",matches=None)
        fig.update_layout(annotations=[], overwrite=True)
        fig.update_layout(legend=dict(x=-0.40),margin=dict(r=0,l=30,t=10,b=10))

        # disable the modebar for such a small plot
        st.plotly_chart(fig,use_container_width=True)

st.set_page_config(page_title="Individuals (Annual)", page_icon="👫",layout='wide')

st.title('Individuals Annual')

if 'auth' in st.session_state:
    individuals_annual()
else:
    st.subheader('Error: Go to Home to download data')