from hockey_rink import NHLRink
import requests
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytz
from matplotlib.lines import Line2D
import re
import concurrent.futures
from statistics import mode


import matplotlib.pyplot as plt
import seaborn as sns
import tkinter as tk
from tkinter import simpledialog

pd.options.mode.chained_assignment = None
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

# Prevent scientific notation in pandas
pd.options.display.float_format = "{:.0f}".format


def get_game_summary():  ## game summary info - the teams, location, logos, and scores
    try:
        # Initialize the DataFrame
        daily_games = pd.DataFrame()
        base_url = "https://api-web.nhle.com/v1/schedule/"

        start_date = datetime.strptime("2024-10-04", "%Y-%m-%d")
        end_date = datetime.strptime("2025-04-17", "%Y-%m-%d")
        current_date = start_date
        pd.set_option("display.max_columns", None)  # Show all columns
        pd.set_option("display.width", None)  # Avoid line wrapping
        # Set to keep track of unique dates
        seen_dates = set()

        while current_date <= end_date:
            formatted_date = current_date.strftime("%Y-%m-%d")
            api_url = f"{base_url}{formatted_date}"
            response = requests.get(api_url)
            if response.status_code == 200:
                response_text = response.text
            else:
                print(f"Request failed with status code {response.status_code}")
                continue

            json_data = json.loads(response_text)
            game_week = json_data["gameWeek"]
            game_week_df = pd.DataFrame(game_week)
            game_week_df = game_week_df[game_week_df["numberOfGames"] != 0]

            if formatted_date not in seen_dates:
                seen_dates.add(formatted_date)
                daily_games = pd.concat([daily_games, game_week_df], ignore_index=True)
            else:
                print(f"Failed to retrieve data for {formatted_date}")

            # Move to the next week
            current_date += timedelta(weeks=1)
            daily_games.loc[:, "date"] = pd.to_datetime(daily_games["date"])
            daily_games = daily_games.loc[daily_games["date"] <= end_date]
            daily_games.reset_index(drop=True, inplace=True)

            game_week_details = pd.json_normalize(daily_games["games"])

        dfs = {}
        for i in range(len(game_week_details.columns)):
            api_response = game_week
            if api_response is not None:
                game_info = pd.json_normalize(game_week_details[i])
                dfs[f"game_test{i}"] = pd.DataFrame(game_info)
            else:
                print(f"API request failed for index {i}")

        combined_df = pd.concat(dfs.values(), ignore_index=True)
        combined_df.dropna(how="all", inplace=True)
        combined_df["id"] = combined_df["id"].fillna(0).astype("Int64")

        combined_df = pd.DataFrame(
            {
                "id": combined_df.get("id", ""),
                "season": combined_df.get("season", pd.Series([""] * len(combined_df))),
                "startTimeUTC": pd.to_datetime(
                    combined_df.get("startTimeUTC", ""), errors="coerce"
                ),  # Convert startTimeUTC to datetime
                "gameType": combined_df.get("gameType", ""),
                "awayTeam.id": combined_df.get("awayTeam.id", ""),
                "awayTeam.abbrev": combined_df.get("awayTeam.abbrev", ""),
                "homeTeam.id": combined_df.get("homeTeam.id", ""),
                "homeTeam.abbrev": combined_df.get("homeTeam.abbrev", ""),
                "homeTeam.placeName.default": combined_df.get(
                    "homeTeam.placeName.default", ""
                ),
                "awayTeam.placeName.default": combined_df.get(
                    "awayTeam.placeName.default", ""
                ),
                "awayTeam.score": combined_df.get("awayTeam.score", 0),
                "homeTeam.score": combined_df.get("homeTeam.score", 0),
                "winningGoalScorer.playerId": combined_df.get(
                    "winningGoalScorer.playerId", ""
                ),
                "winningGoalie.playerId": combined_df.get("winningGoalie.playerId", ""),
                "gameState": combined_df.get("gameState", ""),
            }
        )
        combined_df = combined_df.convert_dtypes()

        combined_df.loc[:, "link"] = (
            "https://api-web.nhle.com/v1/gamecenter/"
            + combined_df["id"].astype(str)
            + "/play-by-play"
        )
        combined_df = combined_df.dropna(subset=["id"])
        combined_df = combined_df.query('gameState == "OFF"')

        # Convert to Eastern time
        eastern_timezone = pytz.timezone("America/New_York")
        combined_df.loc[:, "startTimeUTC"] = combined_df["startTimeUTC"].dt.tz_convert(
            eastern_timezone
        )  # Convert UTC to Eastern
        combined_df.loc[:, "startTimeUTC"] = combined_df["startTimeUTC"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )  # Format as string

        # Add game date and time columns with loc
        combined_df.loc[:, "game_date_time"] = pd.to_datetime(
            combined_df["startTimeUTC"]
        )
        combined_df.loc[:, "start_time"] = (
            combined_df["game_date_time"]
            .dt.strftime("%I:%M %p")
            .str.lstrip("0")
            .str.lower()
        )
        combined_df.loc[:, "game_date"] = combined_df["game_date_time"].dt.strftime(
            "%Y-%m-%d"
        )

        # Drop 'startTimeUTC' column safely
        combined_df = combined_df.drop("startTimeUTC", axis=1)
        combined_df = combined_df.rename(columns={"id": "game_id"})
        combined_df.sort_values(by="game_id", inplace=True)
        combined_df["game_id"] = combined_df["game_id"].astype("int64")
        print("api data pulled")
        output_path = r"C:/Users/kjcs2/GitHub/hockey/combined_df.csv"
        combined_df.to_csv(output_path, index=False)
        return combined_df

    except Exception as e:
        print(f"Error in get_game_summary: {e}")
        return pd.DataFrame()


def select_team(combined_df):
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main Tkinter window

        # Get the team code from the user
        team_code_str = simpledialog.askstring("Input", "Enter the team id:")
        if team_code_str is not None:
            try:
                team_code = int(team_code_str)  # Convert to int
            except ValueError:
                print("Please enter a valid integer for the team id.")
                return  # Exit or handle the error
        else:
            print("No input provided")
            return  # Exit or handle the case where no input is given

        if team_code:
            # Filter the DataFrame
            team_combined_df = combined_df[
                (combined_df["awayTeam.id"] == team_code)
                | (combined_df["homeTeam.id"] == team_code)
            ]
            team_combined_df["game_date"] = pd.to_datetime(
                team_combined_df["game_date"], format="%Y-%m-%d"
            )
            team_combined_df["game_id"] = team_combined_df["game_id"].astype("int64")
            print("team filtered")
            return team_combined_df
        else:
            print("No team code entered.")
            return team_combined_df

    except Exception as e:
        print(f"Error in selecting team: {e}")
        return None


# New Jersey Devils (1), 	2	New York Islanders,	3	New York Rangers,	4	Philadelphia Flyers,	5	Pittsburgh Penguins,	6	Boston Bruins,7	Buffalo Sabres,
# 8	Montréal Canadiens,
# 9	Ottawa Senators,	10	Toronto Maple Leafs,	12	Carolina Hurricanes,	13	Florida Panthers,	14	Tampa Bay Lightning,	15	Washington Capitals,	16	Chicago Blackhawks,
# 17	Detroit Red Wings,	# 18	Nashville Predators,	# 19	St. Louis Blues,	# 20	Calgary Flames,	# 21	Colorado Avalanche,	# 22	Edmonton Oilers,
# 23	Vancouver Canucks,	# 24	Anaheim Ducks,	# 25	Dallas Stars,	# 26	Los Angeles Kings,	# 28	San Jose Sharks,	# 29	Columbus Blue Jackets,
# 30	Minnesota Wild,	# 52	Winnipeg Jets,	# 54	Vegas Golden Knights,	# 55	Seattle Kraken,	# 59	Utah Hockey Club


def get_shots_data(combined_df):
    try:
        pxp_url = "https://api-web.nhle.com/v1/gamecenter/"
        pxp_suffix = "/play-by-play"
#https://api-web.nhle.com/v1/gamecenter/2024020879/play-by-play
        game_plays = pd.DataFrame()

        all_game_ids = combined_df["game_id"].to_list()

        # Function to process a single game
        def process_game(game_id):
            url = f"{pxp_url}{game_id}{pxp_suffix}"
            response = requests.get(url)

            if response.status_code == 200:
                json_data = response.json()

                if "plays" in json_data:
                    game_plays_detail = pd.json_normalize(json_data["plays"])
                    game_plays_detail["game_id"] = game_id
                    game_plays_detail = game_plays_detail[
                        ["game_id"]
                        + [col for col in game_plays_detail.columns if col != "game_id"]
                    ]
                    game_plays_detail = game_plays_detail[
                        game_plays_detail["typeCode"].isin([505, 506, 507, 508])
                    ]
                    return game_plays_detail
            else:
                print(
                    f"Request failed with status code {response.status_code} for game_id {game_id}"
                )

            return pd.DataFrame()

            # Use ThreadPoolExecutor to fetch data in parallel

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit requests for all game_ids
            future_to_game = {
                executor.submit(process_game, game_id): game_id
                for game_id in all_game_ids
            }
            for future in concurrent.futures.as_completed(future_to_game):
                result = future.result()
                if not result.empty:
                    game_plays = pd.concat([game_plays, result], ignore_index=True)

        game_plays.dropna(how="all", inplace=True)
        print("plays pulled")

        return game_plays

    except Exception as e:
        print(f"Error in get_shots_data: {e}")
        return pd.DataFrame()


def process_shots_data(game_plays):
    """
    Processes the raw game_plays DataFrame by renaming columns based on specific rules.
    """
    try:
        # Rename columns using your specified mapping
        all_shots_data = game_plays.rename(
            columns={
                "periodDescriptor.number": "period_number",
                "periodDescriptor.periodType": "period_type",
                "details.eventOwnerTeamId": "event_team_id",
                "details.xCoord": "xCoord",
                "details.yCoord": "yCoord",
                "details.scoringPlayerId": "scoring_player_id",
                "details.playerId": "player_id",
                "details.reason": "reason",
                "details.shotType": "shot_type",
                "details.shootingPlayerId": "shooting_player_id",
                "details.goalieInNetId": "goalie",
                "details.blockingPlayerId": "blocking_player",
            }
        )

        all_shots_data["goalie"] = all_shots_data["goalie"].fillna(0)

        all_shots_data["goalie"] = all_shots_data["goalie"].astype("int64")
        print("shots processed")

        return all_shots_data

    except Exception as e:
        print(f"Error in process_game_plays: {e}")
        return pd.DataFrame()


def roster_data():
    # Roster Data
    team_url = "https://api.nhle.com/stats/rest/en/team"

    response = requests.get(team_url)
    # content = json.loads(response.content)

    # Send an HTTP GET request to the specified URL
    response = requests.get(team_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # The response content can be accessed using response.text
        response_text = response.text
        # pprint(response_text)
    else:
        print(f"Request failed with status code {response.status_code}")

    json_data = json.loads(response_text)
    # json_data.keys()

    roster = json_data["data"]

    df_roster = pd.DataFrame(roster)
    df_roster = df_roster.convert_dtypes()
    df_roster["roster_url"] = (
        "https://api-web.nhle.com/v1/roster/" + df_roster["triCode"] + "/20242025"
    )
    df_roster = df_roster[["id", "fullName", "triCode", "roster_url"]]
    df_roster = df_roster.rename(
        columns={"id": "team_id", "fullName": "team_name", "triCode": "tri_code"}
    )
    df_roster = df_roster.sort_values(by="team_id")

    # for 2024-2025 season :
    valid_team_codes = (
        set(range(1, 11))
        .union(set(range(12, 27)))
        .union(set(range(28, 31)))
        .union(set(range(52, 53)))
        .union(set(range(54, 56)))
        .union(set(range(59, 60)))
    )
    filtered_rosters = df_roster[df_roster["team_id"].isin(valid_team_codes)]
    # filtered_rosters

    # Create an empty dictionary to store the results
    roster_dict = {}
    roster_link = filtered_rosters["roster_url"]

    # Define your extraction script as a function
    def extract_roster_data(roster_link):
        try:
            # Send an HTTP GET request to the game URL
            response = requests.get(roster_link)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                response_text = response.text
                json_data = json.loads(response_text)
                goalies = json_data["goalies"]
                goalies_df = pd.DataFrame(goalies)
                goalies_df = goalies_df[
                    [
                        "id",
                        "headshot",
                        "firstName",
                        "lastName",
                        "sweaterNumber",
                        "positionCode",
                        "shootsCatches",
                    ]
                ]
                goalies_df["firstName"] = goalies_df["firstName"].apply(
                    lambda x: x["default"] if isinstance(x, dict) else x
                )
                goalies_df["lastName"] = goalies_df["lastName"].apply(
                    lambda x: x["default"] if isinstance(x, dict) else x
                )
                goalies_df["player_name"] = (
                    goalies_df["firstName"] + " " + goalies_df["lastName"]
                )
                goalie_roster = goalies_df[
                    [
                        "id",
                        "headshot",
                        "player_name",
                        "sweaterNumber",
                        "positionCode",
                        "shootsCatches",
                    ]
                ]

                def extract_tricode(link):
                    # Use a regular expression to find the tricode
                    match = re.search(r"/([A-Z]{3})/", link)
                    if match:
                        return match.group(1)
                    else:
                        # Return None if no match is found
                        return None

                goalie_roster["tri_code"] = goalie_roster["headshot"].apply(
                    extract_tricode
                )
                return goalie_roster  # Return the entire processed DataFrame
            else:
                print(
                    f"Request failed for {roster_link} with status code {response.status_code}"
                )
                return None  # Return None to indicate failure

        except Exception as e:
            print(f"An error occurred: {e}")
            return None  # Return None to indicate failure

    # Loop through the rows of the filtered_rosters df
    for index, row in filtered_rosters.iterrows():
        # Extract the API link from the current row
        roster_link = row["roster_url"]

        # Run your game-specific data script and get the entire processed DataFrame
        team_roster = extract_roster_data(roster_link)

        # Check if team_roster is not None before proceeding
        if team_roster is not None:
            # Add a 'game_id' column to the game_specific_data DataFrame
            team_roster["tri_code"] = row["tri_code"]

            # Store the result in the dictionary with the game ID as the key
            roster_dict[row["tri_code"]] = team_roster
        else:
            print(f"Skipping row {index} due to failed request or exception.")

    all_rosters = pd.concat(roster_dict.values(), ignore_index=True)

    team_rosters = filtered_rosters[["team_id", "team_name", "tri_code"]]
    team_rosters = team_rosters.merge(all_rosters, on="tri_code", how="left")
    team_rosters = team_rosters.rename(columns={"id": "goalie"})
    print("goalies pulled")
    return team_rosters


def merge_data(all_shots_data, team_rosters):
    try:
        merged = all_shots_data.merge(team_rosters, on="goalie", how="left")
        merged = merged[
            [
                "game_id",
                "eventId",
                "timeInPeriod",
                "situationCode",
                "typeCode",
                "typeDescKey",
                "sortOrder",
                "period_number",
                "period_type",
                "event_team_id",
                "xCoord",
                "yCoord",
                "reason",
                "shot_type",
                "shooting_player_id",
                "scoring_player_id",
                "goalie",
                "blocking_player",
                "player_name",
                "team_id",
                "team_name",
            ]
        ]

        return merged
    except Exception as e:
        print(f"Error in process_game_plays: {e}")
        return pd.DataFrame()


def shots_made_data(merged):
    try:
        all_shots_made = merged.copy()

        def adjust_coordinates(row):
            x = row["xCoord"]
            y = row["yCoord"]
            if x < 0:
                adj_x = abs(x)
                adj_y = -y
            else:
                adj_x = x
                adj_y = y
            return pd.Series({"x_adjusted": adj_x, "y_adjusted": adj_y})

        # Apply the function to each row of the DataFrame
        all_shots_made[["x_adjusted", "y_adjusted"]] = all_shots_made.apply(
            adjust_coordinates, axis=1
        )
        all_shots_made["typeDescKey"] = pd.Categorical(
            all_shots_made["typeDescKey"],
            categories=[
                "blocked-shot",
                "goal",
                "missed-shot",
                "shot-on-goal",
            ],  # Define the order explicitly
            ordered=True,
        )
        print("shots data processed")
        return all_shots_made

    except Exception as e:
        print(f"Error in process_game_plays: {e}")
        return pd.DataFrame()


def team_specific_shots_against(combined_df, all_shots_made):
    try:
        all_codes = (
            combined_df["awayTeam.id"].tolist() + combined_df["homeTeam.id"].tolist()
        )
        team_code = mode(all_codes)
        print(team_code)
        # Ensure team_code is provided
        if not team_code:
            print("Team code not provided.")
            return None

        # List of game ids for the filtered team in combined_df
        team_game_ids = combined_df["game_id"].tolist()

        # Filter down the all_shots_made DataFrame to the games in the filtered combined_df
        team_filtered_games = all_shots_made[
            all_shots_made["game_id"].isin(team_game_ids)
        ]

        # Filter shots against the team based on the typeCode
        team_filtered_shots_against = team_filtered_games[
            (team_filtered_games["typeCode"] != 508)
            & (
                team_filtered_games["event_team_id"]
                != int(team_code)  # Ensure team_code is used correctly
            )
        ]

        # Include shots where typeCode is 508 and event_team_id matches team_code
        team_filtered_blocked_shots = team_filtered_games[
            (team_filtered_games["typeCode"] == 508)
            & (team_filtered_games["event_team_id"] == int(team_code))
        ]

        # Concatenate the results
        team_filtered_shots_against = pd.concat(
            [team_filtered_shots_against, team_filtered_blocked_shots],
            ignore_index=True,
        )
        print("shots against processed")

        # Combine both filtered datasets or handle them as needed
        return team_filtered_shots_against

    except Exception as e:
        print(f"Error in filtering shots against the team: {e}")
        return None


def pre_christmas(team_combined_df, team_filtered_shots_against):
    try:
        start_date = datetime.strptime("2024-10-04", "%Y-%m-%d")
        christmas_day = pd.to_datetime("2024-12-25", format="%Y-%m-%d")

        # Filter the DataFrame
        pre_christmas_dates = team_combined_df[
            (team_combined_df["game_date"] >= start_date)
            & (team_combined_df["game_date"] <= christmas_day)
        ]

        pre_christmas_game_ids = pre_christmas_dates["game_id"].tolist()

        # Filter down the all_shots_made DataFrame to the games in the filtered combined_df
        pre_christmas_shots_against = team_filtered_shots_against[
            team_filtered_shots_against["game_id"].isin(pre_christmas_game_ids)
        ]

        return pre_christmas_shots_against
    except Exception as e:
        print(f"Error in filtering shots against the team: {e}")
        return None


def post_christmas(team_combined_df, team_filtered_shots_against):
    try:
        # end_date = datetime.today().strftime("%Y-%m-%d")
        end_date = datetime.strptime("2025-01-25", "%Y-%m-%d")
        christmas_day = datetime.strptime("2024-12-25", "%Y-%m-%d")
        # Filter the DataFrame
        post_christmas_dates = team_combined_df[
            (team_combined_df["game_date"] >= christmas_day)
            & (team_combined_df["game_date"] <= end_date)
        ]

        post_christmas_game_ids = post_christmas_dates["game_id"].tolist()
        print(post_christmas_game_ids)
        # Filter down the all_shots_made DataFrame to the games in the filtered combined_df
        post_christmas_shots_against = team_filtered_shots_against[
            team_filtered_shots_against["game_id"].isin(post_christmas_game_ids)
        ]

        return post_christmas_shots_against
    except Exception as e:
        print(f"Error in filtering shots against the team: {e}")
        return None


def grouped_plots(team_filtered_shots_against):
    # --- First Visualization: Shot Attempts Against by Game ID with Rolling Average ---
    # Group the data by game_id and typeDescKey, then count occurrences
    grouped = (
        team_filtered_shots_against.groupby(["game_id", "typeDescKey"], observed=False)
        .size()
        .unstack(fill_value=0)
    )

    # Calculate the total shot attempts
    grouped["total_shots"] = grouped.sum(axis=1)

    # Compute the rolling average
    grouped["rolling_avg"] = (
        grouped["total_shots"].rolling(window=3, min_periods=1).mean()
    )

    # Debugging: Print the DataFrame to verify
    print("Grouped DataFrame with Rolling Average:")
    print(grouped.head())

    # Reset index to use "game_id" as a column for plotting
    grouped = grouped.reset_index()

    # Debugging: Ensure "game_id" is in the DataFrame
    print("Grouped DataFrame after reset_index:")
    print(grouped.head())

    return grouped


def season_attempts_against_viz(grouped):
    # Plot the stacked bar chart (game_id is already in the index after reset)
    ax = grouped.drop(columns=["total_shots", "rolling_avg"]).plot(
        kind="bar", x="game_id", stacked=True, figsize=(14, 8), colormap="viridis"
    )
    # Get the x-ticks from the bar plot
    x_ticks = ax.get_xticks()

    # Plot the rolling average line using the x-ticks
    ax.plot(
        x_ticks,  # Use the x-ticks for the X-axis of the rolling average
        grouped["rolling_avg"],  # Y-axis: rolling average of total shots
        color="red",
        marker="o",
        linestyle="-",
        linewidth=2,
        label="Rolling Average",
        zorder=5,  # Ensure the line is above the bars
    )
    # Customize the chart
    ax.set_title("Shot Attempts Against by Game ID with Rolling Average", fontsize=16)
    ax.set_xlabel("Game ID", fontsize=12)
    ax.set_ylabel("Total Shot Attempts", fontsize=12)
    ax.tick_params(axis="x", rotation=90, labelsize=10)
    ax.legend(title="Legend", fontsize=10, title_fontsize=12)
    plt.tight_layout()

    # Display the plot
    plt.show()


# something is backwards here
def shots_against_comparison(pre_christmas_shots_against, post_christmas_shots_against):
    try:
        # Group and calculate stats for recent (post-Christmas) data
        half_2_group = post_christmas_shots_against[["typeDescKey", "game_id"]].groupby(
            "typeDescKey"
        )
        half_2_group_counts = (
            half_2_group["game_id"]
            .agg(
                total_count="size",
                unique_count="nunique",
            )
            .reset_index()
        )
        half_2_group_counts["mean"] = (
            half_2_group_counts["total_count"] / half_2_group_counts["unique_count"]
        )

        # Group and calculate stats for previous (pre-Christmas) data
        half_1_group = pre_christmas_shots_against[["typeDescKey", "game_id"]].groupby(
            "typeDescKey"
        )
        half_1_group_counts = (
            half_1_group["game_id"]
            .agg(
                total_count="size",
                unique_count="nunique",
            )
            .reset_index()
        )
        half_1_group_counts["mean"] = (
            half_1_group_counts["total_count"] / half_1_group_counts["unique_count"]
        )

        # Round the 'mean' values for both the Recent and Previous groups
        half_2_group_counts["rounded_mean"] = round(half_2_group_counts["mean"], 2)
        half_1_group_counts["rounded_mean"] = round(half_1_group_counts["mean"], 2)

        # Add a 'group' column to each DataFrame to indicate "recent" or "previous"
        half_1_group_counts["group"] = "Before Christmas"
        half_2_group_counts["group"] = "After Christmas"

        # Combine the two DataFrames vertically
        combined_data = pd.concat(
            [
                half_2_group_counts[["group", "typeDescKey", "rounded_mean"]].rename(
                    columns={"rounded_mean": "mean"}
                ),
                half_1_group_counts[["group", "typeDescKey", "rounded_mean"]].rename(
                    columns={"rounded_mean": "mean"}
                ),
            ],
            ignore_index=True,
        )

        # Pivot the DataFrame to make "typeDescKey" columns and "group" the index
        pivoted_data = combined_data.pivot(
            index="group", columns="typeDescKey", values="mean"
        ).reset_index()

        # Rename index column
        pivoted_data = pivoted_data.rename_axis(None, axis=1)
        pivoted_data = pivoted_data.sort_values(by="group", ascending=False)

        return pivoted_data
    except Exception as e:
        print(f"Error in filtering shots against the team: {e}")
        return None


def plot_comparisons(pivoted_data):
    # Plot the data
    plt.figure(figsize=(8, 6))

    # Plot a line for each column (typeDescKey)
    for column in pivoted_data.columns[1:]:  # Skip the 'group' column
        plt.plot(
            pivoted_data["group"],  # x-axis: 'group'
            pivoted_data[column],  # y-axis: values for each typeDescKey
            marker="o",
            label=column,  # Use typeDescKey as the label
        )

        # Annotate each point with its value
        for i, txt in enumerate(pivoted_data[column]):
            plt.text(
                x=i,
                y=txt,
                s=f"{txt:.2f}",  # Format to 2 decimal places
                fontsize=10,
                ha="center",
                va="bottom",  # Position the text slightly above the point
            )

    # Adjust x-axis to bring 'recent' and 'previous' closer
    plt.xticks(range(len(pivoted_data["group"])), pivoted_data["group"], fontsize=10)
    plt.xlim(-0.5, 1.7)  # Compress the range even more for tighter spacing

    # Add labels, title, and legend
    plt.xlabel("Time Period")
    plt.ylabel("Average Count")
    plt.title("Average Shots and Shot Attempts Against")
    plt.legend(title="Shot/Shot Attempt Type", loc="best")
    plt.grid(True)

    # Show the plot
    plt.show()


game_summary = get_game_summary()

team = select_team(game_summary)

all_shots = get_shots_data(team)
process_shots = process_shots_data(all_shots)
rosters = roster_data()
merged_d = merge_data(process_shots, rosters)
shots_made = shots_made_data(merged_d)
team_shots = team_specific_shots_against(team, shots_made)
grouped_data = grouped_plots(team_shots)
all_season_viz = season_attempts_against_viz(grouped_data)
half_1 = pre_christmas(team, team_shots)
half_2 = post_christmas(team, team_shots)
half_comparisons = shots_against_comparison(half_1, half_2)
comparison_viz = plot_comparisons(half_comparisons)
if comparison_viz is not None:
    print(comparison_viz.head())

else:
    print("No data returned.")
