import streamlit as st
from streamlit.logger import get_logger
import utils as utils
import json
import requests
import webbrowser
import base64
from io import StringIO
import numpy as np
import pandas as pd
import altair as alt
import os
from plotly import express as px
import utils as utils


def summary():
    
    st.set_page_config(page_title="TC Finance Dashboard",layout="wide")

    st.title("TC Church Finances")

    try:
        df = st.session_state['xero_data']
    except:
        st.error("No Data Downloaded. Please return to Landing Page tab to Download.")
        st.stop()

    if len(df)==0:
        st.stop()

    #st.dataframe(df)
    col1, col2, col3 = st.columns([2.5,1.5,1])
    with col1:
        time_group = st.radio('Choose Time Grouping',['Calendar Year','Tax Year','Academic Year','Quarter','Month','Half',None],horizontal=True)
    
    with col2:
        df.Date = pd.to_datetime(df.Date,format='%Y/%m/%d')
        date_range = st.date_input('Date Range',[pd.to_datetime('2022-01-01'),
                                                df.Date.max()])
        date_range = [pd.to_datetime(x) for x in date_range]
    
    with col3:
        #st.markdown('#### ')
        giftaid = st.toggle('Giftaid',True)
        weekend_away = st.toggle('Exclude Weekend Away',True)

    df = df[df.Date.between(date_range[0],date_range[1])]

    if time_group=='Calendar Year':
        df['Time_Group'] = df['Year']
    elif time_group=='Quarter':
        df['Time_Group'] = df['Quarter']
    elif time_group=='Tax Year':
        df['Time_Group'] = df['Tax_Year']
    elif time_group=='Academic Year':
        df['Time_Group'] = df['Academic_Year']
    elif time_group=='Month':
        df['Time_Group'] = df.Date.dt.to_period('M')
    elif time_group=='Half':
        df['Time_Group']= np.where(df['Date'].dt.month<7,
                                   df['Date'].dt.year.astype('string')+'H1',
                                   df['Date'].dt.year.astype('string')+'H2')
    else:
        df['Time_Group'] = 'All'

    if giftaid:
        df['Total'] = df['SubTotal'] * df['Giftaid_Multiplier']
    else:
        df['Total'] = df['SubTotal']

    if weekend_away:
        df = df[~df.AccountCode.isin([263,4105])]

    Congregations = st.multiselect('Select Congregations:',df['Congregation'].dropna().unique(),default=df['Congregation'].dropna().unique())

    with st.expander('Check Categories'):

        col1, col2 = st.columns([1,1])
        
        df_ex = df[~df['Congregation'].isin(Congregations)][['*Code','*Name','Congregation']].drop_duplicates()
        with col1:
            st.write("The following accounts have been excluded:")
            st.dataframe(df_ex.set_index('*Code').sort_index())
        
        df_inc = df[df['Congregation'].isin(Congregations)][['*Code','*Name','Congregation']].drop_duplicates()
        with col2:
            st.write("The following accounts are still included:")
            st.dataframe(df_inc[['*Code','*Name','Congregation']].drop_duplicates().set_index('*Code').sort_index())

    df = df[df['Congregation'].isin(Congregations)]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Income vs Expenses over Time',divider='blue')

        plot_df = df.groupby(['Time_Group','Classification'])['Total'].sum().reset_index()
        plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

        fig = px.bar(plot_df,x='Time_Group',y='Total',color='Classification',text_auto=',.0f',barmode='group')
        st.plotly_chart(fig,use_container_width=True)
        # utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Classification',
        #            xOffset='Classification',sort_list=['Income','Expenses'])
        
    with col2:
        st.subheader('Number of Givers',divider='blue')

        plot_df = df[df.AccountCode.between(100,235)]
        plot_df = plot_df[~plot_df.AccountCode.isin([150,199])]
        plot_df['Source'] = np.where(plot_df['*Name'].str.contains('Internal'),'Internal','External')
        
        plot_df = plot_df.groupby(['Time_Group','Source'])['Name'].value_counts().reset_index()
        plot_df['Giver_Count'] = [2 if '&' in x else 1 for x in plot_df.Name]
        plot_df = plot_df.groupby(['Time_Group','Source'])['Giver_Count'].sum().reset_index()
        plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

        # utils.altair_bar(plot_df,x='Time_Group',y='Giver_Count',color='Source',stack='zero')
        fig = px.bar(plot_df,x='Time_Group',y='Giver_Count',color='Source',text_auto=',.0f')
        st.plotly_chart(fig,use_container_width=True)


    col1, col2 = st.columns(2)

    with col1:

        st.subheader('Giving: Regular vs One-Off',divider='blue')

        plot_df = df[df.AccountCode.between(100,235)]
        plot_df = plot_df[~plot_df.AccountCode.isin([150,199])]
        plot_df['Frequency'] = np.where(plot_df['*Name'].str.contains('Regular'),'Regular','One-Off')

        plot_df = plot_df.groupby(['Time_Group','Frequency'])['Total'].sum().reset_index()
        plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

        # utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Frequency',stack='zero',text_stack='zero')
        fig = px.bar(plot_df,x='Time_Group',y='Total',color='Frequency',text_auto=',.0f')
        st.plotly_chart(fig,use_container_width=True)

    with col2:

        st.subheader('Giving: Internal vs External',divider='blue')

        plot_df = df[df.AccountCode.between(100,235)]
        plot_df = plot_df[~plot_df.AccountCode.isin([150,199])]
        plot_df['Source'] = np.where(plot_df['*Name'].str.contains('Internal'),'Internal','External')
        plot_df = plot_df.groupby(['Time_Group','Source'])['Total'].sum().reset_index()
        plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

        fig = px.bar(plot_df,x='Time_Group',y='Total',color='Source',text_auto=',.0f')
        st.plotly_chart(fig,use_container_width=True)
        # utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Source')

    col1, col2 = st.columns(2)

    with col1:

        st.subheader('Giving: Donor Distribution',divider='blue')

        plot_df = df[df.AccountCode.between(100,235)]
        plot_df = plot_df[~plot_df.AccountCode.isin([150,199])]
        plot_df = plot_df.groupby(['Time_Group','Name'])['Total'].sum().reset_index()
        plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

        top5d = plot_df.groupby(['Time_Group','Name'])['Total'].sum().sort_values().reset_index()
        top5d['Giving_rank'] = top5d.groupby('Time_Group')['Total'].rank(pct=True,ascending=False)
        top5d['Top20_flag'] = np.where(top5d['Giving_rank']<=0.2,'Top20','Other')

        #st.dataframe(top5d)

        plot_df = plot_df.merge(top5d,how='left',on=['Name','Time_Group'],suffixes=(None,"_y"))
        plot_df = plot_df.groupby(['Time_Group','Top20_flag'])['Total'].sum().reset_index()

        # fig = px.bar(plot_df,x='Time_Group',y='Total',color='Top20_flag',text_auto='.0f')
        # st.plotly_chart(fig,use_container_width=True)
        utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Top20_flag',stack='normalize',text=False)

    with col2:
            
        st.subheader('Expenses by Category',divider='blue')

        expense_category1 = utils.expense_category1()
        expense_category2 = utils.expense_category2()
        
        plot_df = df[df.AccountCode>300]
        plot_df['Category'] = plot_df.AccountCode.map(expense_category1)
        plot_df['Category'] = np.where(plot_df['Category'].isnull(),'Uncategorised',plot_df['Category'])
        plot_df = plot_df.groupby(['Time_Group','AccountCode','*Name','Category'])['Total'].sum().reset_index()
        plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

        fig = px.bar(plot_df,x='Time_Group',y='Total',color='Category',text_auto=',.0f').update_layout(margin=dict(t=10))
        st.plotly_chart(fig,use_container_width=True)
        # utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Category',text=False)

    useful_cols = ['Date','Time_Group','Name','Congregation','*Code','*Name','Description','SubTotal','Giftaid_Multiplier','Directional_Total']
    with st.expander('Show Table'):
        st.subheader('Expenses by Group')
        st.dataframe(plot_df.pivot_table(columns='Time_Group',index='Category',values='Total'),
                    use_container_width=True)
        st.subheader('Top Individual Expenses')
        st.dataframe(df[df['Directional_Total']<-3300][useful_cols].sort_values(by='Directional_Total'),use_container_width=True)

    Category_choice = st.selectbox('Select Category to see more details',plot_df.Category.unique(),None)
    
    if Category_choice is not None:

        plot_df = df[df.AccountCode>300]
        plot_df['Category'] = plot_df.AccountCode.map(expense_category1)
        plot_df = plot_df[plot_df['Category']==Category_choice]

        plot_df['Category'] = plot_df.AccountCode.map(expense_category2)
        plot_df2 = plot_df.groupby(['Time_Group','Category'])['Total'].sum().reset_index()
        plot_df2['Time_Group'] = plot_df2['Time_Group'].astype(str)

        fig = px.bar(plot_df2,x='Time_Group',y='Total',color='Category',text_auto=',.0f')
        st.plotly_chart(fig,use_container_width=True)

        st.dataframe(plot_df[['Date','Time_Group','Congregation','Name','*Code','*Name','Classification','Category','Total']])
        # utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Category',text=False)

    st.subheader('Non-Salary Expenses')
    
    plot_df = df[df.AccountCode>300]
    plot_df['Category'] = plot_df.AccountCode.map(expense_category1)
    plot_df = plot_df[plot_df.Category!='Salaries']
    plot_df = plot_df.groupby(['Time_Group','Category'])['Total'].sum().reset_index()
    plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)
    
    fig = px.bar(plot_df,x='Time_Group',y='Total',color='Category',text_auto=',.0f')
    st.plotly_chart(fig,use_container_width=True)

    st.markdown('# ')

    st.subheader('Internal Regular Income vs Core Expenses')

    plot_df = df.copy()
    plot_df['Category'] = plot_df.AccountCode.map(expense_category1)
    plot_df['Frequency'] = np.where(plot_df['*Name'].str.contains('Regular'),'Regular','One-Off')
    plot_df = plot_df[(plot_df['Frequency']=='Regular') | (plot_df['Classification']=='Expenses')]
    
    plot_df = plot_df.groupby(['Time_Group','Classification'])['Total'].sum().reset_index()
    plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

    utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Classification',
               xOffset='Classification',sort_list=['Income','Expenses'])

    st.subheader('Reserves over Time')

    plot_df = df[['Date','Directional_Total','Time_Group']].set_index('Date').sort_index()
    plot_df['Running_Total'] = plot_df.expanding().Directional_Total.sum().values

    plot_df = plot_df.groupby(['Time_Group'])['Running_Total'].last().reset_index()
    plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

    fig = px.bar(plot_df,x='Time_Group',y='Running_Total',text_auto=',.0f')
    st.plotly_chart(fig,use_container_width=True)

    if st.button('Show All Data'):
        st.dataframe(df[useful_cols].sort_values(by='Date'))

    # st.title('Custom Queries')

    # with st.form("sql_form"):
    #     input_sql = st.text_input('Enter Query',help="""SELECT sum(Directional_Total), Name from read_parquet('xero_data.parquet') where AccountCode<300 group by Name""")
    #     submitted = st.form_submit_button('Calculate')

    # if submitted:
    #     custom_df = duckdb.sql(input_sql).df()
    #     st.dataframe(custom_df,use_container_width=True)
    
if __name__ == "__main__":
    summary()

