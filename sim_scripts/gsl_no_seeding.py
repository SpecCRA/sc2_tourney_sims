# Packages
import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
from simulation_function_classes.create_model_input import match_info
from simulation_function_classes.sim_helper_functions import sim_functions
from catboost import CatBoostClassifier
import os
import datetime

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
    # ro28
    ro28_finishes = list()
    ro16_players = list()
    # ro16
    ro16_finishes = list()
    top_seeds = list()
    second_seeds = list()

    # RO 24
    # Generate groups
    ro28_groups = sim_functions.create_groups(player_list, 4)

    # Simulate each group
    for group in ro28_groups:
        group_winner, second_winner, eliminated_players = sim_functions.gsl_group(
            group, model, period_start, db
        )

        # Gather winners and losers
        ro16_players.append(group_winner)
        ro16_players.append(second_winner)
        #print(f"eliminated players: {eliminated_players}")
        ro28_finishes.append(eliminated_players)

    # Append results for ro24 losers
    for eliminated in ro28_finishes:
        for player in eliminated:
            #print(player)
            sim_results.loc[player]['ro28_groups'] += 1

    # RO 16
    # Generate groups
    ro16_groups = sim_functions.create_groups(ro16_players, 4)

    # Simulate each group
    for group in ro16_groups:
        winner, second, eliminated_players = sim_functions.gsl_group(
            group, model, period_start, db
        )

        top_seeds.append(winner)
        second_seeds.append(second)
        ro16_finishes.append(eliminated_players)
    # Record results for ro16 losers
    for eliminated in ro16_finishes:
        for player in eliminated:
            sim_results.loc[player]['ro16_groups'] += 1

    # Playoffs

    # Generate playoff matchups
    playoff_matchups = sim_functions.gen_gsl_playoffs(top_seeds, second_seeds, ro16_groups)
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

# http://aligulac.com/periods/294/
# Use period 294
# start date: 2021 May 20

# All players
player_list = [
    'serral',
    'clem',
    'reynor',
    'maru',
    'dark',
    'solar',
    'cure',
    'heromarine',
    'trap',
    'innovation',
    'stats',
    'rogue',
    'zest',
    'byun',
    'showtime',
    'parting',
    'ty',
    'bunny',
    'zoun',
    'dream',
    'elazer',
    'sos',
    'maxpax',
    'lambo',
    'neeb',
    'ragnarok',
    'armani',
    'astrea',
]

# Period
period_start = '2021/05/20'

# Check player list is correct
assert len(player_list) == 28

# Check if previous files exist
# Load file
# Count how many sims were run
# Subtract 30000 to see how many more need to be run

filename = 'results/gsl_no_seeding_sim_results.csv'
# Check if previous sim was run
existing_path = f'/home/specc/Documents/school_files/thesis/sim_scripts/results/{filename}'
if os.path.exists(existing_path):
    sim_results = pd.read_csv(existing_path, index_col=0)
    # check how many sims have already run
    sim_start = int(sim_results['first'].sum())
    print(f"{sim_start} simulations already run.")
else:
    # Initialize DataFrame
    finish_cols = ['ro28_groups', 'ro16_groups', 'ro8', 'ro4', 'second', 'first']
    sim_results = pd.DataFrame(0, index=player_list, columns=finish_cols)
    sim_start = 0

# Designate number of simulations to run
n_sims = 10

# Run sims!!!!!
print('Simulations starting...')
time_start = datetime.datetime.now()
for i in range(sim_start, n_sims):
    sim_gsl()

    if (i+1) % 500 == 0: # at every 1000 simulation, print progress and save results
        # Print progress
        print(f"Simulation run: {i+1}")
        progress = round(((i+1)/n_sims)*100, 3)
        elapsed_time = datetime.datetime.now() - time_start
        print(f"GSL No Seeding Simulations run: {i+1}")
        print(f"GSL No Seeding: {progress}%")
        print(f"Time elapsed: {elapsed_time}")

        # Save temp results
        sim_results.to_csv(filename)

print('Simulations finished.')

# Create a DataFrame to store finishes as percentages
sim_results_perc = sim_results / n_sims

# Export finished results
sim_results.to_csv(filename)
sim_results_perc.to_csv('results/gsl_no_seeding_sim_results_perc.csv')
print('Results saved.')