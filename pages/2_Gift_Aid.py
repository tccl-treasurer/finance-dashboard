
import time
import numpy as np
import pandas as pd
import streamlit as st
from streamlit.hello.utils import show_code

def giftaid():

    st.title("Gift Aid Claim")
    st.write("Please note if you are claiming for donations in multiple financial years, HMRC prefers each line to refer to only one year at a time (ie resulting in multiple entries for the same person)")

    giftaid_df = st.session_state['xero_data']

    if len(giftaid_df)==0:
        st.error("Error. First go to Home to Download Data from Xero.")

    date_range = st.date_input('Date Range',[giftaid_df.Date.min(),
                                             giftaid_df.Date.max()])
    date_range = [pd.to_datetime(x) for x in date_range]
    giftaid_df = giftaid_df[giftaid_df.Date.between(date_range[0],date_range[1])]

    giftaid_df['Giftaid_Multiplier'] = np.where(giftaid_df.AccountCode<125,1.25,1)
    giftaid_df['Giftaid_Amount'] = giftaid_df['SubTotal'] * (giftaid_df['Giftaid_Multiplier']-1)
    giftaid_df['Overall'] = giftaid_df['SubTotal'] * giftaid_df['Giftaid_Multiplier']

    giftaid_df['date'] = pd.to_datetime(giftaid_df['DateString'])
    #st.time_input('Date Range',)
    cols = ['date','SubTotal','Name','Giftaid_Amount','Overall','AccountCode','Giftaid_Multiplier']
    chart_df = giftaid_df[giftaid_df['Giftaid_Multiplier']==1.25][cols].groupby('Name').agg(
                Num_Donations=('SubTotal',np.count_nonzero),
                SubTotal=('SubTotal',np.sum),
                Giftaid_Total=('Giftaid_Amount',np.sum),
                Overall=('Overall',np.sum),
                Max_date=('date',np.max)
    ).sort_values(by='Giftaid_Total',ascending=False)

    st.dataframe(chart_df[chart_df.Giftaid_Total>0],use_container_width=True)      

    st.metric(value=chart_df.Giftaid_Total.sum(),label='Claim-able Amount')  

    st.subheader('Audit Donations')

    names = giftaid_df[giftaid_df.SubTotal>0].Name.unique().tolist()

    check_name = st.selectbox('Name',names,0)

    st.dataframe(giftaid_df[giftaid_df.Name==check_name][cols],use_container_width=True)      

giftaid()