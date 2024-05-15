import time
import pandas as pd
import MySQLdb
import plotly.express as px
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Real-Time KECS Commercial Dashboard",
    page_icon="✅",
    layout="wide"
)

# Load image for sidebar
st.sidebar.image('kaduna-removebg-preview.png', use_column_width=True)
st.sidebar.markdown('Created by [Team ITApps](#)')

# Setting up the connection
conn = MySQLdb.connect(host="184.154.139.152",
                       user="kadunael_read",
                       passwd="Password@2017",
                       db="kadunael_commonDb")
cursor = conn.cursor()

# Date range filter
st.sidebar.markdown('Select a date range')
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2024-05-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2024-06-30"))

# Read database data
read_data = pd.read_sql_query(""" SELECT * FROM areaoffice   """, conn)

# Total bill delivery
bill_data = pd.read_sql_query("""SELECT * FROM billdeliverydev_check """, conn)

# Total Visits by Area Office
ao_data_query = f"""
    SELECT areaoffice.area_office AS AreaOffice,
           COUNT(billdeliverydev_check.postedby) AS Visits
    FROM billdeliverydev_check
    INNER JOIN users ON billdeliverydev_check.postedby = users.id
    JOIN areaoffice ON areaoffice.aoid = users.AreaOffice
    WHERE billdeliverydev_check.trans_date BETWEEN '{start_date}' AND '{end_date}'
      AND users.Role = 'nmd'
    GROUP BY AreaOffice;
"""
ao_data = pd.read_sql_query(ao_data_query, conn)

# Total Delivered Bills by Area Office
ao_data1_query = f"""
    SELECT DISTINCT areaoffice.area_office AS AreaOffice, 
           COUNT(billdeliverydev_check.postedby) AS BillDelivered 
    FROM billdeliverydev_check 
    INNER JOIN users ON billdeliverydev_check.postedby = users.id
    JOIN areaoffice ON areaoffice.aoid = users.AreaOffice
    WHERE billdeliverydev_check.trans_date BETWEEN '{start_date}' AND '{end_date}' 
      AND billdeliverydev_check.status = 'delivered'
    GROUP BY AreaOffice
    ORDER BY BillDelivered DESC
"""
ao_data1 = pd.read_sql_query(ao_data1_query, conn)

# Total Undelivered by Area Office
ao_data2_query = f"""
    SELECT DISTINCT areaoffice.area_office AS AreaOffice, 
           COUNT(billdeliverydev_check.postedby) as BillDelivered 
    FROM billdeliverydev_check 
    INNER JOIN users ON billdeliverydev_check.postedby = users.id
    JOIN areaoffice on areaoffice.aoid = users.AreaOffice
    WHERE billdeliverydev_check.trans_date BETWEEN '{start_date}' AND '{end_date}' 
      AND billdeliverydev_check.status = "undelivered"
    GROUP BY AreaOffice 
    ORDER BY BillDelivered DESC
"""
ao_data2 = pd.read_sql_query(ao_data2_query, conn)

# Feeder Delivery Information
feeder_query = f"""
    SELECT users.FullName AS Staff, 
           COUNT(billdelivery.AccountNumber) AS DeliveredBills, 
           feeder.feeder_name AS Feeder, 
           areaoffice.area_office AS AreaOffice 
    FROM users
    INNER JOIN billdelivery ON users.ID = billdelivery.postedby
    JOIN feeder ON feeder.feederid = users.feederid
    JOIN areaoffice ON areaoffice.aoid = users.AreaOffice
    WHERE trans_date BETWEEN '{start_date}' AND '{end_date}' 
      AND users.Role = 'nmd'
    GROUP BY Staff
    ORDER BY AreaOffice DESC
"""
feeder = pd.read_sql_query(feeder_query, conn)

# SQL query to fetch data
query = f"""
SELECT users.FullName AS Staff,
       users.payroll_id AS Payroll,
       COUNT(billdeliverydev_check.AccountNumber) AS DeliveredBills,
       feeder.feeder_name AS Feeder,
       areaoffice.area_office AS AreaOffice
FROM users
INNER JOIN billdeliverydev_check ON users.ID = billdeliverydev_check.postedby
JOIN feeder ON feeder.feederid = users.feederid
JOIN areaoffice ON areaoffice.aoid = users.AreaOffice
WHERE billdeliverydev_check.trans_date BETWEEN '{start_date}' AND '{end_date}'
  AND billdeliverydev_check.status = 'Delivered'
  AND users.Role = 'nmd'
GROUP BY Staff
ORDER BY AreaOffice
"""
delivered_data = pd.read_sql_query(query, conn)

# Calculating total undelivered bills
total_delivered = delivered_data['DeliveredBills'].sum()


# SQL query to fetch undelivered data
undelivered_query = f"""
    SELECT users.FullName AS Staff,
           COUNT(billdeliverydev_check.AccountNumber) AS UndeliveredBills,
           feeder.feeder_name AS Feeder,
           areaoffice.area_office AS AreaOffice
    FROM users
    INNER JOIN billdeliverydev_check ON users.ID = billdeliverydev_check.postedby
    JOIN feeder ON feeder.feederid = users.feederid
    JOIN areaoffice ON areaoffice.aoid = users.AreaOffice
    WHERE billdeliverydev_check.trans_date BETWEEN '{start_date}' AND '{end_date}'
      AND billdeliverydev_check.status = 'Not Delivered'
      AND users.Role = 'nmd'
    GROUP BY Staff
    ORDER BY AreaOffice
"""
undelivered_data = pd.read_sql_query(undelivered_query, conn)

# Calculating total undelivered bills
total_undelivered = undelivered_data['UndeliveredBills'].sum()


st.markdown('### Metrics')
row1_1, row1_2, row1_3 = st.columns((3))
with row1_1:
    st.title("Real-Time / Live Toolkit Application")

with row1_3:
    st.text(time.strftime("%Y-%m-%d %H:%M"))

placeholder = st.empty()
with placeholder.container():
    kpis = st.columns(5)
    kpis[0].metric(label="No. of Area Offices 🏠 ", value=read_data.shape[0], delta=read_data.shape[1])
    kpis[1].metric(label="Total No. of Bills Delivered 🏠 ", value=total_delivered,
                   delta=delivered_data.shape[1])
    kpis[2].metric(label="Total Visits by Area Office 🏠 ", value=ao_data['Visits'].sum(), delta=ao_data.shape[1])
    kpis[3].metric(label="Total Delivered by Area Office 🏠 ", value=ao_data1['BillDelivered'].sum(), delta=ao_data1.shape[1])
    kpis[4].metric(label="Total Undelivered by Area Office 🏠 ", value=total_undelivered,
                   delta=undelivered_data.shape[1])

# Sidebar options
option = st.sidebar.selectbox("Summary Report", ('Information', 'Area Office Summary'))

if option == 'Information':
    st.markdown("""
    In this notebook, we will do some analysis by looking at the data from billdelivery.
    * Total Area Offices, Bill Delivered and Total visit by SR
    * Select chart by Area Office
    * Graph view show casting Total bills delivered, undelivered and disconnected
    * Thank you
    """)

if option == 'Area Office Summary':
    # Plot Area office by total no of visits
    category_tr = ao_data.groupby(by='AreaOffice')['Visits'].sum().to_frame().sort_values('Visits').reset_index()

    # Plot Total Delivered Bills by Area Office
    st.markdown("## Total Delivered Bills by Area Office - (May 2024)")
    fig2 = px.bar(ao_data1, x='BillDelivered', y='AreaOffice',
                  color='AreaOffice', width=950, height=500)
    fig2.update_layout(showlegend=False,
                       title="Total Delivered Bills by Area Office",
                       title_x=0.5,
                       xaxis_title='Delivered Bills',
                       yaxis_title='Area Offices')
    st.plotly_chart(fig2)

    # Execute the query and fetch data
    report_data = pd.read_sql_query(query, conn)

    # Display the report title
    st.markdown("## SR Delivered Bills by Area Office - (May 2024)")

    # Plot bar chart
    fig = px.bar(report_data, x='Staff', y='DeliveredBills', color='AreaOffice',
                 title="SR Delivered Bills by Area Office",
                 labels={'Staff': 'Staff', 'DeliveredBills': 'Delivered Bills'})
    st.plotly_chart(fig)

    # Undelivered Bills by Staff, Feeder, and Area Office
    undelivered_query = f"""
    SELECT users.FullName AS Staff,
           COUNT(billdeliverydev_check.AccountNumber) AS UndeliveredBills,
           feeder.feeder_name AS Feeder,
           areaoffice.area_office AS AreaOffice
    FROM users
    INNER JOIN billdeliverydev_check ON users.ID = billdeliverydev_check.postedby
    JOIN feeder ON feeder.feederid = users.feederid
    JOIN areaoffice ON areaoffice.aoid = users.AreaOffice
    WHERE billdeliverydev_check.trans_date BETWEEN '{start_date}' AND '{end_date}'
      AND billdeliverydev_check.status = 'Not Delivered'
      AND users.Role = 'nmd'
    GROUP BY Staff
    ORDER BY AreaOffice
    """
    undelivered_data = pd.read_sql_query(undelivered_query, conn)

    # Display the report title
    st.markdown("## Undelivered Bills by Staff, Feeder, and Area Office - (May 2024)")

    # Plot bar chart
    fig = px.bar(undelivered_data, x='Staff', y='UndeliveredBills', color='AreaOffice',
                 hover_data=['Feeder', 'AreaOffice'],
                 title="Undelivered Bills by Staff, Feeder, and Area Office",
                 labels={'Staff': 'Staff', 'UndeliveredBills': 'Undelivered Bills'})
    st.plotly_chart(fig)

    # Undelivered Bills by Area Office and Feeder
    feeder_undelivered_query = f"""
    SELECT feeder.feeder_name AS Feeder,
           areaoffice.area_office AS AreaOffice,
           COUNT(billdeliverydev_check.AccountNumber) AS UndeliveredBills
    FROM billdeliverydev_check
    INNER JOIN users ON users.ID = billdeliverydev_check.postedby
    JOIN feeder ON feeder.feederid = users.feederid
    JOIN areaoffice ON areaoffice.aoid = users.AreaOffice
    WHERE billdeliverydev_check.trans_date BETWEEN '{start_date}' AND '{end_date}'
      AND billdeliverydev_check.status = 'Not Delivered'
      AND users.Role = 'nmd'
    GROUP BY Feeder
    ORDER BY AreaOffice
    """
    feeder_undelivered_data = pd.read_sql_query(feeder_undelivered_query, conn)

    # Display the report title
    st.markdown("## Undelivered Bills by Feeder and Area Office - (May 2024)")

    # Plot bar chart
    fig = px.bar(feeder_undelivered_data, x='Feeder', y='UndeliveredBills', color='AreaOffice',
                 title="Undelivered Bills by Feeder and Area Office",
                 labels={'Feeder': 'Feeder', 'UndeliveredBills': 'Undelivered Bills'})
    st.plotly_chart(fig)

    st.markdown("### Detailed Data View")
    st.dataframe(bill_data)
    time.sleep(1)
