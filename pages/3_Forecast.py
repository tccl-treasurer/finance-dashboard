
import time
import numpy as np
import pandas as pd
import streamlit as st
from streamlit.hello.utils import show_code
import utils as utils
from datetime import datetime, timedelta
import time
import altair as alt
import os
import plotly.express as px

st.set_page_config(layout="wide") 

def forecast():

    st.title("Forecast")

    giftaid = st.toggle('Giftaid',True) 

    st.subheader('Income')

    try:
        df = st.session_state['xero_data']
    except:
        st.error("No Data Downloaded. Please return to Landing Page tab to Download.")
        st.stop()

    Congregations_f = st.multiselect('Select Congregations:',df['Congregation'].dropna().unique(),default=['International'])
    df = df[df.Congregation.isin(Congregations_f)]

    if giftaid:
        df['Total'] = df['SubTotal'] * df['Giftaid_Multiplier']
    else:
        df['Total'] = df['SubTotal']

    #st.dataframe(forecast_df.head())
    income_forecast = df[df.AccountCode.between(100,259)] 
    income_forecast['Time_Group'] = income_forecast.Date.dt.to_period('M')
    pivot_income = income_forecast.groupby(['Name','Congregation','Time_Group'])['Total'].sum().reset_index()
    pivot_income = pivot_income.pivot_table(index=['Name','Congregation'],columns='Time_Group',values='Total')

    file_path = 'monthly_income_forecast.parquet'
    if os.path.exists(file_path):
        mf_df = pd.read_parquet(file_path)
        pivot_income = pd.merge(pivot_income.reset_index(),mf_df.reset_index(names='Name'),on=['Name','Congregation'],how='left')
        #add means to missing Names
        pivot_income['Monthly Forecast'] = np.where(pivot_income['Monthly Forecast'].isnull(),
                                                    pivot_income.iloc[:,-12:].fillna(0).mean(axis=1),
                                                    pivot_income['Monthly Forecast'])
    else:
        pivot_income['Monthly Forecast'] = pivot_income.iloc[:,-12:].fillna(0).mean(axis=1) 

    pivot_income = pivot_income.reset_index().set_index(['Name','Congregation','Monthly Forecast'])
    pivot_income = pivot_income[pivot_income.columns[::-1]].reset_index(level=1) #show months in reverse order
    pivot_income = pivot_income.sort_values(by='Monthly Forecast',ascending=False)

    st.write('**Monthly Income Forecasts**')

    all_income_forecasts = {}
    for cong in Congregations_f:
        st.subheader(f'{cong}',divider=True)
        tmp_income_forecast = pivot_income[pivot_income.Congregation==cong].drop(columns='Congregation').reset_index().set_index('Name')
        with st.container(height=400):
            tmp_income_forecast_dict = {}
            for nm in tmp_income_forecast.index:
                col1, col2 = st.columns([1,5])
                # st.write(pivot_income.loc[nm][['Monthly Forecast']].iloc[0])
                with col1:
                    tmp_income_forecast_dict[nm] = st.number_input(label=f'{nm} ({cong})',value=tmp_income_forecast[['Monthly Forecast']].loc[nm].iloc[0])
                with col2:
                    st.dataframe(pd.DataFrame(tmp_income_forecast.loc[nm].iloc[1:]).T,use_container_width=False,hide_index=True)
            all_income_forecasts[cong] =  pd.DataFrame.from_dict(tmp_income_forecast_dict,orient='index',columns=['Monthly Forecast'])          
            all_income_forecasts[cong]['Congregation'] = cong

    all_income_forecasts = pd.concat(all_income_forecasts.values(),axis=0)
    
    if st.button('Save Income Forecasts'):
        all_income_forecasts.to_parquet(file_path)
        st.success('Saved')

    monthly_income = all_income_forecasts['Monthly Forecast'].sum()

    st.write('**One-off Income Forecasts**')

    mo_ahead_3 = datetime.today() + timedelta(days=90)
    try:
        one_off_income_forecast = pd.read_parquet('one_off_income_forecast_edited.parquet')
    except:
        check = st.empty()
        with check:
            st.info('No previous one off forecasts found')
            time.sleep(0.5)
        check.empty()
        one_off_income_forecast = pd.DataFrame(data={'Name':['Joe Bloggs','Joe Dane']
                                    ,'Date':[mo_ahead_3,mo_ahead_3],'Total':[0.00,0.00]})

    one_off_income_forecast_edited = st.data_editor(one_off_income_forecast, num_rows="dynamic")
    one_off_income_forecast_edited.to_parquet('one_off_income_forecast_edited.parquet')
    one_off_income_df = one_off_income_forecast_edited[['Date','Total']].set_index('Date')

    st.subheader('Expenses',divider=True)

    expense_forecast = df[df.AccountCode>300]
    expense_forecast = expense_forecast[expense_forecast.AccountCode!=4105] #remove weekend away
    expense_category1 = utils.expense_category1()
    expense_forecast['Category'] = expense_forecast.AccountCode.map(expense_category1)
    expense_forecast['Time_Group'] = expense_forecast.Date.dt.to_period('M')
    expense_forecast = expense_forecast.groupby(['Time_Group','Category','Congregation'])['Total'].sum().reset_index()
    pivot_expense = expense_forecast.groupby(['Category','Congregation','Time_Group'])['Total'].sum().reset_index() 
    pivot_expense = pivot_expense.pivot_table(index=['Category','Congregation'],columns='Time_Group',values='Total')
   
    file_path = 'monthly_expense_forecast.parquet'
    if os.path.exists(file_path):
        mf_df = pd.read_parquet(file_path)
        pivot_expense = pd.merge(pivot_expense.reset_index(),mf_df.reset_index(names='Category')
                                 ,on=['Category','Congregation'],how='left')
        #add means to missing Names
        pivot_expense['Monthly Forecast'] = np.where(pivot_expense['Monthly Forecast'].isnull(),
                                                    pivot_expense.iloc[:,-12:].fillna(0).mean(axis=1),
                                                    pivot_expense['Monthly Forecast'])
    else:
        pivot_expense['Monthly Forecast'] = pivot_expense.iloc[:,-12:].fillna(0).mean(axis=1) 
 
    pivot_expense = pivot_expense.reset_index().set_index(['Category','Congregation','Monthly Forecast'])
    pivot_expense = pivot_expense[pivot_expense.columns[::-1]].reset_index(level=1) #show months in reverse order
    pivot_expense = pivot_expense.sort_values(by='Monthly Forecast',ascending=False)

    st.write('**Monthly Expense Forecasts**: Enter Values as positive')
    
    all_expense_forecasts = {}
    for cong in Congregations_f:
        st.subheader(f'{cong}',divider=True)
        tmp_expense_forecast = pivot_expense[pivot_expense.Congregation==cong].drop(columns='Congregation').reset_index().set_index('Category')
        with st.container(height=400):
            tmp_expense_forecast_dict = {}
            for nm in tmp_expense_forecast.index:
                col1, col2 = st.columns([1,5])
                # st.write(pivot_expense.loc[nm][['Monthly Forecast']].iloc[0])
                with col1:
                    tmp_expense_forecast_dict[nm] = st.number_input(label=f'{nm} ({cong})',value=tmp_expense_forecast[['Monthly Forecast']].loc[nm].iloc[0])
                with col2:
                    st.dataframe(pd.DataFrame(tmp_expense_forecast.loc[nm].iloc[1:]).T,use_container_width=False,hide_index=True)
            all_expense_forecasts[cong] =  pd.DataFrame.from_dict(tmp_expense_forecast_dict,orient='index',columns=['Monthly Forecast'])          
            all_expense_forecasts[cong]['Congregation'] = cong

    all_expense_forecasts = pd.concat(all_expense_forecasts.values(),axis=0)
    
    if st.button('Save Expense Forecasts'):
        all_expense_forecasts.to_parquet(file_path)
        st.success('Saved')

    monthly_expenses = all_expense_forecasts['Monthly Forecast'].sum()

    st.write('**One-off Expense Forecasts**: Enter Values as positive')

    try:
        one_off_expense_forecast = pd.read_parquet('one_off_expense_forecast_edited.parquet')
    except:
        check = st.empty()
        with check:
            st.info('No previous one off forecasts found')
            time.sleep(0.5)
        check.empty()
        one_off_expense_forecast = pd.DataFrame(data={'Category':['Venue Hire','Christmas Event']
                                                      ,'Congregation':['International','International']
                                    ,'Date':[mo_ahead_3,mo_ahead_3],'Total':[0.00,0.00]})

    one_off_expense_forecast_edited = st.data_editor(one_off_expense_forecast, num_rows="dynamic")
    one_off_expense_forecast_edited.to_parquet('one_off_expense_forecast_edited.parquet')
    one_off_expense_df = one_off_expense_forecast_edited[['Date','Total']].set_index('Date')
    one_off_expense_df *= -1

    col1, col2 = st.columns([1,1])

    with col1:
        current_balance = df.Directional_Total.sum()
        st.metric('Estimated Current Balance',value=current_balance)
    with col2:
        balance_override = st.number_input('Override Current Balance',value=None)

    if balance_override is not None:
        current_balance = balance_override

    st.subheader('Monthly Forecast')

    today = datetime.now()
    end_of_current_month = pd.offsets.MonthEnd().rollforward(today.date())

    month_index = [end_of_current_month + pd.DateOffset(months=i) for i in range(13)]

    monthly_income_df = pd.DataFrame(index=month_index[1:],data={'Total':[monthly_income]*12})
    monthly_expense_df = pd.DataFrame(index=month_index[1:],data={'Total':[-monthly_expenses]*12})
    
    current_df = pd.DataFrame(index=[end_of_current_month],data={'Total':current_balance})
    forecast_df = pd.concat([current_df,monthly_income_df,monthly_expense_df,
                             one_off_income_df,one_off_expense_df],axis=0)

    forecast_df['Month'] = forecast_df.index.to_period('M')
    forecast_df = forecast_df.groupby('Month').sum().reset_index()
    forecast_df['Date'] = forecast_df['Month'].astype('str')
    forecast_df['Balance'] = forecast_df['Total'].cumsum()

    plot_df = pd.concat([monthly_income_df.rename(columns={'Total':'Income'}),-monthly_expense_df.rename(columns={'Total':'Expenses'})],axis=1)
    fig = px.bar(plot_df,x=plot_df.index,y=plot_df.columns,text_auto='.0f',barmode='group')
    st.plotly_chart(fig,use_container_width=True)

    fig = px.bar(forecast_df,x='Date',y='Balance',text_auto='.0f')
    st.plotly_chart(fig,use_container_width=True)

    st.dataframe(forecast_df[['Date','Total','Balance']])
    # get current balance (override-able?)



forecast()