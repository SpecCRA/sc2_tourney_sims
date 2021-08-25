#!/usr/bin/env python

# Import functions
import numpy as np
import pandas as pd
from itertools import combinations
from simulation_function_classes.create_model_input import match_info
import math
from collections import defaultdict
import random

class sim_functions():
    def create_match_proba(model_input, predictor_model):
        model_input = model_input.iloc[:,4:].to_numpy()
        prediction_proba = predictor_model.predict_proba(model_input)

        return prediction_proba
    
    def sim_match(player_a, player_b, n_matches, model, period_start, db):
        """
        Psuedocode:
            1. Gather player info and create model input
            2. Predict probabilities
            3. Set boundaries on a random number generator
            4. Predict outcome of one match, one map
            5. Store results until best of n (1, 3, 5, 7) is met
        """
        min_wins = math.ceil(n_matches/2)
        #print(min_wins)
        match_df = match_info.create_input(player_a, player_b, period_start, db)
        proba = sim_functions.create_match_proba(match_df, model)

        player_a_wins = 0
        player_b_wins = 0

        while (player_a_wins < min_wins) & (player_b_wins < min_wins):
            outcome = np.random.randint(0, 1000)
            if outcome >= proba[0][0]* 1000:
                player_a_wins += 1
            else:
                player_b_wins += 1

        score = [player_a_wins, player_b_wins]

        # perhaps label winner and loser instead of hope
        results = dict()

        if player_a_wins > player_b_wins:
            results['winner'] = player_a
            results['loser'] = player_b
            results['winner_score'] = player_a_wins
            results['loser_score'] = player_b_wins
        else:
            results['winner'] = player_b
            results['loser'] = player_a
            results['winner_score'] = player_b_wins
            results['loser_score'] = player_a_wins
        
        return results
    
    def create_groups(player_list, n_in_group):
        """
        Pseudocode:
            1. input a player list
            2. Put them into a list of lists
            3. Depends on second argument n
                * n should be 4 or 6 depending on GSL or Katowice, respectively.
        ##############
        Needs further documentation
        ##############
        """

        n_groups = len(player_list) / n_in_group
        if len(player_list) % n_in_group != 0:
            return ('Number of players or n_in_group is wrong.')
        player_idx = np.arange(len(player_list))
        # shuffle the array
        np.random.shuffle(player_idx)
        player_list = [player_list[i] for i in player_idx]

        groups = [player_list[i:i+n_in_group] for i in range(0, len(player_list), n_in_group)]

        return groups

    def gsl_group(group, model, period_start, db):
        """
        Inputs:
            group: A list of 4 players
            model: prediction model used
            period_start: in a 'YYYY/MM/DD' string format
            db: database object
        
        Summary:
            Takes in one GSL group and outputs the simulated match results.

        Format:
            4 players total
            2 players returned
            BO3 format
            Initial matches: 2 matches - figure out seeding
            Winner match: winners of initial matches play
                * winner of winner stage wins the group
            Losers match: loser is eliminated, winner moves into next match
            Elimination match: loser from winner match and winner from losers match
                * winner of this match exits stage as second seeded player

        Outputs:
            first_player - winner of the group
            second_player - second player out of the group
            eliminated_players - list of players eliminated from this format
        """
        assert len(group) == 4
        first_player = ''
        second_player = ''
        eliminated_players = list()

        winners = list()
        losers = list()
        elimination = list()

        # match 1
        match_1_res = sim_functions.sim_match(
            group[0], group[3], 3, model, period_start, db
        )

        winners.append(match_1_res['winner'])
        losers.append(match_1_res['loser'])

        # match 2
        match_2_res = sim_functions.sim_match(
            group[1], group[2], 3, model, period_start, db
        )

        winners.append(match_2_res['winner'])
        losers.append(match_2_res['loser'])

        # winners match
        winners_res = sim_functions.sim_match(
            winners[0], winners[1], 3, model, period_start, db
        )
        first_player = winners_res['winner']
        elimination.append(winners_res['loser'])

        # losers match
        losers_res = sim_functions.sim_match(
            losers[0], losers[1], 3, model, period_start, db
        )
        elimination.append(losers_res['winner'])
        eliminated_players.append(losers_res['loser'])

        # elimination match
        elimination_res = sim_functions.sim_match(
            elimination[0], elimination[1], 3, model, period_start, db
        )
        second_player = elimination_res['winner']
        eliminated_players.append(elimination_res['loser'])

        return first_player, second_player, eliminated_players

    def round_robin(group, model, period_start, db):
        """
        Inputs:
            group: list of 6 players
            model: prediction model object
            period_start: date in 'YYYY/MM/DD' string format
            db: database object

        Summary:
            Take in a player list and compute simulated match results in a round
                robin format. Each player will play every other player in the group
                in a best of 3 format.

        Outputs:
            DataFrame: pandas DataFrame with group results, match scores and map scores
            DataFrame: pandas DataFrame with individual match results
        """
        assert len(group) == 6
        wins = pd.Series(index=group, name='wins', dtype=int)
        losses = pd.Series(index=group, name='losses', dtype=int)
        map_wins = pd.Series(index=group, name='map_wins', dtype=int)
        map_losses = pd.Series(index=group, name='map_losses', dtype=int)
        group_data = [wins, losses, map_wins, map_losses]

        matchups = list(combinations(group, 2))

        match_results = list()

        for match in matchups:
            res = sim_functions.sim_match(
                match[0], match[1], 3, model, period_start, db
            )

            wins[res['winner']] += 1
            losses[res['loser']] += 1

            # winner scores
            map_wins[res['winner']] += res['winner_score']
            map_losses[res['winner']] += res['loser_score']

            # loser scores
            map_wins[res['loser']] += res['loser_score']
            map_losses[res['loser']] += res['winner_score']

            match_results.append(res)

        # combine data
        results = pd.DataFrame(group_data).T.reset_index()\
                    .rename(columns={'index':'player'})

        match_results_df = pd.DataFrame(match_results)
        
        return results, match_results_df

    def parse_round_robin(results_df, match_results_df):
        """
        Inputs:
            results_df: pandas DataFrame with round robin match and map sco0res
            match_results_df: pandas DataFrame with individual match results

        Summary:
            Take in round robin results and parse the results by ranking players.

        Ranking:
            1. Match wins
            2. Map wins
            3. Individual match

        Outputs:
            list: ranked list of players that won the group
            list: list of eliminated players
        """
        # add ranking columns
        results_df['wins_rank'] = results_df['wins'].rank(ascending=False, method='dense')
        results_df['map_wins_rank'] = results_df['map_wins'].rank(ascending=False, method='dense')

        # store players in proper rank
        players_present = list(results_df['player'])
        ranked_players = list()

        # see what values are in each ranks
        group_ranks = sorted(list(results_df['wins_rank'].unique()))

        for place in group_ranks:
            subset_df = results_df[
                results_df['wins_rank'] == place
            ]
            # if there is no tie, append the player at that specific place
            if len(subset_df) == 1:
                player = subset_df['player'].iloc[0]
                ranked_players.append(player)
            else:
                # check map wins upon tiebreakers
                map_wins_ranks = sorted(list(subset_df['map_wins_rank'].unique()))

                # loop through each rank to perform same checks as before
                for rank in map_wins_ranks:
                    map_wins_subset_df = subset_df[subset_df['map_wins_rank'] == rank]

                    if len(map_wins_subset_df) == 1:
                        player = map_wins_subset_df.iloc[0]['player']
                        ranked_players.append(player)
                    else:
                        # look for head to head winner and loser for next set of tied players
                        tied_players = list(map_wins_subset_df['player'])

                        # find the exact matchup from group stage
                        match_subset_df = match_results_df[
                            (match_results_df['winner'] == tied_players[0]) |
                            (match_results_df['loser'] == tied_players[0])
                        ][
                            (match_results_df['winner'] == tied_players[1]) |
                            (match_results_df['loser'] == tied_players[1])
                        ]

                        winner = match_subset_df['winner'].iloc[0]
                        loser = match_subset_df['loser'].iloc[0]

                        # append players in order
                        ranked_players.append(winner)
                        ranked_players.append(loser)
        # return two lists
        # 1. continuing players, ranked 1-3 by order of list
        # 2. eliminated players where rank does not matter
        #assert len(ranked_players) == 6

        #if len(ranked_players) < 6:
        #    print(ranked_players)

        ranked_winners = ranked_players[:3]
        eliminated_players = ranked_players[3:]

        ############# BUG REPORT ###############
        # ranked players doesn't seem to have 6 players
        #assert len(eliminated_players) == 3

        return ranked_winners, eliminated_players
    
    def check_same_group(top_seeded_players, second_seeded_players, grouped_players):
        """
        Summary:
            Take in two lists and compare if a shuffled version of the second list
            creates a matchup that may be repeated from the previous group. The point
            of this function is to ensure a possible rematch does not happen in the
            first round of the playoffs.

        Inputs:
            top_seeded_players: first list of top seeded players
            second_seeded_players: second list of lower seeded players
            grouped_players: a list of lists of tournament groups

        Outputs:
            shuffled, non-repeating matchup of the second group of players
        """
        for group in grouped_players:
            for i in range(4):
                if (top_seeded_players[i] in group) and \
                    (second_seeded_players[i] in group):
                    random.shuffle(second_seeded_players)
                    try:
                        sim_functions.check_same_group(top_seeded_players,
                                                second_seeded_players,
                                                grouped_players)
                    except:
                        return second_seeded_players

        return second_seeded_players
    
    def gen_gsl_playoffs(top_seed_players, second_seed_players, groups_lists):
        """
        Summary:
            Takes in a list of top seeded players, a list of lower seeded players, and
            previously grouped players. The output ensures a set of 4 matchups that
            do not repeat matchups from the group stage during the round of 8.

        Inputs:
            top_seed_players ([type]): [description]
            second_seed_players ([type]): [description]
            groups_lists ([type]): [description]

        Output:
            A list of tuples of generated matchups where the first player is the top
            seeded player and the second player is the lower seeded player.
        """
        matchups = list()
        # shuffle second seed
        random.shuffle(second_seed_players)

        # check if groups are same first
        second_seed_players = sim_functions.check_same_group(
            top_seed_players, second_seed_players, groups_lists
        )

        # create matchups
        for i in range(4):
            matchup = (top_seed_players[i], second_seed_players[i])
            matchups.append(matchup)
        return matchups

    def gen_matchups(first_group, second_group):
        """
        Summary:
            Gnerate a list of tuples for round of 8 matchups.

        Args:
            first_group : top seeded players
            second_group : lower seeded players

        Returns:
            List of tuples with first player being top seeded player and second player
            being the lower seeded player.
        """
        matchups = list()

        # shuffle second group
        random.shuffle(second_group)

        # create matchups
        for i in range(4):
            matchup = (first_group[i], second_group[i])
            matchups.append(matchup)
        
        return matchups

    def playoffs_eight(matchups, model, period_start, db):
        """
        Summary:
            This function simulates the GSL playoffs which starts with a round of 8,
            then round of 4, and finally a finals match.

            Round of 8 is a best of 5.
            Round of 4 and finals match is a best of 7.

        Args:
            matchups : list of tuples for round of 8 matchups
            model : prediction model
            period_start : start date required to generate ratings
            db : database used

        Returns:
            Python dictionary for each finish.
                ro8 and ro4 losers are included in a list of 4 and 2 players respectively.
        """
        ro8_losers = list()
        ro4_players = list()
        ro4_losers = list()
        final_players = list()

        # round of 8
        for matchup in matchups:
            res = sim_functions.sim_match(
                matchup[0], matchup[1], 5, model,
                period_start, db
            )
            ro4_players.append(res['winner'])
            ro8_losers.append(res['loser'])
        
        # round of 4
        for i in [0, 2]:
            res = sim_functions.sim_match(
                ro4_players[i], ro4_players[i+1], 7, model,
                period_start, db
            )

            final_players.append(res['winner'])
            ro4_losers.append(res['loser'])
        
        # finals

        final_results = sim_functions.sim_match(
            final_players[0], final_players[1], 7, model, period_start, db
        )

        results = {
            'first': final_results['winner'],
            'second': final_results['loser'],
            'ro4': ro4_losers,
            'ro8': ro8_losers
        }

        return results
    
    def playoffs_sixteen(first_group, second_group, third_group, groups,
                            model, period_start, db):
        """
        Summary:
            Simulates IEM Katowice formatted playoffs.

        Tournament details:
            Top seeded players move immediately to round of 8.
            Round of 16 and round of 8 are best of 5.
            Round of 4 and, third place, and final match are best of 7.

        Args:
            first_group : list of top seeded players
            second_group : list of second seeded players
            third_group : list of third seeded players
            groups : generated groups
            model : prediction model
            period_start : period start of tournament
            db : database object

        Returns:
            Python dictionary for each finish.
            ro16 and ro8 losers have 4 players each.
        """
        ro12_losers = list()
        ro12_winners = list()
        ro4_players = list()
        ro8_losers = list()
        ro4_losers = list()
        final_players = list()

        # generate groups
        # shuffle third group
        random.shuffle(third_group)
        
        # check if first round has players in the same group
        third_group = sim_functions.check_same_group(second_group, third_group, groups)

        # round of 16
        # generate ro16 matchups
        ro12_matchups = sim_functions.gen_matchups(second_group, third_group)
        # round of 16
        for matchup in ro12_matchups:
            res = sim_functions.sim_match(
                matchup[0], matchup[1], 5, model, period_start, db
            )
            ro12_winners.append(res['winner'])
            ro12_losers.append(res['loser'])
        
        # round of 8
        # shuffle round of 16 winners
        random.shuffle(ro12_winners)
        ro8_matchups = sim_functions.gen_matchups(first_group, ro12_winners)
        for matchup in ro8_matchups:
            res = sim_functions.sim_match(
                matchup[0], matchup[1], 5, model, period_start, db
            )
            ro4_players.append(res['winner'])
            ro8_losers.append(res['loser'])
        
        # round of 4
        for i in [0, 2]:
            res = sim_functions.sim_match(
                ro4_players[i], ro4_players[i+1], 7, model,
                period_start, db
            )

            final_players.append(res['winner'])
            ro4_losers.append(res['loser'])
        
        # third place match
        third_place_match = sim_functions.sim_match(
            ro4_losers[0], ro4_losers[1], 7, model, period_start, db
        )

        # final match
        final_match = sim_functions.sim_match(
            final_players[0], final_players[1], 7, model, period_start, db
        )

        # store results
        results = {
            'first' : final_match['winner'],
            'second' : final_match['loser'],
            'third' : third_place_match['winner'],
            'fourth' : third_place_match['loser'],
            'ro8' : ro8_losers,
            'ro12' : ro12_losers
        }

        assert len(ro12_losers) == 4
        assert len(ro8_losers) == 4

        return results