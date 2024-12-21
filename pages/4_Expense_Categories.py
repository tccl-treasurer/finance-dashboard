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

def categories():

    st.header('Change Expense Categories')

    df = st.session_state['xero_data']

    df = df[df['AccountCode']>299][['AccountCode','*Name','SubTotal']
            ].groupby(['AccountCode','*Name'])['SubTotal'].count().reset_index(
            ).sort_values(by='AccountCode').rename(columns={'SubTotal':'Count'})

    # mapping = utils.expense_category1()
    # mapping = pd.DataFrame.from_dict(mapping,orient='index',columns=['Category']).reset_index(names='AccountCode')
    mapping = pd.read_parquet('expense_category_mapping.parquet')

    df = pd.merge(df,mapping,on=['AccountCode','*Name'],how='left')

    st.subheader('Current Mapping')
    st.dataframe(df.set_index('AccountCode'),use_container_width=True)

    st.subheader('Create/Edit Category')
    st.markdown('_This will overwrite the current mapping._')

    col1, col2 = st.columns([1,2])
    with col1:
        category_name = st.text_input('Choose Category Name')
    with col2:
        #concat for improved ui
        code_options = df['AccountCode'].astype(str) + ' - ' + df['*Name']
        codes = st.multiselect('Choose Corresponding Account Codes',options=code_options.tolist())

    #save button
    if st.button('Save Category Mapping'):
 
        new_mapping = pd.DataFrame(data={'Choices':codes,'Category2':[category_name]*len(codes)})
        new_mapping[['AccountCode','*Name']] = new_mapping['Choices'].str.split(' - ',expand=True)
        new_mapping['AccountCode'] = new_mapping['AccountCode'].astype('int64')
        new_mapping['*Name'] = new_mapping['*Name'].astype(str)
        new_mapping = new_mapping[['AccountCode','*Name','Category2']]
 
        df = pd.merge(df,new_mapping,on=['AccountCode','*Name'],how='left')
        df['Category'] = np.where(df['Category2'].notnull(),df['Category2'],df['Category'])
        df[['AccountCode','*Name','Category']].to_parquet('expense_category_mapping.parquet')
        placeholder = st.empty()
        with placeholder:
            st.success('Mapping Saved')
            time.sleep(2)
        placeholder.empty()

categories()



#Create or Edit Category
#Text input to define Category name
#Multiselect to choose relevant categories

