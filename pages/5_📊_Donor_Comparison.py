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

def dc_page():

    st.session_state["payslips"] = st.sidebar.radio("Use Payslips:",['Yes','No'],horizontal=True,index=['Yes','No'].index(st.session_state["payslips"]))
    st.session_state["giftaid_choice"] = st.sidebar.radio("Giftaid Choice:",['Accrual','Cash'],horizontal=True)
    utils.giftaid_toggle(st.session_state["giftaid_choice"])

    # Radio for user to choose view
    view = st.radio('Choose View:',['Lollipop','Tables'], horizontal=True)

    income = st.session_state['income']
    DM = income.groupby(['Academic_Year','Name'])['Income_Amount'].sum().reset_index()

    # User Input Year
    year_list = DM.Academic_Year.unique().tolist()
    year_list.sort()
    select_year = st.selectbox('Select Year',year_list,year_list.index(int(datetime.now().year)))

    DM['Academic_Year'] = DM['Academic_Year'].astype(int)
    DM = DM.sort_values(by=['Income_Amount'], ascending=False)

    # Filter for selected year or year prior to that
    selected_data = DM[(DM['Academic_Year']==select_year) | (DM['Academic_Year']==(select_year-1))]

    # Sum over all Source Types
    df = selected_data.groupby(['Name','Academic_Year']).sum().reset_index()

    # Pivot from long to wide format: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot.html
    output = df.pivot(index='Name',columns='Academic_Year',values='Income_Amount').reset_index().fillna(0)

    # Calculate change
    output['Delta'] = output[select_year] - output[(select_year-1)]

    # Fitler out Delta == 0
    output = output[(output['Delta']!=0)]

    #Sort by absolute values: https://stackoverflow.com/questions/30486263/sorting-by-absolute-value-without-changing-the-data
    output = output.reindex(output['Delta'].abs().sort_values(ascending=False).index)

    if view=='Lollipop':

        #https://towardsdatascience.com/lollipop-dumbbell-charts-with-plotly-696039d5f85

        st.subheader("Change from previous year's giving:")
        
        #st.slider docs: https://docs.streamlit.io/library/api-reference/widgets/st.slider
        x = st.slider('', min_value=-60000, max_value=60000,value=[1000,60000],step=500)

        filtered_output = output[(output['Delta']>=x[0]) & (output['Delta']<=x[1])]

        filtered_output = filtered_output.reindex(filtered_output['Delta'].abs().sort_values().index)

        # Isolate Selected year data and year prior to that
        syd = filtered_output[select_year].tolist() 
        sydm1 = filtered_output[(select_year-1)].tolist()

        fig3= go.Figure()

        # Selected Year Scatter
        fig3.add_trace(go.Scatter(x = syd, 
                                y = filtered_output['Name'],
                                mode = 'markers',
                                marker_color = 'darkblue',
                                marker_size = 10,
                                name = select_year))
        
        # Prior Year Scatter
        fig3.add_trace(go.Scatter(x = sydm1, 
                                y = filtered_output['Name'],
                                mode = 'markers',
                                marker_color = 'darkorange', 
                                marker_size = 10,
                                name = (select_year-1)))
        
        # Add Lines
        for i in range(0, len(syd)):
                    fig3.add_shape(type='line',
                                    x0 = syd[i],
                                    y0 = i,
                                    x1 = sydm1[i],
                                    y1 = i,
                                    line=dict(color='crimson', width = 3))
        
        # Update Layout
        fig3 = fig3.update_layout(height=600,legend=dict(orientation="h",y=-0.15,x=0.15),margin=dict(t=10,b=10))
        
        st.plotly_chart(fig3,use_containter_width=True)
        
        filtered_output = filtered_output.sort_values(by=['Delta'],ascending=False)

        # Convert Column names to string for AgGrid
        filtered_output.columns = filtered_output.columns.astype(str)

        utils.AgGrid_default(filtered_output,
            filtered_output.columns[filtered_output.columns.isin(['Name'])==False],['Name'],600)
        
    else:

        type = st.radio("View List of",['New','Increased','Lost','Decreased'], horizontal=True)

        if type=='New':
        
            st.subheader(f'New donors in {select_year}')
            tmp = output[(output[select_year]>0) & (output[(select_year-1)]==0)]
            tmp.columns = tmp.columns.astype(str)
            utils.AgGrid_default(tmp,tmp.columns[tmp.columns.isin(['Name'])==False],['Name'],600)
        
        elif type=='Increased':
        
            st.subheader(f'Increased donors in {select_year}')
            tmp = output[(output['Delta']>0) & (output[(select_year-1)]!=0)]
            tmp.columns = tmp.columns.astype(str)
            utils.AgGrid_default(tmp,tmp.columns[tmp.columns.isin(['Name'])==False],['Name'],600)
        
        elif type=='Lost':
        
            st.subheader(f'Lost donors in {select_year}')
            tmp = output[(output[select_year]==0) & (output[(select_year-1)]>0)]
            tmp.columns = tmp.columns.astype(str)
            utils.AgGrid_default(tmp,tmp.columns[tmp.columns.isin(['Name'])==False],['Name'],600)
        
        else:
        
            st.subheader(f'Decreased donors in {select_year}')
            tmp = output[(output['Delta']<0) & (output[(select_year)]!=0)]
            tmp.columns = tmp.columns.astype(str)
            utils.AgGrid_default(tmp,tmp.columns[tmp.columns.isin(['Name'])==False],['Name'],600)
        
st.set_page_config(page_title="Donor Comparison", page_icon="📊",layout='centered')

st.title('Donor Comparison')

if 'auth' in st.session_state:
    dc_page()
else:
    st.subheader('Error: Go to Home to download data')