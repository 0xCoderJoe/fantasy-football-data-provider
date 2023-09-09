from yahoo_oauth import OAuth2
from time import sleep
import yahoo_fantasy_api as yfa
import pandas as pd
import dotenv
import json

MY_TEAM="Moneyline"
UPDATE_PLAYERS=False
UPDATE_STATS=True


def handle_auth():
    '''Handle the authentication and token refresh'''
    session = OAuth2(None, None, from_file='oauth2.json')
    print(session)

    # creds = {'consumer_key': os.environ.get('CONSUMER_KEY'),
    #          'consumer_secret': os.environ.get('CONSUMER_SECRET')}
    # with open("oauth2.json", "w") as f:
    #     f.write(json.dumps(creds))

    return session

def acquire_league_obj(session):
    '''get the league ID and return league object'''
    
    game = yfa.Game(sc=session, code='nfl')
    league_id = game.league_ids(year='2023')
    league_obj = game.to_league(league_id=league_id[0])

    return league_obj

def acquire_team_obj(league, team_name):
    '''Return an object to access Team functions'''
    team_obj = league.get_team(team_name)
    return team_obj[team_name]

def get_all_league_players(league):
    '''Updates a database of all the leagues players and stats'''
    
    if UPDATE_PLAYERS == True:
        all_available_players = league._fetch_players(status="A")
        teams = league.teams()

        all_team_names = [teams[x]['name'] for x in teams]

        players_on_teams = []
        for team_name in all_team_names:
            team_obj = acquire_team_obj(league=league, team_name=team_name)
            team_roster = team_obj.roster()
            for player in team_roster:
                players_on_teams.append(player)

        all_players = players_on_teams + all_available_players

        json_object = json.dumps(all_players, indent=4)
        
        # Writing to sample.json
        with open("players.json", "w") as outfile:
            outfile.write(json_object)
    else:

        with open("players.json", "r") as player_data:
            all_players = json.load(player_data)

    return all_players

def get_all_player_stats(league, players):

    if UPDATE_STATS == True:

        all_player_stats = []
        for player in players:
            
            player_stats = league.player_stats(player['player_id'], 'season')
            all_player_stats.append(player_stats[0])
            sleep(1)


        json_object = json.dumps(all_player_stats, indent=4)
        
        # Writing to sample.json
        with open("player_stats.json", "w") as outfile:
            outfile.write(json_object)

    else:

        with open("player_stats.json", "r") as player_stat_data:
            all_player_stats = json.load(player_stat_data)

    return all_player_stats

def main():
    
    dotenv.load_dotenv()
    session = handle_auth()
    league = acquire_league_obj(session)
    
    all_players = get_all_league_players(league=league)

    collected_stats = get_all_player_stats(league=league, players=all_players)
    
    df = pd.DataFrame(collected_stats)
    df.to_excel('ff_data.xlsx', index=False)
    print(df)




if __name__=="__main__":
    main()