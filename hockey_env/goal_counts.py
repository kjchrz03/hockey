import requests
import pandas as pd
import numpy as np
import asyncio
import aiohttp
import nest_asyncio
import subprocess

# List of libraries to install
libraries = ["requests", "pandas", "numpy", "aiohttp", "nest_asyncio"]

# Run the pip install command for each library
for lib in libraries:
    subprocess.run(["pip", "install", lib])

# Apply nest_asyncio to allow nested event loops in Jupyter notebooks
nest_asyncio.apply()

# Constants
START_GAME_ID = 2024020001
END_GAME_ID = 2024021307
BASE_URL = "https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId="
PXP_URL = "https://api-web.nhle.com/v1/gamecenter/"
PXP_SUFFIX = "/play-by-play"

# Create game URLs DataFrame
game_data = [{"game_id": game_id, "shift_url": f"{BASE_URL}{game_id}", "pxp_url": f"{PXP_URL}{game_id}{PXP_SUFFIX}"} 
             for game_id in range(START_GAME_ID, END_GAME_ID + 1)]
game_df = pd.DataFrame(game_data)

# Asynchronous function to fetch shift data
async def fetch_shift_data(session, shift_url):
    try:
        async with session.get(shift_url) as response:
            response.raise_for_status()  # Raise an error for bad responses
            json_data = await response.json()
            details = pd.DataFrame(json_data['data'])
            if not details.empty:
                details['player_name'] = details['firstName'] + " " + details['lastName']
                mask_505 = details['typeCode'] == 505
                details.loc[mask_505, 'eventDetails'] = details.loc[mask_505, 'eventDetails'].fillna('unassisted').replace(r'^\s*$', 'unassisted', regex=True)
                assists = details.loc[mask_505, 'eventDetails'].str.split(', ', expand=True)
                details.loc[mask_505, ['assist_1', 'assist_2']] = assists
                return details
            return pd.DataFrame()  # Return empty DataFrame if no data
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

# Fetch all shift data asynchronously
async def fetch_all_shift_data(game_df):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_shift_data(session, row['shift_url']) for _, row in game_df.iterrows()]
        return await asyncio.gather(*tasks)

# Run the async tasks and collect the results
all_shifts_data = asyncio.run(fetch_all_shift_data(game_df))
all_shifts = pd.concat(all_shifts_data, ignore_index=True)

# Create a dictionary to make shot data more readable 
shot_code_dictionary = {
    801: 'slap shot', 802: 'snap shot', 803: 'wrist shot',
    804: 'wrap-around', 805: 'tip-in', 806: 'backhanded shot',
    807: 'deflected in', 808: 'bat shot', 809: 'cradle/Michigan',
    810: 'poke', 811: 'between the legs'
}
all_shifts['shot_type'] = all_shifts['detailCode'].map(shot_code_dictionary)
all_shifts['gameId'] = all_shifts['gameId'].astype(str)

# Filter and prepare DataFrames for assists and goals
assist_1 = all_shifts[all_shifts['assist_1'].notna()]
assist_2 = all_shifts[all_shifts['assist_2'].notna()]

shifts_df = all_shifts[['gameId', 'period', 'shiftNumber', 'startTime', 'eventNumber', 'playerId', 'player_name', 
                         'teamId', 'teamName', 'typeCode', 'assist_1', 'assist_2', 'shot_type', 'eventDescription']]
goal_shifts = shifts_df[shifts_df['typeCode'].isin([505])]

# Prepare totals for goals and assists
season_goal_totals = goal_shifts.groupby(['playerId', 'player_name', 'gameId'])['eventNumber'].count().reset_index(name='g')
season_assist1_total = assist_1.groupby(['gameId', 'assist_1', 'eventNumber', 'period']).size().reset_index(name='a1')
season_assist2_total = assist_2.groupby(['gameId', 'assist_2', 'eventNumber', 'period']).size().reset_index(name='a2')

# Merge assist totals and goal totals
season_assist1_total = season_assist1_total.rename(columns={'assist_1': 'player_name'})
season_assist2_total = season_assist2_total.rename(columns={'assist_2': 'player_name'})
season_assists = season_assist1_total.merge(season_assist2_total, on=['player_name', 'gameId'], how='outer', suffixes=('_assist1', '_assist2'))
season_totals = season_goal_totals.merge(season_assists, on=['player_name', 'gameId'], how="outer")

# Fill NaN values with 0 and calculate aggregates
season_totals.fillna(0, inplace=True)
season_totals = season_totals.groupby(['playerId', 'player_name']).agg(
    g=('g', 'sum'),
    gp=('gameId', 'nunique'),
    a1=('a1', 'sum'),
    a2=('a2', 'sum')
).reset_index()

# Calculate goals per game and total points
season_totals['gpg'] = season_totals['g'] / season_totals['gp']
season_totals['p'] = season_totals['g'] + season_totals['a1'] + season_totals['a2']



