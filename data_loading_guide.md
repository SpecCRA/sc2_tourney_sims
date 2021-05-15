## Postgres login info
user: postgres
password: impreza

# Steps to get load psql file into database

1. log in as user postgres 

`su - postgres`

2. change working directory to where data is

`cd /home/specc/Documents/school_files/thesis/data/`

3. Go into psql and create the database
* Using projectdb as databasename

`psql`
`create database databaseName;`

db name: projectdb

4. Exit psql then load data

`ctrl + d`
`psql -d databaseName -f filename.ext`