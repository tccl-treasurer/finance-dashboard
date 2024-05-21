import streamlit as st
from streamlit.logger import get_logger
import utils
import json
import requests
import webbrowser
import base64
from io import StringIO
import numpy as np
import pandas as pd
import altair as alt
import os
import utils

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
        time_group = st.radio('Choose Time Grouping',['Calendar Year','Tax Year','Academic Year','Quarter','Month',None],horizontal=True)
    
    with col2:
        df.Date = pd.to_datetime(df.Date,format='%Y/%m/%d')
        date_range = st.date_input('Date Range',[pd.to_datetime('2022-01-01'),
                                                df.Date.max()])
        date_range = [pd.to_datetime(x) for x in date_range]
    
    with col3:
        #st.markdown('#### ')
        giftaid = st.toggle('Giftaid',True)
        other_accounts = st.toggle('Only Current Account',True)

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
    else:
        df['Time_Group'] = 'All'

    if giftaid:
        df['Total'] = df['SubTotal'] * df['Giftaid_Multiplier']
    else:
        df['Total'] = df['SubTotal']

    if other_accounts:
        df = df[df.BankAccountName=='Current Account']

    st.subheader("Exclude Accounts")

    accounts_to_exclude = st.text_input('Remove categories containing any of the words:',value=None)

    if accounts_to_exclude is not None:

        exclude_categories = pd.DataFrame()
        for word in accounts_to_exclude.split(' '):
            #st.write(word)
            exclude_categories = pd.concat([
                exclude_categories,df[df['*Name'].str.contains(word)][['*Code','*Name']].drop_duplicates()
            ],axis=0)
        #exclude_categories['*Code'] = exclude_categories['*Code'].astype('int64')
        st.write("The following accounts have been excluded:")
        st.dataframe(exclude_categories.set_index('*Code').sort_index())

        df = df[~df['AccountCode'].isin(exclude_categories['*Code'].astype('int64').tolist())]

    st.subheader('Income vs Expenses over Time')

    plot_df = df.groupby(['Time_Group','Classification'])['Total'].sum().reset_index()
    plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

    utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Classification',
               xOffset='Classification',sort_list=['Income','Expenses'])
    
    st.subheader('Number of Givers')

    plot_df = df[df.AccountCode.between(100,235)]
    plot_df = plot_df[~plot_df.AccountCode.isin([150,199])]
    plot_df['Source'] = np.where(plot_df['*Name'].str.contains('Internal'),'Internal','External')
    
    plot_df = plot_df.groupby(['Time_Group','Source'])['Name'].value_counts().reset_index()
    plot_df['Giver_Count'] = [2 if '&' in x else 1 for x in plot_df.Name]
    plot_df = plot_df.groupby(['Time_Group','Source'])['Giver_Count'].sum().reset_index()
    plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

    utils.altair_bar(plot_df,x='Time_Group',y='Giver_Count',color='Source',stack='zero')

    st.subheader('Giving: Regular vs One-Off')

    plot_df = df[df.AccountCode.between(100,235)]
    plot_df = plot_df[~plot_df.AccountCode.isin([150,199])]
    plot_df['Frequency'] = np.where(plot_df['*Name'].str.contains('Regular'),'Regular','One-Off')

    plot_df = plot_df.groupby(['Time_Group','Frequency'])['Total'].sum().reset_index()
    plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

    utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Frequency',stack='zero',text_stack='zero')

    st.subheader('Giving: Internal vs External')

    plot_df = df[df.AccountCode.between(100,235)]
    plot_df = plot_df[~plot_df.AccountCode.isin([150,199])]
    plot_df['Source'] = np.where(plot_df['*Name'].str.contains('Internal'),'Internal','External')
    plot_df = plot_df.groupby(['Time_Group','Source'])['Total'].sum().reset_index()
    plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

    utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Source')

    st.subheader('Giving: Donor Distribution')

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

    utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Top20_flag',stack='normalize',text=False)

    st.subheader('Expenses by Category')

    expense_category1 = utils.expense_category1()
    expense_category2 = utils.expense_category2()
    
    plot_df = df[df.AccountCode>300]
    plot_df['Category'] = plot_df.AccountCode.map(expense_category1)
    plot_df = plot_df.groupby(['Time_Group','Category'])['Total'].sum().reset_index()
    plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

    utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Category',text=False)

    if st.button('Show Table'):
        st.dataframe(plot_df.pivot_table(columns='Time_Group',index='Category',values='Total'),
                     use_container_width=True)

    Category_choice = st.selectbox('Select Category to see more details',plot_df.Category.unique(),None)
    
    if Category_choice is not None:

        plot_df = df[df.AccountCode>300]
        plot_df['Category'] = plot_df.AccountCode.map(expense_category1)
        plot_df = plot_df[plot_df['Category']==Category_choice]

        plot_df['Category'] = plot_df.AccountCode.map(expense_category2)
        plot_df = plot_df.groupby(['Time_Group','Category'])['Total'].sum().reset_index()
        plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

        utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Category',text=False)

    st.subheader('Non-Salary Expenses')
    
    plot_df = df[df.AccountCode>300]
    plot_df['Category'] = plot_df.AccountCode.map(expense_category1)
    plot_df = plot_df[plot_df.Category!='Salaries']
    plot_df = plot_df.groupby(['Time_Group','Category'])['Total'].sum().reset_index()
    plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)
    
    x='Time_Group'
    y='Total'
    color='Category'
    text_offset = 6
    stack='zero'

    selection = alt.selection_multi(fields=['Category'], bind='legend')

    fig = alt.Chart(plot_df).mark_bar().encode(
    x=alt.X(f'{x}:N',axis=alt.Axis(labelAngle=0)).title(f'{x.replace("_"," ")}').stack(stack),
    y=alt.Y(f'sum({y}):Q').stack(stack), 
    color=alt.Color(f'{color}:N') #.legend(orient="top",direction='horizontal',labelAlign ='left',padding=0)
    ).add_selection(
    selection
    )
    
    text = alt.Chart(plot_df).mark_text(
                        #dy=text_offset,
                        dy=alt.expr(alt.expr.if_(alt.datum[f'sum({y}):Q'] > 1000, 20, 6)),
                        dx=3,color='white' #,fontSize=10
                        ).encode(y=alt.Y(f'sum({y}):Q').stack(stack), #
                                x=alt.X(f'{x}:N',axis=alt.Axis(labelAngle=0)).title(f'{x.replace("_"," ")}').stack(stack),
                                detail=f'{color}:N',
                                text=alt.Text(f'sum({y}):Q',format=',.0f')
                                )

    st.markdown('# ')
    st.altair_chart(fig + text,use_container_width=True)

    st.subheader('Internal Regular Income vs Core Expenses')

    plot_df = df.copy()
    plot_df['Category'] = plot_df.AccountCode.map(expense_category1)
    plot_df = plot_df[(plot_df.AccountCode.isin([210,211,212,213,214,215,])) |
                (plot_df.Category.isin(['Salaries','Equipment, Books & Fliers',
                                        'Food','Kids & Youth Work','Admin','General']))]
    
    plot_df = plot_df.groupby(['Time_Group','Classification'])['Total'].sum().reset_index()
    plot_df['Time_Group'] = plot_df['Time_Group'].astype(str)

    utils.altair_bar(plot_df,x='Time_Group',y='Total',color='Classification',
               xOffset='Classification',sort_list=['Income','Expenses'])

    st.subheader('Reserves over Time')

    plot_df = df[['Date','Directional_Total']].set_index('Date').sort_index()
    plot_df = plot_df.expanding().Directional_Total.sum().reset_index()

    fig = alt.Chart(plot_df).mark_line().encode(
    x=alt.X('Date:T'),
    y=alt.Y('Directional_Total:Q')
    )

    st.markdown('# ')
    st.altair_chart(fig,use_container_width=True)

    # st.title('Custom Queries')

    # with st.form("sql_form"):
    #     input_sql = st.text_input('Enter Query',help="""SELECT sum(Directional_Total), Name from read_parquet('xero_data.parquet') where AccountCode<300 group by Name""")
    #     submitted = st.form_submit_button('Calculate')

    # if submitted:
    #     custom_df = duckdb.sql(input_sql).df()
    #     st.dataframe(custom_df,use_container_width=True)
    
if __name__ == "__main__":
    summary()

