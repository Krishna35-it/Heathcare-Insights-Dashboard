import streamlit as st
import pandas as pd
import numpy as np
import pymysql
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')


mydb = pymysql.connect(
    host ="localhost",
    user = "root",
    password = "root",
    database = "healthcare_insights",
    autocommit=True
)
mycursor = mydb.cursor()

st.title("Heathcare Insights Dashboard")
page = st.sidebar.radio("***Navigation***",["Home","Business Case Study"])
if page =="Home":
    st.header("Please Navigate to Business Case Study")
elif page == "Business Case Study":
    st.markdown("<h1 style='color:red'>Business Use Case</h1>", unsafe_allow_html=True)

    st.markdown('<h2 style="color:black;">1) Diagnosis Frequency Over Years</h2>', unsafe_allow_html=True)
    freq = """
    SELECT 
        YEAR(Admit_Date) AS Year,
        Diagnosis, 
        COUNT(*) AS Frequency
    FROM 
        health
    GROUP BY 
        YEAR(Admit_Date), Diagnosis
    ORDER BY 
        Year ASC, Frequency DESC;
    """
    mycursor.execute(freq)
    col_buc1 = [column[0] for column in mycursor.description]
    res_buc1 = mycursor.fetchall()
    freq1 = pd.DataFrame(res_buc1,columns=col_buc1)
    plt.figure(figsize=(5,3))
    sns.barplot(data = freq1,x='Year',y='Frequency',hue='Diagnosis',palette = 'viridis')
    plt.title("Diagnosis Frequency over the years")
    plt.xlabel("Year")
    plt.ylabel("Frequency")
    plt.xticks(rotation = 45)
    plt.legend(title="Diagnosis")
    plt.grid(axis='y')
    st.pyplot(plt)

    st.markdown('<h2 style="color:black;">2) Identifying the Patient Time Visits</h2>', unsafe_allow_html=True)
    visits = """
    SELECT 
        DATE_FORMAT(Admit_Date,'%Y-%m-%d') as Admit_Date,
        YEAR(Admit_Date) AS Year,
        COUNT(*) AS Visit_Count
    FROM 
        health
    GROUP BY 
        Admit_Date, YEAR(Admit_Date) 
    ORDER BY 
        Visit_Count DESC,YEAR(Admit_Date) DESC,Admit_Date DESC;
    """
    mycursor.execute(visits)
    col_vis = [column[0] for column in mycursor.description]
    res_vis = mycursor.fetchall()
    visits_df = pd.DataFrame(res_vis,columns = col_vis)

    visits_df = visits_df.sort_values("Admit_Date")
    plt.figure(figsize=(10,3))
    sns.lineplot(data=visits_df,x='Admit_Date',y='Visit_Count',marker='o',color = 'blue')
    plt.title('Dialy Hospital Visit Count',fontsize = 14,color = 'red')
    plt.xlabel('Admit Date',fontsize = 12,color = 'red')
    plt.ylabel('Visit Count',fontsize = 12,color = 'red')
    plt.xticks(visits_df["Admit_Date"][::30], rotation=45) #Provides 30 day window in x-axis
    plt.grid(True)
    st.pyplot(plt)

    #Measure admission and discharge trends over time.
    st.markdown('<h2 style="color:black;">3) Admissions Vs Discharges Over Times</h2>', unsafe_allow_html=True)
    admis_trends = """
    SELECT 
        DATE_FORMAT(Admit_Date,'%Y-%m-%d') AS Admit_Date,
        COUNT(*) AS Admissions,
        (SELECT COUNT(*) 
        FROM health h2 
        WHERE DATE(h2.Discharge_Date) = DATE(h1.Admit_Date)) AS Discharges
    FROM 
        health h1
    GROUP BY 
        Admit_Date
    ORDER BY 
        Admit_Date ASC;
    """
    mycursor.execute(admis_trends)
    col_trend = [column[0] for column in mycursor.description]
    res_trend = mycursor.fetchall()
    admis_trends_df = pd.DataFrame(res_trend,columns=col_trend)

    plt.figure(figsize=(14,6))
    sns.lineplot(data=admis_trends_df,x='Admit_Date',y='Admissions',label="Admissions",marker = 'o',color='blue')
    sns.lineplot(data=admis_trends_df,x='Admit_Date',y='Discharges',label='Discharges',color='red',marker='o')
    plt.title('Admission vs Discharges Over Time', fontsize = 14)
    plt.xlabel('Admit Date',fontsize=12)
    plt.ylabel('Count',fontsize = 12)
    plt.legend(title='Category')
    plt.xticks(admis_trends_df["Admit_Date"][::30], rotation=45)
    plt.grid(True)
    st.pyplot(plt)

    #Monitor facility usage to prevent overcrowding and ensure efficient operations.
    st.markdown('<h2 style="color:black;">4)Facility Usage To Prevent Overcrowding</h2>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:black;">i)Monthly ICU Admissions and Discharges</h3>',unsafe_allow_html=True)
    occupancy = """
    SELECT 
        Months,
        SUM(Monthly_Admissions) AS Monthly_Admissions,
        SUM(Monthly_Discharges) AS Monthly_Discharges
    FROM (
    -- Admissions query
        SELECT 
            DATE_FORMAT(Admit_Date, '%Y-%m') AS Months,
            COUNT(DISTINCT Patient_ID) AS Monthly_Admissions,
            0 AS Monthly_Discharges
    FROM health
    WHERE Bed_Occupancy = 'ICU'
    GROUP BY Months

    UNION ALL

    -- Discharges query
    SELECT 
        DATE_FORMAT(Discharge_Date, '%Y-%m') AS Months,
        0 AS Monthly_Admissions,
        COUNT(DISTINCT Patient_ID) AS Monthly_Discharges
    FROM health
    WHERE Bed_Occupancy = 'ICU'
    GROUP BY Months
    ) AS combined
    GROUP BY Months
    ORDER BY Months ASC;

    """
    mycursor.execute(occupancy)
    col_occ = [column[0] for column in mycursor.description]
    res_occ = mycursor.fetchall()
    occupancy_df = pd.DataFrame(res_occ,columns=col_occ)

    occupancy_df['Months'] = pd.to_datetime(occupancy_df['Months'], format='%Y-%m')

    #This line is used because i got error in x-axis as'2022-12-01 00:00:00' so inorder to get as same as the Months column i used strftime format
    occupancy_df['Months'] = occupancy_df['Months'].dt.strftime('%Y-%m') 

    #Error comes as no numeric data found so using below method to change it to numeric
    #Coerce is used to convert any non-numeric values to NaN and NaN will convert it to 0
    occupancy_df['Monthly_Admissions'] = pd.to_numeric(occupancy_df['Monthly_Admissions'], errors='coerce').fillna(0)
    occupancy_df['Monthly_Discharges'] = pd.to_numeric(occupancy_df['Monthly_Discharges'], errors='coerce').fillna(0)

    plt.figure(figsize=(10, 6))

    #stacked bar chart
    occupancy_df.set_index('Months')[['Monthly_Admissions', 'Monthly_Discharges']].plot(kind='bar', stacked=True, color=['blue', 'red'])

    plt.title('Monthly ICU Admissions and Discharges', fontsize=16)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.xticks(rotation=45)  
    plt.legend(title="ICU Activity")

    plt.tight_layout()
    st.pyplot(plt)

    st.markdown('<h3 style="color:black;">ii)Monthly Private Ward Admissions and Discharges</h3>',unsafe_allow_html=True)
    occ_pvt = """
    SELECT 
        Months,
        SUM(Monthly_Admissions) AS Monthly_Admissions,
        SUM(Monthly_Discharges) AS Monthly_Discharges
    FROM (
    -- Admissions query
        SELECT 
            DATE_FORMAT(Admit_Date, '%Y-%m') AS Months,
            COUNT(DISTINCT Patient_ID) AS Monthly_Admissions,
            0 AS Monthly_Discharges
    FROM health
    WHERE Bed_Occupancy = 'Private'
    GROUP BY Months

    UNION ALL

    -- Discharges query
    SELECT 
        DATE_FORMAT(Discharge_Date, '%Y-%m') AS Months,
        0 AS Monthly_Admissions,
        COUNT(DISTINCT Patient_ID) AS Monthly_Discharges
    FROM health
    WHERE Bed_Occupancy = 'Private'
    GROUP BY Months
    ) AS combined
    GROUP BY Months
    ORDER BY Months ASC;
    """
    mycursor.execute(occ_pvt)
    col1_occ = [column[0] for column in mycursor.description]
    res2_occ = mycursor.fetchall()
    occ_pvt_df = pd.DataFrame(res2_occ,columns=col1_occ)

    occ_pvt_df['Months'] = pd.to_datetime(occ_pvt_df['Months'], format='%Y-%m')

    occ_pvt_df['Months'] = occ_pvt_df['Months'].dt.strftime('%Y-%m')  

    occ_pvt_df['Monthly_Admissions'] = pd.to_numeric(occ_pvt_df['Monthly_Admissions'], errors='coerce').fillna(0)
    occ_pvt_df['Monthly_Discharges'] = pd.to_numeric(occ_pvt_df['Monthly_Discharges'], errors='coerce').fillna(0)

    plt.figure(figsize=(10, 6))

    occ_pvt_df.set_index('Months')[['Monthly_Admissions', 'Monthly_Discharges']].plot(kind='bar', stacked=True, color=['blue', 'red'])

    plt.title('Monthly Private Ward Admissions and Discharges', fontsize=16)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.xticks(rotation=45)  
    plt.legend(title="Private Ward Activity")

    plt.tight_layout()
    st.pyplot(plt)

    st.markdown('<h3 style="color:black;">iii)Monthly General Ward Admissions and Discharges</h3>',unsafe_allow_html=True)
    occ_gen = """
    SELECT 
        Months,
        SUM(Monthly_Admissions) AS Monthly_Admissions,
        SUM(Monthly_Discharges) AS Monthly_Discharges
    FROM (
    -- Admissions query
        SELECT 
            DATE_FORMAT(Admit_Date, '%Y-%m') AS Months,
            COUNT(DISTINCT Patient_ID) AS Monthly_Admissions,
            0 AS Monthly_Discharges
        FROM health
        WHERE Bed_Occupancy = 'General'
        GROUP BY Months

    UNION ALL

    -- Discharges query
    SELECT 
        DATE_FORMAT(Discharge_Date, '%Y-%m') AS Months,
        0 AS Monthly_Admissions,
        COUNT(DISTINCT Patient_ID) AS Monthly_Discharges
    FROM health
    WHERE Bed_Occupancy = 'General'
    GROUP BY Months
    ) AS combined
    GROUP BY Months
    ORDER BY Months ASC;
    """
    mycursor.execute(occ_gen)
    col_gen = [column[0] for column in mycursor.description]
    res_gen = mycursor.fetchall()
    occ_gen_df = pd.DataFrame(res_gen,columns=col_gen)
    
    occ_gen_df['Months'] = pd.to_datetime(occ_gen_df['Months'], format='%Y-%m')

    occ_gen_df['Months'] = occ_gen_df['Months'].dt.strftime('%Y-%m')  

    occ_gen_df['Monthly_Admissions'] = pd.to_numeric(occ_gen_df['Monthly_Admissions'], errors='coerce').fillna(0)
    occ_gen_df['Monthly_Discharges'] = pd.to_numeric(occ_gen_df['Monthly_Discharges'], errors='coerce').fillna(0)

    plt.figure(figsize=(10, 6))
    occ_pvt_df.set_index('Months')[['Monthly_Admissions', 'Monthly_Discharges']].plot(kind='bar', stacked=True, color=['blue', 'red'])
    plt.title('Monthly General Ward Admissions and Discharges', fontsize=16)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.xticks(rotation=45) 
    plt.legend(title="General Ward Activity")

    plt.tight_layout()
    st.pyplot(plt)