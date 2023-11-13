import pandas as pd


def filter_thermal_comfort_dashboard(df):
    df['tc_timestamp'] = pd.to_datetime(df['tc_timestamp'], unit='s')

    df = df.sort_values(by='tc_timestamp', ascending=False)

    df['time_diff'] = df['tc_timestamp'].diff(-1).abs().dt.total_seconds()

    first_gap_index = df[df['time_diff'] > 60].first_valid_index()

    df = df.loc[:first_gap_index] if first_gap_index is not None else df

    df = df.sort_values(by='tc_timestamp', ascending=True)

    df.drop(columns=['time_diff'], inplace=True)

    df['tc_timestamp'] = df['tc_timestamp'].astype('int64') // 10 ** 9

    thermal_comfort = [tuple(row) for row in df.to_numpy()]

    return thermal_comfort
