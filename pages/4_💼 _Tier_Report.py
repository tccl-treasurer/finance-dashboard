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

def categorize_donor(x):
    if x >= 50000:
        cat = 1
    elif x >= 20000:
        cat = 2
    elif x >= 2000:
        cat = 3
    elif x >= 400:
        cat = 4
    else:
        cat = 5
    return cat

def tier_page():

    st.session_state["currency_choice"] = st.sidebar.radio("Choose Currency:",['GBP','USD'],horizontal=True,index=['GBP','USD'].index(st.session_state["currency_choice"]))

    utils.convert_gbpusd(st.session_state["currency_choice"])

    DM = st.session_state.TRD

    # Sum over Source Type
    DM = DM.drop(columns=['Debit Amount','Source Type'])
    DM = DM.groupby(['Renamer','Y']).sum().reset_index()
    DM = DM.sort_values(by=['Credit Amount'], ascending=False)

    # Create Category Column
    DM['Category'] = DM['Credit Amount'].apply(categorize_donor)
    
    # Eliminate zeros to reduce table length for Tier 5
    DM = DM[DM['Credit Amount']!=0] 

    # User Input Year
    DM = DM.sort_values(by=['Y'])
    year_list = DM['Y'].unique().tolist()
    year_list.append('All') 
    select_year = st.selectbox('Select Year',year_list,year_list.index('All'))

    if select_year=='All':
        
        # Sum by Category and Year
        df2 = DM.groupby(['Y','Category']).sum().reset_index()
        df2 = df2.sort_values(by=['Category'])
        df2['Category'] = df2['Category'].astype(str)

        # Count by Category and Year
        df3 = DM[['Renamer','Y','Category']].groupby(['Y','Category']).count().reset_index()
        df3.columns = ['Y','Category','Count']
        df3 = df3.sort_values(by=['Category'])
        df3['Category'] = df3['Category'].astype(str)
       
        view_choice = st.radio('Show by Absolute or Percent:',['Absolute','Percent','Count','Count Percent'],horizontal=True)

        if view_choice=='Absolute':

            df4 = df2.merge(df3,on=['Y','Category'])

            fig = px.bar(df4, x="Y", y="Credit Amount", custom_data=['Count'], color="Category",text_auto='.2s')
            fig = fig.update_layout(legend=dict(orientation="h",y=-0.15,x=0.15),margin=dict(t=30,b=10))
            fig = fig.update_layout(title_text ="Income by Category", title_font_size = 20)
            fig = fig.update_xaxes(categoryorder='array',categoryarray=df4.Y.unique().tolist())
            fig = fig.update_traces(hovertemplate="<br>".join(["Year: %{x}", "Credit Amount: %{y}", "Count: %{customdata[0]}"]))
        
        elif view_choice=='Percent':

            totals = df2[['Y','Credit Amount']].groupby(['Y']).sum().reset_index()
            totals.columns = ['Y','Total']
            df5 = df2.merge(totals,on='Y')
            df5 = df5.merge(df3,on=['Y','Category'])
            df5['Percent'] = 100 * df5['Credit Amount']/df5['Total']

            fig = px.bar(df5, x="Y", y="Percent", custom_data=['Count'], color="Category",text_auto='.1f')
            fig = fig.update_layout(legend=dict(orientation="h",y=-0.15,x=0.15),margin=dict(t=30,b=10))
            fig = fig.update_layout(title_text ="Income by Category", title_font_size = 20)
            fig = fig.update_layout(barmode='relative')
            fig = fig.update_xaxes(categoryorder='array',categoryarray=df5.Y.unique().tolist())
            fig = fig.update_traces(hovertemplate="<br>".join(["Year: %{x}", "Percent: %{y}", "Count: %{customdata[0]}"]))
        
        elif view_choice=='Count':

            fig = px.bar(df3, x="Y", y="Count", color="Category",text_auto='.0f')
            fig = fig.update_layout(legend=dict(orientation="h",y=-0.15,x=0.15),margin=dict(t=30,b=10))
            fig = fig.update_layout(title_text ="Income by Category", title_font_size = 20)
            fig = fig.update_layout(barmode='relative')
            fig = fig.update_xaxes(categoryorder='array',categoryarray=df3.Y.unique().tolist())

        elif view_choice=='Count Percent':

            count_total = df3.groupby(['Y']).sum().reset_index()
            count_total.columns = ['Y','Total']
            df6 = df3.merge(count_total,on='Y')
            df6 = df6.sort_values(by=['Category'])
            df6['Count Percent'] = 100 * df6['Count']/df6['Total']

            fig = px.bar(df6, x="Y", y="Count Percent", color="Category",text_auto='.1f')
            fig = fig.update_layout(legend=dict(orientation="h",y=-0.15,x=0.15),margin=dict(t=30,b=10))
            fig = fig.update_layout(title_text ="Income by Category", title_font_size = 20)
            fig = fig.update_layout(barmode='relative')
            fig = fig.update_xaxes(categoryorder='array',categoryarray=df6.Y.unique().tolist())

        st.plotly_chart(fig,use_container_width=True)
    
    else:
    
        # User Radio to enable User Tier Selection: https://docs.streamlit.io/library/api-reference/widgets/st.radio
        tier = st.radio("Select Tier", [1,2,3,4,5], horizontal=True)
        
        #Filter and sum
        df = DM[(DM['Y']==select_year) & (DM['Category']==tier)]
        df_total = pd.to_numeric(df['Credit Amount'].sum())
        df = df.drop(columns=['Category'])

        st.markdown(f'### Tier {tier} Table: Total = £{df_total:,.2f}')

        #Add Copy to Clipboard table
        utils.AgGrid_default(df,df.columns[df.columns.isin(['Renamer','Y'])==False],['Renamer','Y'],400)
        
st.set_page_config(page_title="Tier Report", page_icon="💼",layout='centered')

st.title('Tier Report')

if 'auth' in st.session_state:
    tier_page()
    
    # Tier Key at bottom
    st.markdown("<h5 style='text-align: center;'> Tier 1: £50k+ | Tier 2: £20k+ | Tier 3: £2k+ | Tier 4: £400+ | Tier 5: <£400 </h5>", unsafe_allow_html=True)

else:
    st.subheader('Error: Go to Home to download data')

