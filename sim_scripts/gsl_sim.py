# Packages
import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
from simulation_function_classes.create_model_input import match_info
from simulation_function_classes.sim_helper_functions import sim_functions
from catboost import CatBoostClassifier

# Set up Postgres engine
db_string = 'postgresql://postgres:impreza@localhost/projectdb'
db = create_engine(db_string)

con = psycopg2.connect(database="finaldb", user="postgres", password="impreza", host="127.0.0.1", port="5432")
curr = con.cursor()

# Import prediction model
model_path = 'models/match_predictor.cb'
model = CatBoostClassifier()
model.load_model(model_path)

# Put together simulation functions to be able to repeat
def sim_gsl():
    # Initialize storage data structures
    group_finishes = list()
    top_seeds = list()
    second_seeds = list()

    # Generate groups
    groups_list = sim_functions.create_groups(player_list, 4)

    # Simulate each group
    for group in groups_list:
        group_winner, second_winner, eliminated_players = sim_functions.gsl_group(
            group, model, period_start, db
        )

        # Gather winners and losers
        top_seeds.append(group_winner)
        second_seeds.append(second_winner)
        #print(f"eliminated players: {eliminated_players}")
        group_finishes.append(eliminated_players)

    # Append results for losers
    for eliminated in group_finishes:
        for player in eliminated:
            #print(player)
            sim_results.loc[player]['group_stage'] += 1

    # Generate playoff matchups
    playoff_matchups = sim_functions.gen_gsl_playoffs(top_seeds, second_seeds, groups_list)
    #print(playoff_matchups)
    # simulate playoffs
    playoff_results = sim_functions.playoffs_eight(playoff_matchups, model,\
                                                    period_start, db)

    #print(playoff_results.items())

    # Append rest of results
    # Check here for errors
    for finish, players in playoff_results.items():
        if type(players) == list:
            #print(f"{finish} : {players}")
            for player in players:
                #print(f"eliminated player: {player}")
                sim_results.loc[player][finish] += 1
        else:
            #print(f"{finish} : {players}")
            sim_results.loc[players][finish] += 1

# Simulation Information

# Player list from 2021 GSL Season 1
player_list = [
    'trap',
    'zest',
    'dream',
    'zoun',
    'innovation',
    'armani',
    'rogue',
    'solar',
    'hurricane',
    'sos',
    'bunny',
    'cure',
    'ty',
    'maru',
    'dark',
    'dongraegu'
]

# Period
# Touranment ran 2021-04-05 to 2021-05-06
period_start = '2021/04/05'

# Check player list is correct
assert len(player_list) == 16

# Create groups
# Groups should have 4 players each
groups_list = sim_functions.create_groups(player_list, 4)

# Check if previous files exist
# Load file
# Count how many sims were run
# Subtract 30000 to see how many more need to be run

# Store simulation information
finish_cols = ['group_stage', 'ro8', 'ro4', 'second', 'first']
sim_results = pd.DataFrame(0, index=player_list, columns=finish_cols)

# Designate number of simulations to run
n_sims = 30000

# Export results
filename = 'results/gsl_2021_sim_results.csv'

# Run sims!!!!!
print('Simulations starting...')
for i in range(n_sims):
    sim_gsl()

    if (i+1) % 500 == 0: # at every 1000 simulation, print progress and save results
        # Print progress
        print(f"Simulation run: {i+1}")
        progress = round(((i+1)/n_sims)*100, 3)
        print(f"GSL Simulations run: {i+1}")
        print(f"GSL: {progress}%")

        # Save temp results
        sim_results.to_csv(filename)

print('Simulations finished.')

# Create a DataFrame to store finishes as percentages
sim_results_perc = sim_results / n_sims

# Export finished results
sim_results.to_csv(filename)
sim_results_perc.to_csv('results/gsl_2021_sim_results_perc.csv')
print('Results saved.')