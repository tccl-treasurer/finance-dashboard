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

    st.session_state["payslips"] = st.sidebar.radio("Use Payslips:",['Yes','No'],horizontal=True,index=['Yes','No'].index(st.session_state["payslips"]))
    st.session_state["giftaid_choice"] = st.sidebar.radio("Giftaid Choice:",['Accrual','Cash'],horizontal=True)
    utils.giftaid_toggle(st.session_state["giftaid_choice"])

    # Retrive data from session_state
    income = st.session_state.income
    expenses = st.session_state.expenses

    date_range = pd.to_datetime(st.date_input('Date Range',[income.Transaction_Date.min(),datetime(2022,8,31)]))

    recipients = st.multiselect('View Analysis for:',income.Recipient.unique().tolist(),['General','Associate Pastor','Student'])

    #utils.convert_gbpusd(st.session_state["currency_choice"])

    page_view = st.radio('Choose View:',['Total','Income Sources','Income Regularity','Income Recipients','Expenditure Recipients','Giver Count'],horizontal=True) #'Expenditure by Reference'

    if st.session_state["payslips"]=='Yes':

        expenses_tmp = expenses.copy()
        expenses_tmp['Transaction_Date'] = pd.to_datetime(expenses_tmp['Transaction_Date'],format="%d/%m/%Y")
        removed_total = expenses_tmp[(expenses_tmp.Transaction_Date > pd.to_datetime('2019-01-01',format="%Y-%m-%d")) & \
             (expenses_tmp.Reference.isin(['Malc Salary','Dave Salary','Janet Salary','Natalie Salary','Tax']))].Debit_Amount.sum()
        expenses_tmp = expenses_tmp[(expenses_tmp.Transaction_Date < pd.to_datetime('2019-01-01',format="%Y-%m-%d")) | (~expenses_tmp.Reference.isin(['Malc Salary','Dave Salary','Janet Salary','Natalie Salary','Tax']))]
        removed_total = removed_total #+ expenses_tmp.Debit_Amount.sum()
        payslip_df = pd.read_csv('pages/Payslips_2019_202209.csv')
        payslip_df.Date = payslip_df.Date.ffill()
        payslip_df = payslip_df[~payslip_df['Employee Name'].isin(['Process Date:','Employee\nName'])]
        payslip_df = payslip_df.iloc[:,:3]
        payslip_df['Transaction_Date'] = pd.to_datetime(payslip_df['Date'],format="%d/%m/%Y")
        payslip_df['Transaction_Description'] = "Payslip"
        payslip_df['Debit_Amount'] = pd.to_numeric(payslip_df['Gross Pay pre Sacrifice'])
        payslip_df['Category'] = 'Salaries'
        payslip_df['Recipient'] = ['General' if (x=='MT Riley')|(x=='N Halliday') else 'Associate Pastor' if x=='DR Seckington' else 'Farsi' for x in payslip_df['Employee Name']]
        payslip_df['Reference'] =  payslip_df['Employee Name'] + ' Salary'
        payslip_df['Year'] = payslip_df['Transaction_Date'].dt.year
        payslip_df['Academic_Year'] =  payslip_df['Transaction_Date'].map(lambda d: d.year + 1 if d.month > 8 else d.year)
        payslip_df['Month'] = payslip_df['Transaction_Date'].dt.to_period('M')
        payslip_df['Forecast'] = 'History'

        balancing_figure = {}
        balancing_figure['Transaction_Date'] = pd.to_datetime(expenses.Transaction_Date.max())
        balancing_figure['Transaction_Description'] = "Balancing Figure"
        balancing_figure['Debit_Amount'] =  payslip_df.Debit_Amount.sum()-removed_total
        balancing_figure['Reference'] = 'Tax Balance'
        balancing_figure['Category'] = 'Salaries'
        balancing_figure['Recipient'] = 'General'
        balancing_figure['Year'] = balancing_figure['Transaction_Date'].year
        balancing_figure['Month'] = balancing_figure['Transaction_Date'].to_period('M')
        balancing_figure['Forecast'] = 'History'
        balancing_figure['Academic_Year'] = np.where(balancing_figure['Transaction_Date'].month > 8, balancing_figure['Transaction_Date'].year + 1 , balancing_figure['Transaction_Date'].year).item()
        balancing_figure = {k:[v] for k,v in balancing_figure.items()}  # WORKAROUND
        balancing_figure = pd.DataFrame(balancing_figure)

        expenses = pd.concat([expenses_tmp,payslip_df[['Transaction_Date', 'Transaction_Description', 'Debit_Amount',
       'Reference', 'Category', 'Recipient', 'Year', 'Month', 'Forecast','Academic_Year']],balancing_figure])

    income = income[(income.Recipient.isin(recipients)) & \
                    (income.Transaction_Date >= date_range[0]) & \
                    (income.Transaction_Date <= date_range[1])]

    expenses = expenses[expenses.Recipient.isin(recipients) & \
                       (expenses.Transaction_Date >= date_range[0]) & \
                       (expenses.Transaction_Date <= date_range[1])] 

    if page_view=='Total':

        #Define Years
        annual_income = income[['Academic_Year','Income_Amount']].groupby(['Academic_Year']).sum()
        annual_income = annual_income.rename(columns={'Income_Amount':'Income'})

        annual_expenses = expenses[['Academic_Year','Debit_Amount']].groupby(['Academic_Year']).sum()
        annual_expenses = annual_expenses.rename(columns={'Debit_Amount':'Expenses'})

        annual_data = annual_income.join(annual_expenses).reset_index()
        annual_data_melt = pd.melt(annual_data, id_vars = ['Academic_Year'], var_name='Group')
        annual_data['Delta'] = annual_data['Income'] - annual_data['Expenses']

        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(annual_data_melt, x="Academic_Year", y="value", color='Group', barmode='group', labels={
                     "value": "Income / Expenditure (£)"},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))
        
        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(annual_data,['Income','Expenses','Delta'],['Academic_Year'])

    elif page_view=='Income Sources':

        # Calculate Income by Year & Source Type
        income_type = income[['Academic_Year','Source','Income_Amount']].groupby(['Source','Academic_Year']).sum().reset_index()

        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(income_type.sort_values(['Academic_Year','Source'],ascending=False), x="Academic_Year", y="Income_Amount", color='Source', labels={
                     "Income_Amount": "Income"},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

        income_type_pivot = income_type.pivot(index='Source',columns='Academic_Year',values='Income_Amount').reset_index().fillna(0)
        income_type_pivot = utils.reindex_pivot(income_type_pivot,income_type.Academic_Year.unique().tolist())
        income_type_pivot.columns = income_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(income_type_pivot,income_type_pivot.columns[income_type_pivot.columns!='Source'],['Source'])

    elif page_view=='Income Regularity':

        # Calculate Income by Year & Source Type
        income_type = income[['Academic_Year','Regularity','Income_Amount']].groupby(['Regularity','Academic_Year']).sum().reset_index()

        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(income_type.sort_values(['Academic_Year','Regularity']), x="Academic_Year", y="Income_Amount", color='Regularity', labels={
                     "Income_Amount": "Income"},height=400)

        income_type['Academic_Year'] = income_type['Academic_Year'].astype(str)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

        income_type_pivot = income_type.pivot(index='Regularity',columns='Academic_Year',values='Income_Amount').reset_index().fillna(0)
        #income_type_pivot = utils.reindex_pivot(income_type_pivot,income_type.Academic_Year.astype(str).unique().tolist())
        income_type_pivot.columns = income_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(income_type_pivot,income_type_pivot.columns[income_type_pivot.columns!='Regularity'],['Regularity'])

    elif page_view=='Income Recipients':

        # Calculate Income by Year & Source Type
        income_type = income[['Academic_Year','Recipient','Income_Amount']].groupby(['Recipient','Academic_Year']).sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(income_type, x="Academic_Year", y="Income_Amount", color='Recipient', labels={
                     "Income_Amount": "Income"},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

        income_type_pivot = income_type.pivot(index='Recipient',columns='Academic_Year',values='Income_Amount').reset_index().fillna(0)
        income_type_pivot = utils.reindex_pivot(income_type_pivot,income_type.Academic_Year.unique().tolist())
        income_type_pivot.columns = income_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=True)
        utils.AgGrid_default(income_type_pivot,income_type_pivot.columns[income_type_pivot.columns!='Category'],['Recipient'])

    elif page_view=='Expenditure Recipients':

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

    elif page_view=='Giver Count':

        #Define Years
        tmp = income[['Name','Academic_Year','Source','Income_Amount']].groupby(['Academic_Year','Source','Name']).count().reset_index()
        tmp = tmp[tmp.Income_Amount>2]
        giver_count = tmp[['Academic_Year','Source','Name']].groupby(['Academic_Year','Source']).count().reset_index()
        giver_count.columns = ['Academic_Year','Source','Count']
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(giver_count, x="Academic_Year", y="Count", color='Source', labels={
                     "Count": "Number of Givers"},height=400)
        
        # Legend positioning: https://plotly.com/python/legend/
        fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))
        
        st.plotly_chart(fig, use_container_width=True)
        st.write('Counts only 2+ donations per year. Counts each Direct Debit as 1.')
        utils.AgGrid_default(giver_count)

st.set_page_config(page_title="Overall", page_icon="📈",layout='centered')

st.title('Overall')

if 'auth' in st.session_state:
    overall_page()
else:
    st.subheader('Error: Go to Home to download data')
