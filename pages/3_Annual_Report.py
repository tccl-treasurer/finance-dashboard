import numpy as np
import pandas as pd
import streamlit as st
import utils

st.set_page_config(layout="wide") 

def annual_report():

    st.title("Annual Report Breakdown")

    report_df = st.session_state['xero_data']
    report_df['Calendar_Year'] = np.where(((report_df.Date.dt.month==4) & (report_df.Date.dt.day>5)) \
                                          | (report_df.Date.dt.month>4),0,1) + report_df.Date.dt.year
    
    years = st.multiselect('Select Years to View',report_df['Calendar_Year'].unique().tolist(),[2023,2024])
    report_df = report_df[report_df.Calendar_Year.isin(years)]

    st.subheader('Income')
    income, height, income_raw = utils.report_table(report_df,1)
    st.dataframe(income,use_container_width=True,height=height)
    
    st.subheader('Expenses')
    expenses, height, expenses_raw = utils.report_table(report_df,-1)
    st.dataframe(expenses,use_container_width=True,height=height)

    st.subheader('Export to CSV')
    df = pd.concat([income_raw,expenses_raw])
    csv = utils.convert_df(df)
    st.download_button(
        "Download",csv,"income.csv","text/csv",key='download-csv'
    )

    st.subheader('Audit Section')
    with st.form('Dive'):
        choice = st.selectbox('Choose an Account Code to view transactions',report_df['*Name'].sort_values().unique().tolist(),0)
        submit = st.form_submit_button()
    
        if submit:
            cols = ['Date','Name','AccountCode','Directional_Total','BankTransactionID']
            st.dataframe(report_df[report_df['*Name']==choice][cols])

annual_report()