#!/usr/bin/env python3

# Import packages

import psycopg2
import pandas as pd
from sqlalchemy import create_engine

# Start database engine
db_string = 'postgresql://postgres:impreza@localhost/projectdb'
db = create_engine(db_string)

con = psycopg2.connect(database="projectdb", user="postgres", password="impreza", host="127.0.0.1", port="5432")
curr = con.cursor()


# 