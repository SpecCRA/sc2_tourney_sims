# Database Notes & Problems
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
	* ratings used were from previous 2-week period of match
		* this uses previous ratings instead of matches within the same period to calculate ratings
	* There is no label imbalance because one player always wins
	* No real data shrinking had to occur because this is a database with a large majority of ranked players

# Prediction Algorithm
	* Tried logistic regression, SVM, XGBoost, CatBoost
	* Caveat: data is based on matches won
		* the winner encoding does not account for bo1, bo3, bo5, or bo7
	* CV: stratified k-fold, regular k-fold
		* data is already shuffled in train-test splitting
		* data is also pretty balanced, so no need for stratified k-fold
	* Removing too many features made everything worse
		* things like ranking among matchup helped
	* Completely ignoring time restraint when it comes to training/test models
	* removing extraneous (-1000, -2000, etc) ratings made prediction worse
	* removing random also made everything slightly worse
	* added player age into the features
	* added whether player A was higher ranked than player B as a feature
	* grab feature importances to show in report
	* optimizing feature: accuracy
	* Test set: Last 20% of data, most recent matches
	* Final model: optimized catboost, only slightly better than logistic regression
	* Null rate: 0.588165504968115 - this is the rate where one rating is simply higher than another

# Simulation Script
	* Tournaments selected
		* IEM Katowice 2020: https://liquipedia.net/starcraft2/IEM_Katowice/2020
		* IEM Katowice 2021: https://liquipedia.net/starcraft2/IEM_Katowice/2021
		* GSL Season 3 2020: https://liquipedia.net/starcraft2/Global_StarCraft_II_League/2020/Season_3

	* Match simulation setup:
		* Each map is treated as an independent event and will not rely on result of previous maps.
	* Player selection:
		* The list of players is taken directly from each tournament page.
		* The player list is the players who have qualified to play in the main tournaments.
	* Group creation is completely random and no seed is used.
	* GSL tournament formatting:
		* Caveat 1: groups are randomly seeded as opposed to relying on seeding from a ranking system
			* The group stage, round of 16 are chosen by the players in a particular format, and the resulting groups are not entirely even. There is often one or two peculiarly stacked groups.
			* I cannot programmatically account for the top seed's ability to change group dynamics by switching two players. There is no good way for me to manage player psychology in instances such as how certain players do not like playing against Protoss opponents.
		* Playoffs seeding:
			* The seeding format mimics how the modern GSL works.
				* Group winners play second seeded players.
				* Players from the same group will not play each other in the round of 8.
				* Second seeded players are shuffled and randomly drawn to each top seeded player.
	* Katowice tournament formatting:
		* Groups are again randomly chosen.
		* Groups winners are calculated by the following terms:
			* match wins
			* map wins
			* direct matchups
		* Playoff brackets mimic the 2020 and 2021 formats.
			* Group winners pass immediately to round of 8 to play round of 16 winners.
			* Second place and third place play one another.
			* Players from the same group cannot play each other in round of 16.
			* Third place players are shuffled.
			* Round of 16 winners are shuffled.
			* Previous points are in place to ensure first place group winners do not often play their second place group mates.
			* Third and fourth place match is played by round of 4 losers.
	* Data recorded:
		* Where players finish: group stage or some round of playoffs.
	* What is encapsulated by this simulation setup:
		* Bracket fluctuations - player and matchups are shuffled around.
		* There are times when players get favorable brackets for their preferred matchups.
		* Race vs Race dynamics. For instance, if TvP is historically Protoss favored, there may be a slight bias towards favoring a Protoss player in that matchup.
	* What to look for:
		* Double elimination group versus round robin robustness
		* Were the actual results a surprise?
	* Questions
		* how to manage uncertainty?
			* model uncertainty
			* how brackets play out

# Resources
	* CatBoost optimization guide: https://ai.plainenglish.io/catboost-cross-validated-bayesian-hyperparameter-tuning-91f1804b71dd
	* Read about matthew's corr coef: https://en.wikipedia.org/wiki/Matthews_correlation_coefficient#:~:text=The%20Matthews%20correlation%20coefficient%20(MCC,Matthews%20in%201975.
	* read about bayesian optimization