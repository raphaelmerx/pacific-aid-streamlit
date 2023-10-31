import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime as dt
import humanize


st.title("Pacific Aid Map data")


DATE_COLUMNS = ["expectedstartdate", "completiondate", "data collection date"]
DATA_URL = "./Pacific_Aid_Map_Database.csv.gz"


@st.cache_data
def load_data(nrows=None):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    for date_column in DATE_COLUMNS:
        # converting column to a numeric type first
        data[date_column] = pd.to_numeric(data[date_column], errors="coerce")
        # get datetime from Excel format, then only keep date
        data[date_column] = pd.to_datetime(
            data[date_column], unit="D", origin="1899-12-30"
        )

    data["final transaction date"] = pd.to_datetime(data["final transaction date"])
    return data


data_load_state = st.text("Loading data...")
data = load_data(None)
data_load_state.text("Data loaded")

## FILTERING

filtered_data = data

selected_transaction_type = st.sidebar.radio(
    "Transaction type", ["Spent", "Committed"], index=0
)
filtered_data = filtered_data[
    filtered_data["spent/committed"] == selected_transaction_type
]

unique_donors = data["donor"].unique()
unique_donors.sort()
selected_donor = st.sidebar.selectbox("Donor", unique_donors, index=None)
if selected_donor:
    filtered_data = filtered_data[filtered_data["donor"] == selected_donor]

unique_recipients = data["recipient"].unique()
unique_recipients.sort()
selected_recipient = st.sidebar.selectbox("Recipient", unique_recipients, index=None)
if selected_recipient:
    filtered_data = filtered_data[filtered_data["recipient"] == selected_recipient]

unique_sectors = data["lowy sector"].unique()
unique_sectors.sort()
selected_sector = st.sidebar.selectbox("Sector", unique_sectors, index=None)
if selected_sector:
    filtered_data = filtered_data[filtered_data["lowy sector"] == selected_sector]

unique_aid_type = data["flow type"].unique()
unique_aid_type.sort()
selected_aid_type = st.sidebar.selectbox("Aid type", unique_aid_type, index=None)
if selected_aid_type:
    filtered_data = filtered_data[filtered_data["flow type"] == selected_aid_type]

# year filter: from 2008 to 2021
year_range = st.sidebar.slider("Year range", 2008, 2021, (2008, 2021), format="%d")
# filter using column "final transaction date"
if year_range:
    filtered_data = filtered_data[
        (filtered_data["final transaction date"].dt.year >= year_range[0])
        & (filtered_data["final transaction date"].dt.year <= year_range[1])
    ]


## END FILTERING

## BAR CHART value by year

st.subheader(f"{selected_transaction_type} by year")

# get data
grouped_data = filtered_data.groupby(filtered_data["final transaction date"].dt.year)[
    "usd constant - transaction value"
].sum()
sum_value_df = pd.DataFrame(
    {
        "Year": grouped_data.index.astype(str),
        "Value": grouped_data.values,
    }
)
sum_value_df = sum_value_df.set_index("Year")


# add humanized value column
sum_value_df["Humanized_Value"] = sum_value_df["Value"].apply(humanize.intword)

# Create the Plotly figure
fig = px.bar(
    sum_value_df.reset_index(),
    x="Year",
    y="Value",
    labels={"Value": "Value (in USD)"},
    text="Humanized_Value",
)
fig.for_each_trace(
    lambda trace: trace.update(hovertemplate="Year: %{x}<br>Value: %{text}")
)

# Display the Plotly chart in Streamlit
st.plotly_chart(fig)

# END BAR CHART value by year

## BAR CHART value by sector

st.subheader(f"{selected_transaction_type} by sector")

# get data
grouped_data = filtered_data.groupby(filtered_data["lowy sector"])[
    "usd constant - transaction value"
].sum()
sum_value_df = pd.DataFrame(
    {
        "Sector": grouped_data.index.astype(str),
        "Value": grouped_data.values,
    }
)
sum_value_df = sum_value_df.set_index("Sector")


# add humanized value column
sum_value_df["Humanized_Value"] = sum_value_df["Value"].apply(humanize.intword)

# Create the Plotly figure
fig = px.pie(
    sum_value_df.reset_index(),
    names="Sector",
    values="Value",
    title=None,
    labels={"Value": "Value (in USD)"},
    custom_data=["Humanized_Value"],
)
fig.for_each_trace(
    lambda trace: trace.update(
        hovertemplate="Sector: %{label}<br>Value: %{customdata[0]}<br>Percentage: %{percent}"
    )
)

# Display the Plotly chart in Streamlit
st.plotly_chart(fig)

# END BAR CHART value by sector

col1, col2 = st.columns(2)

# BEGIN: value by donor table
with col1:
    grouped_data = filtered_data.groupby(filtered_data["donor"])[
        "usd constant - transaction value"
    ].sum()
    sum_value_df = pd.DataFrame(
        {
            "Donor": grouped_data.index.astype(str),
            "Value": grouped_data.values,
        }
    )
    sum_value_df = sum_value_df.set_index("Donor")
    sum_value_df = sum_value_df.sort_values(by=["Value"], ascending=False)
    sum_value_df["Value"] = sum_value_df["Value"].astype(int)

    st.subheader(f"{selected_transaction_type} by donor")
    st.write(sum_value_df)

# END: value by donor table

# BEGIN: value by recipient
with col2:
    grouped_data = filtered_data.groupby(filtered_data["recipient"])[
        "usd constant - transaction value"
    ].sum()
    sum_value_df = pd.DataFrame(
        {
            "recipient": grouped_data.index.astype(str),
            "Value": grouped_data.values,
        }
    )
    sum_value_df = sum_value_df.set_index("recipient")
    sum_value_df = sum_value_df.sort_values(by=["Value"], ascending=False)
    sum_value_df["Value"] = sum_value_df["Value"].astype(int)

    st.subheader(f"{selected_transaction_type} by recipient")
    st.write(sum_value_df)

# END: value by recipient table

# BEGIN: value by project

# Group by "2023 project identifier" and aggregate
grouped_data = (
    filtered_data.groupby("2023 project identifier")
    .agg(
        {
            "usd constant - transaction value": "sum",
            "project title": "first",  # Assuming all titles are the same within each group
            "donor": "first",  # Assuming all donors are the same within each group
            "recipient": "first",  # Assuming all recipients are the same within each group
            "expectedstartdate": "first",  # Assuming all start dates are the same within each group
            "completiondate": "first",  # Assuming all completion dates are the same within each group
        }
    )
    .reset_index()
)

# Extract the year from date columns
grouped_data["expectedstartdate"] = (
    grouped_data["expectedstartdate"].dt.year.dropna().astype("Int64").astype(str)
)
grouped_data["completiondate"] = (
    grouped_data["completiondate"].dt.year.dropna().astype("Int64").astype(str)
)

# Create a DataFrame for display
sum_value_df = pd.DataFrame(
    {
        "Project": grouped_data["2023 project identifier"].astype(str),
        "Title": grouped_data["project title"],
        "Donor": grouped_data["donor"],
        "Recipient": grouped_data["recipient"],
        "Start Year": grouped_data["expectedstartdate"],
        "Completion Year": grouped_data["completiondate"],
        "Value": grouped_data["usd constant - transaction value"],
    }
)
sum_value_df = sum_value_df.sort_values(by=["Value"], ascending=False)
sum_value_df["Value"] = sum_value_df["Value"].astype(int)

# Set the index to "Project"
sum_value_df = sum_value_df.set_index("Project")

st.subheader(f"{selected_transaction_type} by project")
st.write(sum_value_df)


# END: value by project

## RAW DATA
if st.checkbox("Show list of transactions"):
    st.subheader("All transactions matching filters")
    st.write(filtered_data)
