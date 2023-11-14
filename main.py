from yahoo_oauth import OAuth2
from time import sleep
from nosql_common.nosql_cloudant import NoSQLCommCloudant
import yahoo_fantasy_api as yfa
import pandas as pd
import dotenv
import json
import os
import logging
logging.basicConfig(level=logging.INFO)


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
    
    game = yfa.Game(sc=session, code=os.environ.get('FANTASY_SPORT'))
    league_id = game.league_ids(year=os.environ.get('FANTASY_YEAR'))
    league_obj = game.to_league(league_id=league_id[0])

    return league_obj

def acquire_team_obj(league, team_name):
    '''Return an object to access Team functions'''
    team_obj = league.get_team(team_name)
    return team_obj[team_name]

def get_all_league_players(league):
    '''Updates a database of all the leagues players and stats'''
    
    use_cache = os.environ.get('USE_CACHE')
    if use_cache == "False":
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

    use_cache = os.environ.get('USE_CACHE')
    if use_cache == "False":

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

def combine_data(d1, d2):
    '''Combine data into docs'''

    combined_data = []
    for player_d1 in d1:
        for player_d2 in d2:
            if player_d1['player_id'] == player_d2['player_id']:
                player_d2.update(player_d1)
                combined_data.append(player_d2)

    # Writing to sample.json
    json_object = json.dumps(combined_data, indent=4)
    with open("player_data.json", "w") as outfile:
        outfile.write(json_object)

    return combined_data

def main():
    
    dotenv.load_dotenv()
    db = NoSQLCommCloudant()
    database = os.environ.get('CLOUDANT_DB')
    ddoc = os.environ.get('CLOUDANT_DDOC')
    view = os.environ.get('CLOUDANT_VIEW')

    session = handle_auth()
    league = acquire_league_obj(session)

    logging.info("Collecting player data from Yahoo Fantasy")    
    all_players = get_all_league_players(league=league)
    collected_stats = get_all_player_stats(league=league, players=all_players)
    
    logging.info("Aggregating player data and stats..")
    combined_data = combine_data(all_players, collected_stats)
    
    if os.environ.get('WRITE_CACHE') == "True":
        df = pd.DataFrame(combined_data)
        df.to_excel('combined_data.xlsx', index=False)

    logging.info('Updating our player database..')
    player_id_index = db.get_view(database=database, ddoc=ddoc, limit=1000, view=view)._to_dict()
    
    operations_watch=0
    for player in combined_data:
        
        logging.info(f"Processing: {player['name']}..")
        
        check_exists = [x for x in player_id_index['result']['rows'] if player['player_id'] == x['value']]
        if len(check_exists) == 1:
            curr_doc = db.get_document(database=database, doc_id=check_exists[0]['id'])._to_dict()
            
            player['_rev'] = curr_doc['result']['_rev']
            player['_id'] = curr_doc['result']['_id']
            
            try:
                db.update_document(database=database, doc=player)
            
            except Exception as e:
                logging.error(f"ERROR - {e}")


        elif len(check_exists) > 1:
            logging.info("Documents returned greater than 1, might indicate an issue..skipping")
            logging.warning(f"Check on records for {player['name']} in the database")
        
        else:

            try:
                db.update_document(database=database, doc=player)
            
            except Exception as e:
                logging.error(f"ERROR - {e}")
        
        # Necessary timing functions for the free API
        if operations_watch >= 10:
            sleep(1)
            operations_watch = 0
        else:
            operations_watch += 1
            sleep(.03)

    logging.info("The player provider has finished")

if __name__=="__main__":
    main()