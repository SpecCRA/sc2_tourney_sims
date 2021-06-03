#!/usr/bin/env python
import pandas as pd
import psycopg2
import numpy as np
from sqlalchemy import create_engine
import datetime

class match_info():
    def __init__(self):
        pass

    def create_date_str(start):
        """
        Takes a start date and generates a new start and
        end date as datetime objects.

        The end date is 2 weeks after the start date.

        Args:
            start (string): date in YYYY/MM/DD format

        Returns:
            start and end datetime objects in YYYY/MM/DD format
        """
        # Create start and end dates for a tournament period query
        start_date = pd.to_datetime(start)
        end_date = start_date + pd.Timedelta(days=18)

        return start_date.strftime('%Y/%m/%d'), end_date.strftime('%Y/%m/%d')

    def query_period(start_date, end_date, db):
        """
        Queries database for the period in a given start date.

        Args:
            start_date ([string]): Input a date format in YYYY/MM/DD
            db ([Postgres db object with cursor])

        Return:
            period ID of specified start date
        """

        period_query = f"""
                SELECT id
                FROM PERIOD p
                WHERE start >= '{start_date}'
                    AND p.end <= '{end_date}'
            """
        df = pd.read_sql_query(period_query, db)

        if len(df) >= 1:
            return list(df['id'][0])
        else:
            return("try an earlier date")

    def query_player_rating(player_id, period_id, db):
        """

        """
        period_id -= 1 # take the previous period's ratings
        rating_query = f"""
            SELECT period_id, player_id, rating,
                (rating + rating_vp) as rating_vp,
                (rating + rating_vt) as rating_vt,
                (rating + rating_vz) as rating_vz,
                position, position_vp, position_vt, position_vz
            FROM RATING
            WHERE position IS NOT NULL
                AND player_id = {player_id}
                AND period_id = {period_id}
            """

        rating_df = pd.read_sql_query(rating_query, db)

        return rating_df
    
    def calc_age(player_id, period_id, db):
        """
        Calculates a player's age at the time of the matchup.
        The age is the player's western age.
        """
        birthday_query = f"""
            SELECT birthday
            FROM PLAYER
            WHERE id = {player_id}
        """

        period_query = f"""
            SELECT start
            FROM PERIOD
            WHERE id = {period_id}
        """

        birthday = pd.read_sql_query(birthday_query, db).iloc[0]['birthday']
        period_start = pd.read_sql_query(period_query, db).iloc[0]['start']

        diff = period_start - birthday
        age = int(diff/datetime.timedelta(days=365))

        return age

    def player_info(player_tag, db):
        """
        Takes a player's user tag and outputs the player's basic information:
            1. database ID
            2. Gamer tag
            3. Name
            4. Primary race

        The function only works for the highest ranked player to mitigate players with
            similar or the same tag. The purpose of the simulation is only around the
            top players.
        """

        player_query = f"""
            SELECT p.id, tag, name, race
            FROM PLAYER p
                JOIN RATING r
                ON p.id = r.player_id
            WHERE LOWER(tag) = '{player_tag}'
            ORDER BY rating DESC
            LIMIT 1
        """

        player_df = pd.read_sql_query(player_query, db)

        return player_df

    def gather_player_df(player_tag, period_id, db):
        """
        Grabs a player's rating information during the appropriate period
            by his tag. The output dataframe includes one player's information including:
                * relevant game information
                * ratings
                * positions
                * period queried
                * player's age at the time of the period

        Args:
            player_tag (string): player's gamer tag
            period_id (int): generated period ID based on a start date
            db (Postgres db object with cursor)

        Returns:
            pandas DataFrame
        """

        player_df = match_info.player_info(player_tag, db)
        rating_df = match_info.query_player_rating(
            player_df.iloc[0]['id'], period_id, db
        )

        player_df['age'] = match_info.calc_age(
            player_df.iloc[0]['id'], period_id, db
        )

        ohe_race = pd.get_dummies(['Z', 'T', 'P'], prefix='race')

        player_df = pd.merge(player_df, rating_df,
                                left_on='id', right_on='player_id')

        if player_df['race'].iloc[0] == 'Z':
            player_df = pd.concat([player_df, ohe_race.iloc[[0]]], axis=1)
        elif player_df['race'].iloc[0] == 'T':
            player_df = pd.concat([player_df, ohe_race.iloc[[1]].reset_index(drop=True)],
                                    axis=1)
        elif player_df['race'].iloc[0] == 'P':
            player_df = pd.concat([player_df, ohe_race.iloc[[2]].reset_index(drop=True)],
                                    axis=1)

        return player_df
    
    def combine_player_df(df1, df2):
        """
        Takes two players cleaned DataFrames with player info and combines it into one.

        Args:
            df1
            df2

        Returns:
            Combined DataFrame all in one row
        """
        combined_df = df1.merge(df2,
                                left_on='period_id',
                                right_on='period_id',
                                suffixes=('_a', '_b'))
        return combined_df
    
    def create_eff_ratings(player_a_or_b, df):
        """
        Takes a combined players DataFrame and adds a new column for effective ratings
            based on the race matchup.
        """
        opp = None
        if player_a_or_b == 'a':
            opp = 'b'
        else:
            opp = 'a'

        col_name = f'player_{opp}_eff_rating'

        if df['race_' + player_a_or_b].iloc[0] == 'Z':
            df[col_name] = df.iloc[0]['rating_vz_' + opp]
        elif df['race_' + player_a_or_b].iloc[0] == 'T':
            df[col_name] = df.iloc[0]['rating_vt_' + opp]
        else:
            df[col_name] = df.iloc[0]['rating_vp_' + opp]

    def process_calcs(df):
        """
        Performs calculations with a combined DataFrame with effective ratings in tact.
            This function calculates the effective rating difference between two players
            and adds a column for which player is higher ranked.

        Returns:
            pandas DataFrame
        """
        df['ratings_diff'] = df['player_a_eff_rating'] - df['player_b_eff_rating']

        # assign value for higher ranked player
        if df.iloc[0]['rating_a'] > df.iloc[0]['rating_b']:
            df['higher_ranked_a'] = 1
        else:
            df['higher_ranked_a'] = 0
        
        return df
    
    def clean_df(df):
        """
        Takes a combined player DataFrame and cleans it, prepping it for model input.

        This function renames some columns then rearranges them for model input.

        Args:
            df (pandas DataFrame)

        Returns:
            cleaned DataFrame
        """
        # rename columns
        cols_dict = {
            'race_P_a': 'pla_race_P',
            'race_T_a': 'pla_race_T',
            'race_Z_a': 'pla_race_Z',
            'race_P_b': 'plb_race_P',
            'race_T_b': 'plb_race_T',
            'race_Z_b': 'plb_race_Z',
        }

        df = df.rename(columns=cols_dict)

        # rearrange columns
        df = df[['rating_a',
            'rating_vp_a',
            'rating_vt_a',
            'rating_vz_a',
            'position_a',
            'position_vp_a',
            'position_vt_a',
            'position_vz_a',
            'rating_b',
            'rating_vp_b',
            'rating_vt_b',
            'rating_vz_b',
            'position_b',
            'position_vp_b',
            'position_vt_b',
            'position_vz_b',
            'race_P_a',
            'race_T_a',
            'race_Z_a',
            'race_P_b',
            'race_T_b',
            'race_Z_b',
            'player_a_eff_rating',
            'player_b_eff_rating',
            'ratings_diff',
            'higher_ranked_a',
            'age_a',
            'age_b']]

        return df