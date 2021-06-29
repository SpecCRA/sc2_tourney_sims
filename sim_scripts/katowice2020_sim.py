# Packages
import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
from simulation_function_classes.create_model_input import match_info
from simulation_function_classes.sim_helper_functions import sim_functions
from catboost import CatBoostClassifier
import time
import os

# Set up Postgres engine
db_string = 'postgresql://postgres:impreza@localhost/projectdb'
db = create_engine(db_string)

con = psycopg2.connect(database="finaldb", user="postgres", password="impreza", host="127.0.0.1", port="5432")
curr = con.cursor()

# Import prediction model
model_path = 'models/match_predictor.cb'
model = CatBoostClassifier()
model.load_model(model_path)

def sim_tournament():
    # Initialize data structures
    group_finishes = list()
    top_seeds = list()
    second_seeds = list()
    third_seeds = list()

    # Generate groups
    groups_lists = sim_functions.create_groups(player_list, 6)

    # Simulate each round robin group
    for group in groups_lists:
        group_standings, group_match_results = sim_functions.round_robin(
            group, model, period_start, db
        )

        ranked_group, eliminated_players = sim_functions.parse_round_robin(
            group_standings, group_match_results
        )

        # store results
        top_seeds.append(ranked_group[0])
        second_seeds.append(ranked_group[1])
        third_seeds.append(ranked_group[2])
        group_finishes.append(eliminated_players)
    
    # Store eliminated player results into DataFrame
    for eliminated in group_finishes:
        for player in eliminated:
            sim_results.loc[player, 'group_stage'] += 1
    
    # Run playoffs
    playoff_results = sim_functions.playoffs_sixteen(
        top_seeds, second_seeds, third_seeds, groups_lists, model, period_start, db
    )

    for finish, players in playoff_results.items():
        if type(players) == list:
            for player in players:
                sim_results.loc[player, finish] += 1
        else:
            sim_results.loc[players, finish] += 1

# Simulation information

# Player list from IEM Katowice 2020
player_list = [
    'dark',
    'parting',
    'stats',
    'zest',
    'dear',
    'has',
    'hurricane',
    'patience',
    'showtime',
    'sos',
    'trap',
    'cure',
    'maru',
    'ty',
    'innovation',
    'special',
    'elazer',
    'reynor',
    'rogue',
    'serral',
    'solar',
    'armani',
    'lambo',
    'soo'
]

# Period
# Tournament ran from 2020-02-24 to 2020-03-01
# Start date was adjusted to get correct period
period_start = '2020/02/10'

# Ensure player count is correct
assert len(player_list) == 24

# Check if previous sim was run
existing_path = '/home/specc/Documents/school_files/thesis/sim_scripts/results/katowice_2020_sim_results.csv'
if os.path.exists(existing_path):
    sim_results = pd.read_csv(existing_path, index_col=0)
    # check how many sims have already run
    sim_start = int(sim_results['first'].sum())
    print(f"{sim_start} simulations already run.")
else:
    # Initialize DataFrame
    finish_cols = ['group_stage', 'ro16', 'ro8', 'fourth', 'third', 'second', 'first']
    sim_results = pd.DataFrame(0, index=player_list, columns=finish_cols)
    sim_start = 0

# Designate number of simulations to run
n_sims = 30000

# Results filename
filename = 'results/katowice_2020_sim_results.csv'

# Run simulations
print('Katowice 2020 simulations starting...')
for i in range(sim_start, n_sims):
    sim_tournament()

    if (i+1) % 500 == 0: # every 1000 sims, print progress and save results
        # Print progress
        print(f"Simulation run: {i+1}")
        progress = round(((i+1)/n_sims)*100, 3)
        print(f"IEM 2020 Simulations run: {i+1}")
        print(f"IEM 2020: {progress}%")
        print(f"Current time: {time.strftime('%H:%M:S', time.localtime())}")

        # Save temporary results
        sim_results.to_csv(filename)

print('Simulation finished.')

# Create a DataFrame to store finishes as percentages
sim_results_perc = sim_results / n_sims

# Export final results
sim_results.to_csv(filename)
sim_results_perc.to_csv('results/katowice_2020_sim_results_perc.csv')
print('Results saved.')