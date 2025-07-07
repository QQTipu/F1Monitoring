import pandas as pd
import streamlit as st

def process_lap_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare lap data for visualization.

    - Filters out laps without duration.
    - Sorts by driver number and lap number.

    Args:
        df (pd.DataFrame): Raw lap data from API.

    Returns:
        pd.DataFrame: Cleaned and sorted lap data.
    """
    if df.empty:
        return df

    df = df[df['lap_duration'].notna()]  # Drop laps missing duration info (i.e. retirements or red flags)
    df = df.sort_values(['driver_number', 'lap_number'])  # Sort for logical order in lap-time visualization
    return df

def get_best_lap_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get the best lap times for each driver.

    Args:
        df (pd.DataFrame): Cleaned lap data.

    Returns:
        pd.DataFrame: DataFrame with best lap times per driver.
    """
    if df.empty:
        return pd.DataFrame()

    best_laps = df.loc[df.groupby('driver_number')['lap_duration'].idxmin()]
    return best_laps[['driver_number', 'lap_duration', 'duration_sector_1', 'duration_sector_2', 'duration_sector_3', 'i1_speed', 'i2_speed', 'st_speed']].reset_index(drop=True)

def get_race_lap_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get the mean lap time, mean speed, and the best sector times for each driver.

    Args:
        df (pd.DataFrame): Cleaned lap data.

    Returns:
        pd.DataFrame: DataFrame with mean lap times per driver.
    """
    if df.empty:
        return pd.DataFrame()

    # Calculate the mean lap duration 
    best_laps = df.groupby('driver_number')['lap_duration'].min().reset_index()
    best_laps.columns = ['driver_number', 'best_lap_duration']

    # Calculate the mean speed using 3 speed tracking points
    mean_speeds = df.groupby('driver_number')[['i1_speed', 'i2_speed', 'st_speed']].mean().reset_index()
    mean_speeds.columns = ['driver_number', 'mean_i1_speed', 'mean_i2_speed', 'mean_st_speed']

    # Calculate the best sector times
    best_sectors = df.groupby('driver_number')[['duration_sector_1', 'duration_sector_2', 'duration_sector_3']].min().reset_index()
    best_sectors.columns = ['driver_number', 'best_sector_1', 'best_sector_2', 'best_sector_3']

    result = best_laps.merge(mean_speeds, on='driver_number').merge(best_sectors, on='driver_number')
    
    return result

def build_race_df(drivers_df: pd.DataFrame, times_df: pd.DataFrame, results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a DataFrame for the race with driver, lap, and result information.

    Args:
        drivers_df (pd.DataFrame): DataFrame with driver information.
        times_df (pd.DataFrame): DataFrame with lap time information.
        results_df (pd.DataFrame): DataFrame with race result information.

    Returns:
        pd.DataFrame: Merged DataFrame with all relevant information.
    """
    merged_df = drivers_df.merge(results_df, 
                                 on='driver_number', 
                                 how='left')
    monitoring_df = merged_df.merge(times_df,
                                    on='driver_number',
                                    how='left')
    monitoring_df = monitoring_df.sort_values(by=['position', 'number_of_laps'], ascending=[True, False])
    
    config = {'position': st.column_config.NumberColumn('Position', width='small', format="%d", help="Position of the driver", pinned=True, ),
              'headshot_url': st.column_config.ImageColumn('Headshot', width='small', pinned=True),
              'full_name': st.column_config.TextColumn('Driver', help="Full name of the driver", pinned=True),
              'team_name': st.column_config.TextColumn('Team', help="Team name of the driver"),
              'points': st.column_config.NumberColumn('Points', width='small', format="%d", help="Points scored by the driver"),
              'time_gap': st.column_config.TimeColumn('Time Gap', format='iso8601', help="Time gap from the leader"),
              'number_of_laps': st.column_config.NumberColumn('Laps', width='small', format="%d", help="Number of laps completed by the driver"),
              'best_lap_duration': st.column_config.NumberColumn('Best Lap Duration', format="%.3f", help="Best lap duration of the driver"),
              'mean_i1_speed': st.column_config.NumberColumn('Mean Interval 1 Speed', format="%.2f", help="The mean speed of the car, in km/h, at the first intermediate point on the track."),
              'mean_i2_speed': st.column_config.NumberColumn('Mean Interval 2 Speed', format="%.2f", help="The mean speed of the car, in km/h, at the second intermediate point on the track."),
              'mean_st_speed': st.column_config.NumberColumn('Mean ST Speed', format="%.2f", help="The mean speed of the car, in km/h, at the speed trap, which is a specific point on the track where the highest speeds are usually recorded."),
              'best_sector_1': st.column_config.NumberColumn('Best Sector 1', format="%.3f", help="Best time in sector 1"),
              'best_sector_2': st.column_config.NumberColumn('Best Sector 2', format="%.3f", help="Best time in sector 2"),
              'best_sector_3': st.column_config.NumberColumn('Best Sector 3', format='%.3f', help="Best time in sector 3")
    }
    
    col_order = ['position', 'headshot_url', 'full_name',
                 'team_name', 'points', 'time_gap', 'best_lap_duration', 
                 'best_sector_1', 'best_sector_2', 'best_sector_3', 
                 'mean_i1_speed', 'mean_i2_speed', 'mean_st_speed', 
                 'number_of_laps']

    return monitoring_df, config, col_order