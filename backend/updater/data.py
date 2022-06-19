import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
from collections import defaultdict
from dataclasses import field

import pandas as pd
from pandas.core.frame import DataFrame
from utils.utilities import Utilities

from dataframes.form import Form
from dataframes.fixtures import Fixtures
from dataframes.standings import Standings
from dataframes.home_advantages import HomeAdvantages
from dataframes.team_ratings import TeamRatings
from dataframes.upcoming import Upcoming
from dataframes.season_stats import SeasonStats

utils = Utilities()

class Data:
    def __init__(self, current_season: int):
        self.current_season = current_season
        self.team_names: list[str] = field(default_factory=list)
        self.logo_urls: dict = defaultdict

        self.fixtures: Fixtures = Fixtures()
        self.standings: Standings = Standings()
        self.team_ratings: TeamRatings = TeamRatings()
        self.home_advantages: HomeAdvantages = HomeAdvantages()
        self.form: Form = Form()
        self.upcoming: Upcoming = Upcoming(current_season)
        self.season_stats: SeasonStats = SeasonStats()
    
    def built_all_dataframes(self) -> bool:
        return (self.fixtures.df is not None and self.standings.df is not None 
                and self.team_ratings.df is not None and self.home_advantages.df is not None 
                and self.form.df is not None and self.upcoming is not None 
                and self.season_stats is not None)
    
    def to_one_dataframe(self) -> DataFrame:
        return pd.concat((self.fixtures.df, self.standings.df, self.team_ratings.df, self.home_advantages.df, self.form.df, self.upcoming.df, self.season_stats.df), 1)

    def collapse_tuple_keys(self, d):
        if type(d) is not dict:
            if type(d) is float and math.isnan(d):
                # Remove NaN values
                return None
            return d
        
        new_d = {}
        for k, v in d.items():
            if type(k) is tuple:
                k = [x for x in k if x != '']  # Remove blank multi-index levels
                if len(k) == 1:
                    k = k[0]  # If only one level remains, take single heading
            
            if type(k) is list:
                # Separate multi-index into a nested dict
                k1 = str(k[0]) if type(k[0]) is int else utils.camel_case(k[0])
                k2 = str(k[1]) if type(k[1]) is int else utils.camel_case(k[1])
                if k1 in new_d:
                    new_d[k1][k2] = self.collapse_tuple_keys(v)
                else:
                    new_d[k1] = {k2: self.collapse_tuple_keys(v)}
            elif type(k) is int:
                new_d[str(k)] = self.collapse_tuple_keys(v)
            else:
                new_d[utils.camel_case(k)] = self.collapse_tuple_keys(v)
        
        return new_d
    
    def to_one_dict(self) -> dict:
        # Build one dict containing all dataframes
        if self.built_all_dataframes():
            d = {
                'lastUpdated': self.last_updated,
                'currentSeason': self.current_season,
                'teamNames': self.team_names,
                'logoURLs': self.logo_urls,
                'fixtures': self.fixtures.df.to_dict(orient='index'),
                'standings': self.standings.df.to_dict(orient='index'),
                'teamRatings': self.team_ratings.df.to_dict(orient='index'),
                'homeAdvantages': self.home_advantages.df.to_dict(orient='index'),
                'form': self.form.df.to_dict(orient='index'),
                'upcoming': self.upcoming.df.to_dict(orient='index'),
                'seasonStats': self.season_stats.df.to_dict(orient='index'),
            }
            # Collapse tuple keys, convert int key to str and remove NaN values
            d = self.collapse_tuple_keys(d)
            return d
        else:
            raise ValueError('❌ [ERROR] Cannot build one team data dict: A dataframe is empty')
