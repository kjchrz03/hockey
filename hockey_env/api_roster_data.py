import pandas as pd
import json
import re
import requests


pd.options.mode.chained_assignment = None


def get_roster_data():
    # Roster Data
    team_url = "https://api.nhle.com/stats/rest/en/team"

    response = requests.get(team_url)
    # content = json.loads(response.content)

    # Send an HTTP GET request to the specified URL
    response = requests.get(team_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        response_text = response.text

    else:
        print(f"Request for player data failed with status code {response.status_code}")

    json_data = json.loads(response_text)

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

    # Create an empty dictionary to store the results
    roster_dict = {}

    # Define your function to extract player data and avoid repetition
    def process_player_data(player_data, position):
        df = pd.DataFrame(player_data)
        if not df.empty:
            df = df[
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
            df["firstName"] = df["firstName"].apply(
                lambda x: x["default"] if isinstance(x, dict) else x
            )
            df["lastName"] = df["lastName"].apply(
                lambda x: x["default"] if isinstance(x, dict) else x
            )
            df["player_name"] = df["firstName"] + " " + df["lastName"]
            df["position"] = position
            df["sweaterNumber"] = df["sweaterNumber"].astype(str)
            return df[
                [
                    "id",
                    "headshot",
                    "player_name",
                    "sweaterNumber",
                    "positionCode",
                    "shootsCatches",
                ]
            ]
        return pd.DataFrame()

    # Function to extract tricode from headshot link
    def extract_tricode(link):
        match = re.search(r"/([A-Z]{3})/", link)
        return match.group(1) if match else None

    # Function to fetch and process roster data
    def extract_roster_data(roster_link):
        try:
            response = requests.get(roster_link)
            if response.status_code == 200:
                json_data = json.loads(response.text)
                forwards_df = process_player_data(json_data["forwards"], "FWD")
                defense_df = process_player_data(json_data["defensemen"], "DEF")
                goalies_df = process_player_data(json_data["goalies"], "GOL")

                # Concatenate all positions into a single DataFrame
                team_roster_df = pd.concat(
                    [forwards_df, defense_df, goalies_df], axis=0, ignore_index=True
                )
                team_roster_df["tri_code"] = team_roster_df["headshot"].apply(
                    extract_tricode
                )
                return team_roster_df
            else:
                # print(f"Request failed for roster {roster_link} with status code {response.status_code}")
                return None
        except Exception as e:
            # print(f"An error occurred in roster data: {e}")
            return None

    # Loop through the rows of filtered_rosters and extract data
    for index, row in filtered_rosters.iterrows():
        roster_link = row["roster_url"]
        team_roster = extract_roster_data(roster_link)

        if team_roster is not None:
            team_roster["tri_code"] = row["tri_code"]
            roster_dict[row["tri_code"]] = team_roster
        else:
            print(
                f"Skipping row {index} due to failed request or exception in roster data."
            )

    # Combine all rosters into a single DataFrame
    all_rosters = pd.concat(roster_dict.values(), ignore_index=True)

    # Merge team information with the player roster data
    team_rosters = filtered_rosters[["team_id", "team_name", "tri_code"]]
    team_rosters = team_rosters.merge(all_rosters, on="tri_code", how="left")
    team_rosters = team_rosters.rename(columns={"id": "player_id"})
    team_rosters = team_rosters[
        [
            "player_id",
            "player_name",
            "team_name",
            "positionCode",
            "sweaterNumber",
            "shootsCatches",
        ]
    ]
    # View result
    return team_rosters


def load_roster_data(team_rosters):
    try:
        team_rosters = get_roster_data()
        return team_rosters
    except Exception as e:
        print(f"Error loading roster data: {e}")
        return None


roster = get_roster_data()
if roster is not None:
    print(roster.head())

else:
    print("No data returned.")
