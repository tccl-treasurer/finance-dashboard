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

def overall_page():

    use_payslips = st.sidebar.radio("Use Payslips:",['Yes','No'],horizontal=True,index=['Yes','No'].index(st.session_state["payslips"]))
    st.session_state["giftaid_choice"] = st.sidebar.radio("Giftaid Choice:",['Accrual','Cash'],horizontal=True)
    st.session_state["year_choice"] = st.sidebar.radio("Year Choice:",['Tax','Academic','Calendar'],horizontal=False)
    utils.giftaid_toggle(st.session_state["giftaid_choice"])

    # Retrive data from session_state
    income = st.session_state.income
    expenses = st.session_state.expenses

    col1 , col2, col3 = st.columns([1,3,1])

    with col1:
        date_range = pd.to_datetime(st.date_input('Date Range',[datetime(2017,9,1),income.Transaction_Date.max()]))

    with col2:
        recipients = st.multiselect('View Analysis for:',income.Recipient.unique().tolist(),['International','Associate Pastor','Student'])

    # with col3:
    #     year_divider = st.number_input('Year Divider (0=Jan, 1=Feb..)',value=8)

    #utils.convert_gbpusd(st.session_state["currency_choice"])

    page_view = st.radio('Choose View:',['Total','Income Sources','Income Regularity','Income Recipients', \
                                         'Expenditure Recipients','Expenditure References','Giver Count'],horizontal=True) #'Expenditure by Reference'

    if use_payslips=='Yes':

        expenses_tmp = expenses.copy()
        #expenses_tmp['Transaction_Date'] = pd.to_datetime(expenses_tmp['Transaction_Date'],format="%d/%m/%Y")
        removed_total = expenses_tmp[(expenses_tmp.Transaction_Date > pd.to_datetime('2019-01-30',format="%Y-%m-%d")) & \
             (expenses_tmp.Transaction_Date < pd.to_datetime('2023-09-01',format="%Y-%m-%d")) & \
             (expenses_tmp.Reference.isin(['Malc Salary','Dave Salary','Janet Salary','Natalie Salary','Tax']))].Debit_Amount.sum()
        expenses_tmp = expenses_tmp[(expenses_tmp.Transaction_Date < pd.to_datetime('2019-01-01',format="%Y-%m-%d")) | (~expenses_tmp.Reference.isin(['Malc Salary','Dave Salary','Janet Salary','Natalie Salary','Tax']))]
        expenses_tmp['Year'] = expenses_tmp['Transaction_Date'].apply(lambda x: x.year)
        removed_total = removed_total #+ expenses_tmp.Debit_Amount.sum()
        payslip_df = pd.read_csv('pages/Payslips_2019_202308.csv')
        payslip_df.Date = payslip_df.Date.ffill()
        payslip_df = payslip_df[~payslip_df['Employee Name'].isin(['Process Date:','Employee\r\nName'])]
        payslip_df = payslip_df.iloc[:,:3]
        payslip_df['Transaction_Date'] = pd.to_datetime(payslip_df['Date'],format="%d/%m/%Y")
        #payslip_df = payslip_df[payslip_df.Transaction_Date<'2022-09-01']
        payslip_df['Transaction_Description'] = "Payslip"
        payslip_df['Debit_Amount'] = pd.to_numeric(payslip_df['Gross Pay pre Sacrifice'],errors='coerce')
        payslip_df['Category'] = 'Salaries'
        payslip_df['Recipient'] = ['International' if (x=='MT Riley')|(x=='N Halliday') else 'Associate Pastor' if x=='DR Seckington' else 'Farsi' for x in payslip_df['Employee Name']]
        payslip_df['Reference'] = payslip_df['Employee Name'] + ' Salary'
        payslip_df['Calendar_Year'] = payslip_df['Transaction_Date'].apply(lambda x: x.year)
        #payslip_df['Academic_Year'] = payslip_df['Transaction_Date'].map(lambda d: d.year + 1 if d.month > 8 else d.year)
        payslip_df['Academic_Year'] = utils.academic_year(payslip_df['Transaction_Date'])
        payslip_df['Tax_Year'] = utils.tax_year(payslip_df['Transaction_Date'])
        #payslip_df['Tax_Year'] = payslip_df['Transaction_Date'].apply(lambda x: utils.tax_year(x))

        balancing_figure = {}
        balancing_figure['Transaction_Date'] = pd.to_datetime(payslip_df.Transaction_Date.max())
        balancing_figure['Transaction_Description'] = "Balancing Figure"
        balancing_figure['Debit_Amount'] =  payslip_df.Debit_Amount.sum()-removed_total
        balancing_figure['Reference'] = 'Tax Balance'
        balancing_figure['Category'] = 'Salaries'
        balancing_figure['Recipient'] = 'International'
        balancing_figure['Year'] = balancing_figure['Transaction_Date'].year
        #balancing_figure['Academic_Year'] = np.where(balancing_figure['Transaction_Date'].month > 8, balancing_figure['Transaction_Date'].year + 1 , balancing_figure['Transaction_Date'].year).item()
        balancing_figure['Academic_Year'] = utils.academic_year(pd.Series(balancing_figure['Transaction_Date']))[0]
        balancing_figure['Tax_Year'] = utils.tax_year(pd.Series(balancing_figure['Transaction_Date']))[0]
        balancing_figure['Calendar_Year'] = balancing_figure['Transaction_Date'].year
        balancing_figure = {k:[v] for k,v in balancing_figure.items()}  # WORKAROUND
        balancing_figure = pd.DataFrame(balancing_figure)

        expenses = pd.concat([expenses_tmp,payslip_df[['Transaction_Date', 'Transaction_Description', 'Debit_Amount',
       'Reference', 'Category', 'Recipient', 'Academic_Year','Tax_Year','Calendar_Year']],balancing_figure])

    income = income[(income.Recipient.isin(recipients)) & \
                    (income.Transaction_Date >= date_range[0]) & \
                    (income.Transaction_Date <= date_range[1])]

    expenses = expenses[expenses.Recipient.isin(recipients) & \
                       (expenses.Transaction_Date >= date_range[0]) & \
                       (expenses.Transaction_Date <= date_range[1])] 

    # if 'Weekend Away' not in recipients:
    #     expenses = expenses[expenses.Category!='Weekend Away']

    if st.session_state["year_choice"]=='Tax':
        income['Group_Year'] = income['Tax_Year']
        expenses['Group_Year'] = expenses['Tax_Year']
    elif st.session_state["year_choice"]=='Academic':
        income['Group_Year'] = income['Academic_Year']
        expenses['Group_Year'] = expenses['Academic_Year']
    else:
        income['Group_Year'] = income['Calendar_Year']
        expenses['Group_Year'] = expenses['Calendar_Year']

    if page_view=='Total':

        #Define Years
        annual_income = income.groupby('Group_Year')['Income_Amount'].sum().reset_index()
        annual_income = annual_income.rename(columns={'Income_Amount':'Income'})

        annual_expenses = expenses.groupby('Group_Year')['Debit_Amount'].sum().reset_index()
        annual_expenses = annual_expenses.rename(columns={'Debit_Amount':'Expenses'})

        annual_data = pd.merge(annual_income,annual_expenses,on='Group_Year')
        annual_data_melt = pd.melt(annual_data, id_vars = ['Group_Year'], var_name='Group')
        annual_data['Delta'] = annual_data['Income'] - annual_data['Expenses']

        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(annual_data_melt, x="Group_Year", y="value", color='Group', barmode='group', labels={
                     "value": "Income / Expenditure (£)","Group_Year":""},text="value",
                     color_discrete_sequence=['#1054da','#ea5e5b','#82c7a5','#FFFFFF'],height=450,width=900)

        fig = utils.format_plotly(fig,x=1/3,y=-0.1)

        st.plotly_chart(fig, use_container_width=False,theme=None)
        st.dataframe(annual_data.style.format(precision=0,thousands=' '))

    elif page_view=='Income Sources':

        # Calculate Income by Year & Source Type
        income_type = income.groupby(['Source','Group_Year'])['Income_Amount'].sum().reset_index()

        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(income_type.sort_values(['Group_Year','Source'],ascending=False), x="Group_Year", y="Income_Amount", color='Source', labels={
                     "Income_Amount": "Income","Group_Year":""},color_discrete_sequence=['#1054da','#ea5e5b','#82c7a5','#FFFFFF']
                     ,height=450,width=900)

        fig = utils.format_plotly(fig,x=1/3,y=-0.1)

        income_type_pivot = income_type.pivot(index='Source',columns='Group_Year',values='Income_Amount').reset_index().fillna(0)
        income_type_pivot = utils.reindex_pivot(income_type_pivot,income_type.Group_Year.unique().tolist())
        income_type_pivot.columns = income_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=False,theme=None)
        st.dataframe(income_type_pivot.style.format(precision=1,thousands=' '))
        income_type_name = income.groupby(['Source','Group_Year','Name'])['Income_Amount'].sum().reset_index()
        income_type_name_pivot = income_type_name.pivot(index=['Name','Source'],columns='Group_Year',values='Income_Amount').reset_index().fillna(0)
        income_type_name_pivot['Delta'] = income_type_name_pivot.iloc[:,-1] - income_type_name_pivot.iloc[:,-2]
        st.dataframe(income_type_name_pivot.style.format(precision=1,thousands=' '),use_container_width=True)
        # utils.AgGrid_default(income_type_pivot,income_type_pivot.columns[income_type_pivot.columns!='Source'],['Source'])

    elif page_view=='Income Regularity':

        # Calculate Income by Year & Source Type
        income_type = income.groupby(['Regularity','Group_Year'])['Income_Amount'].sum().reset_index()

        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(income_type.sort_values(['Group_Year','Regularity']), x="Group_Year", y="Income_Amount", color='Regularity', labels={
                     "Income_Amount": "Income"},color_discrete_sequence=['#1054da','#ea5e5b','#82c7a5','#FFFFFF']
                     ,height=450,width=900)

        income_type['Group_Year'] = income_type['Group_Year'].astype(str)

        fig = utils.format_plotly(fig,x=1/3,y=-0.1)

        income_type_pivot = income_type.pivot(index='Regularity',columns='Group_Year',values='Income_Amount').reset_index().fillna(0)
        #income_type_pivot = utils.reindex_pivot(income_type_pivot,income_type.Group_Year.astype(str).unique().tolist())
        income_type_pivot.columns = income_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=False,theme=None)
        st.dataframe(income_type_pivot.style.format(precision=1,thousands=' '))
        # utils.AgGrid_default(income_type_pivot,income_type_pivot.columns[income_type_pivot.columns!='Source'],['Source'])

    elif page_view=='Income Recipients':

        # Calculate Income by Year & Source Type
        income_type = income.groupby(['Recipient','Group_Year'])['Income_Amount'].sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(income_type, x="Group_Year", y="Income_Amount", color='Recipient', labels={
                     "Income_Amount": "Income"},color_discrete_sequence=['#1054da','#ea5e5b','#82c7a5','#FFFFFF']
                     ,height=450,width=900)
        
        fig = utils.format_plotly(fig,x=0.25)

        income_type_pivot = income_type.pivot(index='Recipient',columns='Group_Year',values='Income_Amount').reset_index().fillna(0)
        income_type_pivot = utils.reindex_pivot(income_type_pivot,income_type.Group_Year.unique().tolist())
        income_type_pivot.columns = income_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=False,theme=None)
        st.dataframe(income_type_pivot.style.format(precision=1,thousands=' '))
        # utils.AgGrid_default(income_type_pivot,income_type_pivot.columns[income_type_pivot.columns!='Source'],['Source'])

    elif page_view=='Expenditure Recipients':

        # Calculate Income by Year & Source Type
        expenses_type = expenses.groupby(['Category','Group_Year'])['Debit_Amount'].sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(expenses_type, x="Group_Year", y="Debit_Amount", color='Category', labels={
                     "Debit_Amount": "Expenses","Group_Year":""},color_discrete_sequence=['#1054da','#ea5e5b','#82c7a5','#FFFFFF']
                     ,height=450,width=900)
        
        fig = utils.format_plotly(fig,x=0.1,y=-0.1)

        expenses_type_pivot = expenses_type.pivot(index='Category',columns='Group_Year',values='Debit_Amount').reset_index().fillna(0)
        expenses_type_pivot = utils.reindex_pivot(expenses_type_pivot,expenses_type.Group_Year.unique().tolist())
        expenses_type_pivot.columns = expenses_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=False,theme=None)
        st.dataframe(expenses_type_pivot.style.format(precision=1,thousands=' '))
        #utils.AgGrid_default(expenses_type_pivot,expenses_type_pivot.columns[expenses_type_pivot.columns!='Category'],['Category'])

        st.dataframe(expenses[(expenses.Academic_Year==2023) & (expenses.Category=='Salaries') ].style.format(precision=1,thousands=' '))

    elif page_view=='Expenditure References':

        categories = st.multiselect('View Category:',expenses.Category.unique().tolist(),['Expenses'])

        # Calculate Income by Year & Source Type
        expenses_type = expenses[expenses.Category.isin(categories)].groupby(['Reference','Group_Year'])['Debit_Amount'].sum().reset_index()
        
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(expenses_type, x="Group_Year", y="Debit_Amount", color='Reference', labels={
                     "Debit_Amount": "Expenses"},color_discrete_sequence=['#1054da','#ea5e5b','#82c7a5','#FFFFFF']
                     ,height=450,width=900)
        
        fig = utils.format_plotly(fig)

        expenses_type_pivot = expenses_type.pivot(index='Reference',columns='Group_Year',values='Debit_Amount').reset_index().fillna(0)
        expenses_type_pivot = utils.reindex_pivot(expenses_type_pivot,expenses_type.Group_Year.unique().tolist())
        expenses_type_pivot.columns = expenses_type_pivot.columns.astype(str)

        st.plotly_chart(fig, use_container_width=False,theme=None)
        st.dataframe(expenses_type_pivot.style.format(precision=1,thousands=' '))
        #utils.AgGrid_default(expenses_type_pivot,expenses_type_pivot.columns[expenses_type_pivot.columns!='Category'],['Category'])

    # elif page_view=='Expenditure by Reference':

    #     # Calculate Income by Year & Source Type
    #     expenses_type = expenses[['Group_Year','Reference','Debit_Amount']].groupby(['Reference','Group_Year']).sum().reset_index()
        
    #     # Plotly bar chart: https://plotly.com/python/bar-charts/
    #     fig = px.bar(expenses_type, x="Group_Year", y="Debit_Amount", color='Reference', labels={
    #                  "Debit_Amount": "Expenses"},height=400)
        
    #     # Legend positioning: https://plotly.com/python/legend/
    #     fig = fig.update_layout(legend=dict(orientation="h", y=-0.15, x=0.15))

    #     expenses_type_pivot = expenses_type.pivot(index='Reference',columns='Group_Year',values='Debit_Amount').reset_index().fillna(0)
    #     expenses_type_pivot = utils.reindex_pivot(expenses_type_pivot,expenses_type.Group_Year.unique().tolist())
    #     expenses_type_pivot.columns = expenses_type_pivot.columns.astype(str)

    #     st.plotly_chart(fig, use_container_width=False,theme=None)
    #     utils.AgGrid_default(expenses_type_pivot,expenses_type_pivot.columns[expenses_type_pivot.columns!='Reference'],['Reference'])

    elif page_view=='Giver Count':

        #Define Years
        tmp = income[income['Transaction_Description']!='Weekend Away'].groupby(['Group_Year','Source','Name'])['Income_Amount'].count().reset_index()

        #xero['Congregation'] = ['Weekend Away' if x==263 else y for x , y in zip(xero['Account Code'],xero['Congregation'])]

        tmp = tmp[tmp.Income_Amount>2]
        
        giver_count = tmp.groupby(['Group_Year','Source'])['Name'].count().reset_index()


        giver_count.columns = ['Group_Year','Source','Count']
        
        #st.bar_chart(giver_count,x="Group_Year", y="Count",color=['#7c98cb','#ea5e5b'],height=400)
        # Plotly bar chart: https://plotly.com/python/bar-charts/
        fig = px.bar(giver_count, x="Group_Year", y="Count", color='Source', labels={
                     "Count": "Number of Givers"},height=400
                     ,color_discrete_sequence=['#1054da','#ea5e5b','#82c7a5','#FFFFFF']
                     )
        
        fig = utils.format_plotly(fig)
        
        st.plotly_chart(fig, use_container_width=False, theme=None)
        st.write('Counts only 2+ donations per year. Counts each Direct Debit as 1.')

        st.dataframe(giver_count.style.format(precision=1,thousands=' '))
        st.dataframe(tmp[(tmp.Source=='Internal') & (tmp.Group_Year==2023)])
        # Malc has 15/16
        # Anusha external
        # Abhishek x2
        # Emily Driver -> External
        # Myung twice
        # Oliver twice
        # Rob twice
        # Amy twice

        # utils.AgGrid_default(giver_count)

    st.dataframe(income[income.Group_Year==2023])
    st.dataframe(expenses[expenses.Group_Year==2023])

st.set_page_config(page_title="Overall", page_icon="📈",layout='wide')

st.title('Overall')

if 'auth' in st.session_state:
    overall_page()
else:
    st.subheader('Error: Go to Home to download data')
