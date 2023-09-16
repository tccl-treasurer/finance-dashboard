import numpy as np
import pandas as pd
import streamlit as st
import math
import plotly.express as px
import plotly.graph_objects as go
from re import sub
from decimal import Decimal
# from st_aggrid import AgGrid
# from st_aggrid.grid_options_builder import GridOptionsBuilder
import time 
from datetime import datetime, timedelta
import utils as utils

def ec_page():

    st.session_state["payslips"] = st.sidebar.radio("Use Payslips:",['Yes','No'],horizontal=True,index=['Yes','No'].index(st.session_state["payslips"]))
    st.session_state["giftaid_choice"] = st.sidebar.radio("Giftaid Choice:",['Accrual','Cash'],horizontal=True)
    utils.giftaid_toggle(st.session_state["giftaid_choice"])
    expenses = st.session_state['expenses']
    
    recipients = st.multiselect('View Analysis for:',expenses.Recipient.unique().tolist(),['International'])
    
    DM = expenses[expenses.Recipient.isin(recipients)] \
         .groupby(['Academic_Year','Reference'])['Debit_Amount'].sum().reset_index()

    # Radio for user to choose view
    view = st.radio('Choose View:',['Tables','Lollipop'], horizontal=True)

    DM['Academic_Year'] = DM['Academic_Year'].astype(int)
    DM = DM.sort_values(by=['Debit_Amount'], ascending=False)
    
    # User Input Year
    year_list = DM.Academic_Year.unique().tolist()
    year_list.sort()
    year_list.append("Custom")
    select_year = st.selectbox('Select Year',year_list,year_list.index(2022))

    if select_year=='Custom':
        date_range1 = [expenses['Transaction Date'].min(),(expenses['Transaction Date'].max()-timedelta(92))]
        date_range2 = [(expenses['Transaction Date'].max()-timedelta(91)),expenses['Transaction Date'].max()]

        col1, col2 = st.columns([1,1])
        with col1:
            range1 = st.date_input('Range 1 (Previous)',value=date_range1)
        with col2:
            range2 = st.date_input('Range 2 (Recent)',value=date_range2)

        range1 = pd.to_datetime(range1)
        range2 = pd.to_datetime(range2)

        df_range1 = expenses[expenses['Transaction Date'].between(range1[0],range1[1])] \
                    .groupby(['Reference'])['Debit_Amount'].sum().reset_index(name='Range 1')

        df_range2 = expenses[expenses['Transaction Date'].between(range2[0],range2[1])] \
                    .groupby(['Reference'])['Debit_Amount'].sum().reset_index(name='Range 2')

        #Merge the two custom filtered grouped Series
        df_custom = pd.merge(df_range1,df_range2,how='outer',on='Reference')
        df_custom = df_custom.fillna(0)
        df_custom['Delta'] = df_custom['Range 2'] - df_custom['Range 1']

        output = df_custom.copy()

        #Sort by absolute values: https://stackoverflow.com/questions/30486263/sorting-by-absolute-value-without-changing-the-data
        output = output.reindex(output['Delta'].abs().sort_values(ascending=False).index)

        #st.dataframe(output)

    else:

        DM['Academic_Year'] = DM['Academic_Year'].astype(int)
        DM = DM.sort_values(by=['Debit_Amount'], ascending=False)

        # Filter for selected year or year prior to that
        selected_data = DM[(DM['Academic_Year']==select_year) | (DM['Academic_Year']==(select_year-1))]

        # Sum over all Source Types
        df = selected_data.groupby(['Reference','Academic_Year']).sum().reset_index()

        # Pivot from long to wide format: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot.html
        output = df.pivot(index='Reference',columns='Academic_Year',values='Debit_Amount').reset_index().fillna(0)

        # Calculate change
        output['Delta'] = output[select_year] - output[(select_year-1)]

        # Fitler out Delta == 0
        output = output[(output['Delta']!=0)]

        #Sort by absolute values: https://stackoverflow.com/questions/30486263/sorting-by-absolute-value-without-changing-the-data
        output = output.reindex(output['Delta'].abs().sort_values(ascending=False).index)

        # st.dataframe(output)

    if view=='Lollipop':

        #https://towardsdatascience.com/lollipop-dumbbell-charts-with-plotly-696039d5f85

        st.subheader("Change from previous period's expenses:")
        
        #st.slider docs: https://docs.streamlit.io/library/api-reference/widgets/st.slider
        x = st.slider('', min_value=-60000, max_value=60000,value=[1000,60000],step=500)

        filtered_output = output[(output['Delta']>=x[0]) & (output['Delta']<=x[1])]

        filtered_output = filtered_output.reindex(filtered_output['Delta'].abs().sort_values().index)

        # Isolate Selected year data and year prior to that
        syd = filtered_output.iloc[:,2].tolist() 
        sydm1 = filtered_output.iloc[:,3].tolist()

        # syd = filtered_output[select_year].tolist() 
        # sydm1 = filtered_output[(select_year-1)].tolist()

        fig3= go.Figure()

        if select_year=='Custom':
            name1 = str(range1[0].strftime('%Y/%m/%d')) + '-' + str(range1[1].strftime('%Y/%m/%d'))
            name2 = str(range2[0].strftime('%Y/%m/%d')) + '-' + str(range2[1].strftime('%Y/%m/%d'))
        else:
            name1 = "Previous"
            name2 = "Current"

        # Prior Year Scatter
        fig3.add_trace(go.Scatter(x = sydm1, 
                                y = filtered_output['Reference'],
                                mode = 'markers',
                                marker_color = 'darkorange', 
                                marker_size = 10,
                                name = name1))

        # Selected Year Scatter
        fig3.add_trace(go.Scatter(x = syd, 
                                y = filtered_output['Reference'],
                                mode = 'markers',
                                marker_color = 'darkblue',
                                marker_size = 10,
                                name = name2))        
        
        # Add Lines
        for i in range(0, len(syd)):
                    fig3.add_shape(type='line',
                                    x0 = syd[i],
                                    y0 = i,
                                    x1 = sydm1[i],
                                    y1 = i,
                                    line=dict(color='crimson', width = 3))
        
        # Update Layout
        fig3 = fig3.update_layout(height=400,legend=dict(orientation="h",y=-0.15,x=0.15),margin=dict(t=10,b=10))
        
        st.plotly_chart(fig3,use_containter_width=True)
        
        filtered_output = filtered_output.sort_values(by=['Delta'],ascending=False)

        # Convert Column names to string for AgGrid
        filtered_output.columns = filtered_output.columns.astype(str)

        # utils.AgGrid_default(filtered_output,
        #     filtered_output.columns[filtered_output.columns.isin(['Reference'])==False],['Reference'],400)
        st.dataframe(filtered_output.style.format(precision=1,thousands=' '))

    else:

        type = st.radio("View List of",['New','Increased','Lost','Decreased'], horizontal=True)

        if type=='New':
        
            st.subheader(f'New expenses in {select_year}')
            if select_year=='Custom':
                tmp = output[(output['Range 2']>0) & (output['Range 1']==0)]    
            else:
                tmp = output[(output[select_year]>0) & (output[(select_year-1)]==0)]
            tmp.columns = tmp.columns.astype(str)
            #utils.AgGrid_default(tmp,tmp.columns[tmp.columns.isin(['Reference'])==False],['Reference'],400)
            st.dataframe(tmp.style.format(precision=1,thousands=' '))
        
        elif type=='Increased':
        
            st.subheader(f'Increased expenses in {select_year}')
            if select_year=='Custom':
                tmp = output[(output['Delta']>0) & (output.iloc[:,1]!=0)]    
            else:
                tmp = output[(output['Delta']>0) & (output[(select_year-1)]!=0)]
            tmp.columns = tmp.columns.astype(str)
            #utils.AgGrid_default(tmp,tmp.columns[tmp.columns.isin(['Reference'])==False],['Reference'],400)
            st.dataframe(tmp.style.format(precision=1,thousands=' '))
        
        elif type=='Lost':
        
            st.subheader(f'Lost expenses in {select_year}')
            if select_year=='Custom':
                tmp = output[(output.iloc[:,2]==0) & (output.iloc[:,1]>0)]    
            else:
                tmp = output[(output[select_year]==0) & (output[(select_year-1)]>0)]
            tmp.columns = tmp.columns.astype(str)
            #utils.AgGrid_default(tmp,tmp.columns[tmp.columns.isin(['Reference'])==False],['Reference'],400)
            st.dataframe(tmp.style.format(precision=1,thousands=' '))
        
        else:
        
            st.subheader(f'Decreased expenses in {select_year}')
            if select_year=='Custom':
                tmp = output[(output['Delta']<0) & (output.iloc[:,1]!=0)]    
            else:
                tmp = output[(output['Delta']<0) & (output[(select_year)]!=0)]
            tmp.columns = tmp.columns.astype(str)
            #utils.AgGrid_default(tmp,tmp.columns[tmp.columns.isin(['Reference'])==False],['Reference'],400)
            st.dataframe(tmp.style.format(precision=1,thousands=' '))
        
st.set_page_config(page_title="Expense Comparison", page_icon="📊",layout='wide')

st.title('Expense Comparison')

if 'auth' in st.session_state:
    ec_page()
else:
    st.subheader('Error: Go to Home to download data')