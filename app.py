
from app.data_loader import (
    fetch_data
)

from app.data_processor import (
    process_lap_data, 
    get_best_lap_times, 
    get_race_lap_times,
    build_race_df
)

import pandas as pd
import numpy as np

import streamlit as st

# Set the page configuration
st.set_page_config(page_title="Formula 1 Data Analysis", layout="wide", page_icon=":racing_car:")
st.title("Formula 1 Data Analysis")
st.markdown("*This app allows you to explore Formula 1 data.*\n\n")

col1, col2, col3 = st.columns(3)

with col1:
    # Create a year-range selector
    available_years = range(2023, 2026)
    selected_year = st.selectbox("**Select Year**",
                                 options=available_years, 
                                 index=len(available_years) - 1)

# Get the list of meetings for the selected year
meetings_df = fetch_data("meetings", {'year': selected_year})
meetings_df['full_name'] = meetings_df['circuit_short_name'].str.cat(" - " + meetings_df['meeting_name'], na_rep='')

with col2:
# Create a selection box for the meeting concatenated with the meeting name
    selected_meeting = st.selectbox("**Select Meeting**",
                                    options=meetings_df['full_name'].tolist(),
                                    index=len(meetings_df['full_name']) - 2)
    meeting_id = meetings_df[meetings_df['full_name'] == selected_meeting]['meeting_key'].values[0]
    st.write("Selected Meeting Key:", meeting_id)

# Get the list of sessions for the selected meeting
sessions_df = fetch_data("sessions", {'meeting_key': meeting_id})

with col3:
# Create a selection box for the session
    selected_session = st.selectbox("**Select Session**",
                                    options=sessions_df['session_name'].tolist(),
                                    index=len(sessions_df['session_name']) - 1)
    session_id = sessions_df[sessions_df['session_name'] == selected_session]['session_key'].values[0]
    st.write("Selected Session Key:", session_id)

tab1, tab2 = st.tabs(["Overview", "Stints"])

with tab1:
    # Get the list of drivers for the selected session
    drivers_df = fetch_data("drivers", {'session_key': session_id})

    # Get the lap times for the selected session
    times_df = process_lap_data(fetch_data("laps", {'session_key': session_id}))

    # Get the results for the selected session
    results_df = fetch_data("session_result", {'session_key': session_id})

    # Display the appropriate DataFrame depending on the selected session
    st.markdown(f"### Here are the results of the ***{selected_meeting} {selected_session}***")

    if selected_session in ['Race', 'Sprint']:
        times_df = get_race_lap_times(times_df)
        df, config, col_order = build_race_df(drivers_df, times_df, results_df)
        st.dataframe(df, hide_index=True, column_config=config, column_order=col_order, height=725)
    else:
        st.dataframe(get_best_lap_times(times_df))

with tab2:
    st.markdown("### Stints Overview")
    st.write("*Coming soon...*")