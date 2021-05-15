# Database Notes & Problems
	* Don't fully understand ratings table
	* Ratings don't match up to ratings shown on website
	* all types of ratings are low numbers whereas site shown ratings are in the thousands
	* also do not understand smoothed, precision
	* overall rating is an average of 3 matchup ratings
	* Number of games
		* Terran: 179978
		* Zerg: 200241
		* Protoss: 222430
		* Total: 362893
	* Matchup numbers:
		* TvZ: 79542
		* TvP: 69835
		* TvT: 28787
		* ZvT: 79542
		* ZvP: 90506
		* ZvZ: 50179
		* PvT: 69835
		* PvZ: 90506
		* PvP: 37928
	* Dataset is heterogenous: different countries, matchups, region locks, etc
	* some ratings are -1000, which could is strange, but doesn't seem to affect model results
		* extension: removing those leaves only about 61000 as opposed to over 300000
	* effective data ratings (rating differences between appropriate races) are normally distributed and require no transformations
	* There is no label imbalance because one player always wins

# Prediction Algorithm
	* Try 6 models: 1 for each matchup
	* Try 1 big model: using all data
	* Caveat: data is based on matches won
		* the winner encoding does not account for bo1, bo3, bo5, or bo7
	* CV: stratified k-fold, regular k-fold
		* data is already shuffled in train-test splitting
		* data is also pretty balanced, so no need for stratified k-fold
	* Removing too many features made everything worse
	* Completely ignoring time restraint when it comes to training/test models
	* removing extraneous (-1000, -2000, etc) ratings made prediction worse
	* removing random also made everything worse
	* conclusion: keep all the data in there
	* grab feature importances to show in report
	* look at how model performs on different categorizations
		* accuracy rates per match-up
		* maybe over patches (period)
		* rating differences
	* Test set: Last 20% of data, most recent matches

# Resources
	* CatBoost optimization guide: https://ai.plainenglish.io/catboost-cross-validated-bayesian-hyperparameter-tuning-91f1804b71dd
	* Read about matthew's corr coef: https://en.wikipedia.org/wiki/Matthews_correlation_coefficient#:~:text=The%20Matthews%20correlation%20coefficient%20(MCC,Matthews%20in%201975.
	* read about bayesian optimization