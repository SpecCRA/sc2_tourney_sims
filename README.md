# Topic: Simulation Analysis of StarCraft 2 Tournament Formats with Aligulac Data

Code and files for Northwestern Master's in Data Science thesis.

# Summary

This project aims to analyze two tournament formats and professional StarCraft 2 players' performances in each format.
## Data
* Databse: [Aligulac](http://aligulac.com/)
* Database file is updated as of May 5, 2021 (1.2 gb+)

## Prediction Model
* Two finished models are developed and saved into the `/models/` folders. The CatBoost model named `match_predictor.cb` will be the prediction model used for the simulations. The other similar model uses a logistic regression and is named `logit_predictor.sav`.

## Simulation
* All files are in the `sim_scripts/` folder. The folder includes the scripts used to run a GSL style and IEM Katowice style tournament.
* The following tournaments were replicated:
    * 2021 GSL Season 1
    * 2020 IEM Katowice
    * 2021 IEM Katowice
* Results are stored in `sim_scripts/results` in separate CSV files.

## Notes
* See `project_notes.md` for a detailed outline of the project