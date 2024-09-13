from hockey_rink import NHLRink, RinkImage
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf

pd.options.mode.chained_assignment = None

# Load datasets
all_players_24 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\skaters_2024.csv")
mult_teams_24 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\split_times_2024.csv")
goals_24 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\goals_2024.csv")

all_players_23 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\skaters_2023.csv")
mult_teams_23 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\split_times_2023.csv")
goals_23 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\goals_2023.csv")

all_players_22 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\skaters_2022.csv")
mult_teams_22 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\split_times_2022.csv")
goals_22 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\goals_2022.csv")

ages_22 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\player_ages_22.csv")
ages_23 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\player_ages_23.csv")
ages_24 = pd.read_csv("C:\\Users\\Karoline Sears\\Desktop\\stats\\2024 report card\\player_ages_24.csv")

# Store datasets in lists
ages_list = [ages_22, ages_23, ages_24]
player_usage_list = [all_players_22, all_players_23, all_players_24]
multi_teams_list = [mult_teams_22, mult_teams_23, mult_teams_24]
goals_list = [goals_22, goals_23, goals_24]

# Function to process each dataset
def process_data(ages, all_players, multi_teams, goals):
    
    individual_stats = all_players[['Player', 'CF', 'CA', 'GF', 'GA', 'GF%', 'xGF', 'xGA', 'HDGF%', 'PDO']]
    goals = goals[['Player', 'Goals', 'Total Assists', 'First Assists', 'Second Assists', 'Total Points', 'IPP', 'Shots', 'SH%', 'ixG', 'iCF', 'iHDCF', 'Rush Attempts','Rebounds Created', 'Giveaways', 'Takeaways', 'Hits', 'Hits Taken', 'Shots Blocked', 'Faceoffs %']]
    player_stats = goals.merge(individual_stats, on="Player")
    
    # All Players usage to calculate the overall percentile
    all_toi = all_players[['Player', 'Team', 'Position', 'GP', 'TOI']]
    all_toi = all_toi.query('GP >= 30')
    all_toi.loc[:, 'TOI'] = round(all_toi['TOI'], 2)


    all_toi = all_toi.merge(ages, on=('Player', 'Position'), how='left')
    all_toi = all_toi[['Player', 'Team_x', 'Position', 'GP', 'TOI', 'Age']]
    all_toi = all_toi.rename(columns={'Team_x': 'Team'})

    # Total TOI Percentile
    all_toi['total_percentile'] = all_toi['TOI'].rank(pct=True)
    all_toi['Skater'] = np.where(all_toi['Position'] == "D", "D", "F")

    # Multi-team players
    multiple_teams = all_toi.query('Team.str.contains(",")')
    multiple_teams = multiple_teams.explode('Team').reset_index(drop=True)
    multi_teams = multi_teams[['Player', 'Team', 'GP', 'TOI']]
    multi_teams['atoi'] = round((multi_teams['TOI']/multi_teams['GP']),2)
    multi_teams['TOI'] = round(multi_teams['TOI'],2)
    multi_teams = multi_teams[multi_teams.duplicated('Player', keep=False)]
    multi_teams = multi_teams.sort_values(by=['Player', 'GP'], ascending=[True, False]).reset_index()

    multiple_teams = multiple_teams.merge(multi_teams, on="Player", how="left")
    multiple_teams = multiple_teams[['Player', 'Team_y', 'Position', 'GP_x', 'GP_y', 'TOI_x', 'TOI_y', 'atoi_x', 'atoi_y', 'Age', 'total_percentile', 'Skater' ]]
    multiple_teams = multiple_teams.rename(columns={'Team_y': 'Team',
                                       'TOI_x':'TOI', 'TOI_y':'team_TOI', 'GP_x':'GP', 'GP_y':'team_gp', 'atoi_x':'atoi', 'atoi_y':'team_atoi'})

    # Single-team players
    single_teams = all_toi.query('~Team.str.contains(",")')
    all_players = pd.concat([single_teams, multiple_teams], ignore_index=True)

    all_players['team_TOI'] = np.where(pd.isnull(all_players['team_TOI']), all_players['TOI'], all_players['team_TOI'])
    all_players['team_gp'] = np.where(pd.isnull(all_players['team_gp']), all_players['GP'], all_players['team_gp'])
    all_players['team_atoi'] = np.where(all_players['team_atoi'].isnull(), all_players['atoi'],all_players['team_atoi'])
    all_players['adj_toi'] = all_players['team_atoi']*all_players['GP']

    # Quality of Team - Rank Among Forwards
    def calculate_percentile_rank_f(player_time_on_ice, player_position, player_team):
        filtered_data = all_players[(all_players["Skater"] == "F") & (all_players["Team"] == player_team)]
        forwards_time_on_ice = filtered_data["adj_toi"]
        return stats.percentileofscore(forwards_time_on_ice, player_time_on_ice)

    all_players["QoTF"] = all_players.apply(lambda row: calculate_percentile_rank_f(row["adj_toi"], row["Skater"], row["Team"]), axis=1)

    # Quality of Team - Rank Among Defensemen
    def calculate_percentile_rank_d(player_time_on_ice, player_position, player_team):
        filtered_data = all_players[(all_players["Skater"] == "D") & (all_players["Team"] == player_team)]
        defense_time_on_ice = filtered_data["adj_toi"]
        return stats.percentileofscore(defense_time_on_ice, player_time_on_ice)

    all_players["QoTD"] = all_players.apply(lambda row: calculate_percentile_rank_d(row["adj_toi"], row["Skater"], row["Team"]), axis=1)

    # Specific name to keep
    name_to_keep = 'Sebastian Aho'
    duplicates_except_specific = all_players[all_players['Player'] != name_to_keep]
    duplicated_names = duplicates_except_specific[duplicates_except_specific.duplicated(subset='Player')]['Player']
    result_df = all_players[all_players['Player'].isin(duplicated_names)]

    
    result_df.loc[:, 'team_no'] = result_df.groupby('Player').cumcount() + 1
    pivoted_df = result_df.pivot(index='Player', columns='team_no', values=['Team', 'adj_toi'])
    pivoted_df.columns = [f'{col[0]} {col[1]}' for col in pivoted_df.columns]
    pivoted_df.reset_index(inplace=True)
    pivoted_df = pivoted_df.fillna(0)
    all_players = all_players.merge(pivoted_df, on="Player", how="left")

    # Quality of Competition - Forwards
    def calculate_qoc_f(player_row):
        filtered_data = all_players[(all_players["Skater"] == "F") & (all_players["Player"] != player_row["Player"]) & (all_players["Team"] != player_row["Team"])]
        grouped_data = filtered_data.groupby("Player")["adj_toi"].mean()
        return stats.percentileofscore(grouped_data, player_row["adj_toi"])

    all_players["QoCF"] = all_players.apply(lambda row: calculate_qoc_f(row), axis=1)

    # Quality of Competition - Defense
    def calculate_qoc_d(player_row):
        filtered_data = all_players[(all_players["Skater"] == "D") & (all_players["Player"] != player_row["Player"]) & (all_players["Team"] != player_row["Team"])]
        grouped_data = filtered_data.groupby("Player")["adj_toi"].mean()
        return stats.percentileofscore(grouped_data, player_row["adj_toi"])

    all_players["QoCD"] = all_players.apply(lambda row: calculate_qoc_d(row), axis=1)


    all_players['team_no'] = all_players.groupby('Player').cumcount() + 1
    all_players['team_count'] = np.where(pd.isnull(all_players['Team 1']), all_players['Team'], "Multi")

    mult_team_quals = all_players.query('team_count == "Multi"')
    mult_team_quals.loc[:, 'team_no'] = mult_team_quals.groupby('Player').cumcount() + 1

    # Pivot the DataFrame to reshape it and include QoC
    pivot_competition_f = mult_team_quals.pivot(index='Player', columns='team_no', values=['Team', 'adj_toi', 'QoCF', 'QoTF'])
    pivot_competition_d = mult_team_quals.pivot(index='Player', columns='team_no', values=['Team', 'adj_toi', 'QoCD', 'QoTD'])

    # Rename columns to 'Team 1', 'Team 2', 'TOI Team 1', 'TOI Team 2', etc.
    pivot_competition_f.columns = [f'{col[0]} {col[1]}' for col in pivot_competition_f.columns]
    pivot_competition_d.columns = [f'{col[0]} {col[1]}' for col in pivot_competition_d.columns]

    # Reset index to make 'Player' a column again
    pivot_competition_f.reset_index(inplace=True)
    pivot_competition_d.reset_index(inplace=True)

    # Replace NaN values with 0
    pivot_competition_f = pivot_competition_f.fillna(0)
    pivot_competition_d = pivot_competition_d.fillna(0)

    # Select and rename columns as required for final output
    pivot_competition_d = pivot_competition_d[['Player', 'QoCD 1', 'QoCD 2', 'QoCD 3', 'QoTD 1', 'QoTD 2', 'QoTD 3']]

    # Merge the pivoted DataFrames back together
    weighted_df = pd.merge(pivot_competition_f, pivot_competition_d, on='Player')

    # Identify the specific name to keep (the one with two different players)
    name_to_keep = 'Sebastian Aho'

    # Create a mask to keep the first occurrence of all player names except for the specific name
    mask = all_players['Player'] != name_to_keep
    filtered_players = all_players[mask].drop_duplicates(subset='Player', keep='first')

    # Append the rows with the specific name to the filtered DataFrame
    filtered_players = pd.concat([filtered_players, all_players], ignore_index=True).drop_duplicates()

    player_usage = filtered_players.merge(weighted_df, on="Player", how="left")

    player_usage['total_percentile'] = round(player_usage['total_percentile'] * 100, 2)
    columns_to_round = ['QoCF', 'QoCD', 'QoTF', 'QoTD', 'w_QoCF', 'w_QoCD', 'w_QoTF', 'w_QoTD']

    player_usage[columns_to_round] = player_usage[columns_to_round].apply(lambda x: round(x, 2))


    player_usage['toughest_min'] = player_usage['QoCF']+player_usage['QoCD']+player_usage['QoTF']+player_usage['QoTD'] 

    player_usage = player_usage.sort_values(['toughest_min', 'TOI'], ascending=[False, False]).reset_index(drop=True)

    player_usage = player_usage.merge(player_stats, on="Player")

    return player_usage

# Process each dataset
for i, (ages, player_usage, multi_teams, goals) in enumerate(zip(ages_list, player_usage_list, multi_teams_list, goals_list)):
    processed_data = process_data(ages, player_usage, multi_teams, goals)
    output_filename = f'processed_players_{2022 + i}.csv'
    processed_data.to_csv(output_filename, index=False)
    print(f'Dataset for {2022 + i} processed and saved as {output_filename}')

# Load the processed datasets
processed_2022 = pd.read_csv('processed_players_2022.csv')
processed_2023 = pd.read_csv('processed_players_2023.csv')
processed_2024 = pd.read_csv('processed_players_2024.csv')

# Add a column to identify the year
processed_2022['Year'] = 2022
processed_2023['Year'] = 2023
processed_2024['Year'] = 2024

# Combine the datasets into a single DataFrame
all_years_df = pd.concat([processed_2022, processed_2023, processed_2024], ignore_index=True).drop_duplicates()

# Save the combined DataFrame to a new CSV file (optional)
all_years_df.to_csv('combined_players_2022_2024.csv', index=False)

# Example comparison: Compare TOI for a specific player across years
player_name = 'Elias Lindholm'

player_data = all_years_df[all_years_df['Player'] == player_name]

print(player_data[['Player', 'Year', 'GP', 'TOI', 'team_TOI', 'QoCF', 'QoCD', 'QoTF', 'QoTD', 'toughest_min', 'Goals']])

