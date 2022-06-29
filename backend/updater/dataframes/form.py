from collections import defaultdict

import pandas as pd
from pandas import DataFrame
from timebudget import timebudget
from utils.utilities import Utilities

from dataframes.df import DF
from dataframes.fixtures import Fixtures
from dataframes.standings import Standings
from dataframes.team_ratings import TeamRatings

utils = Utilities()

class Form(DF):
    def __init__(self, d: DataFrame = DataFrame()):
        super().__init__(d, 'form')
        
    def get_prev_matchday(self):
        return self._get_matchday(n_back=1)

    def get_current_matchday(self):
        return self._get_matchday(n_back=0)

    def get_current_form_rating(self, team_name: str):
        current_matchday = self.get_current_matchday()
        matchday = self._get_last_played_matchday(current_matchday, team_name)
        return self._get_form_rating(team_name, matchday, 5)

    def get_long_term_form_rating(self, team_name: str):
        current_matchday = self.get_current_matchday()
        matchday = self._get_last_played_matchday(current_matchday, team_name)
        return self._get_form_rating(team_name, matchday, 10)

    @staticmethod
    def _n_should_have_played(current_matchday: int, maximum: int) -> int:
        return min(maximum, current_matchday)

    def _not_played_current_matchday(
        self,
        recent_games: list[str],
        current_matchday: int,
        N: int
    ) -> bool:
        n_should_have_played = self._n_should_have_played(current_matchday, N)
        return len(recent_games) != n_should_have_played

    def _get_last_played_matchday2(self, current_matchday: int, team_name: str) -> int:
        matchday = current_matchday
        if self._not_played_current_matchday(team_name, current_matchday):
            # Use previous matchday's form
            matchday = self.get_prev_matchday()
        return matchday

    def _get_last_played_matchday(self, current_matchday: int, team_name: str) -> int:
        matchday = current_matchday
        while self.df.at[team_name, (matchday, 'Score')] is None and matchday > 0:
            matchday -= 1
        return matchday

    def _get_form(self, team_name: str, matchday: int) -> list[str]:
        form = []
        if matchday is not None:
            form = self.df.at[team_name, (matchday, 'Form5')]
            if form is None:
                form = []
            else:
                form = list(reversed(form))  # Most recent

        form = ['None'] * (5 - len(form)) + form  # Pad list

        return form

    def _not_played_current_matchday(
        self,
        team_name: str,
        current_matchday: int
    ) -> bool:
        return self.df.at[team_name, (current_matchday, 'Score')] == None

    def _get_latest_teams_played(
        self,
        team_name: str,
        matchday: int,
        last_n_matchdays: list[int]
    ) -> list[str]:
        latest_teams_played = []
        if matchday is not None:
            latest_teams_played = self._get_matchday_range_values(team_name, 'Team', last_n_matchdays)
        return latest_teams_played

    def _get_form_rating(self, team_name: str, matchday: int, n_games: int) -> float:
        rating = 0
        if matchday is not None:
            rating = (self.df.at[team_name, (matchday, f'FormRating{n_games}')] * 100).round(1)
        return rating

    def _get_won_against_star_team(
        self,
        team_name: str,
        matchday: int,
        last_n_matchdays: list[int]
    ) -> list[str]:
        won_against_star_team = []  # 'star-team' or 'not-star-team' elements
        if matchday is not None:
            won_against_star_team = self._get_matchday_range_values(
                team_name, 'BeatStarTeam', last_n_matchdays)
        return won_against_star_team

    def _get_matchday_range_values(
        self,
        team_name: str,
        column_name: str,
        matchday_ns: list[int]
    ) -> list[bool]:
        col_headings = [(matchday, column_name) for matchday in matchday_ns]
        values = [self.df.at[team_name, col] for col in col_headings]
        return values


    def _get_matchday(self, n_back=0):
        current_matchday = None
        matchdays = self.df.columns.unique(level=0)
        if len(matchdays) != 0:
            current_matchday = matchdays[-(n_back+1)]
        return current_matchday
    
    def get_recent_form(self, team_name: str):
        matchday = self.get_current_matchday()
        team_row = self.df.loc[team_name]
        # Played games sorted by date
        games = sorted([team_row[i] for i in range(1, matchday+1) if team_row[i]['Score'] != 'None - None'], key=lambda x: x['Date'])
        if len(games) > 5:
            games = games[-5:]  # Take last 5 games
        
        # Take most recent form values
        form_lst = list(reversed(games[-1]['Form5']))
        rating = (games[-1]['FormRating5'] * 100).round(1)
        
        # Construct lists of last 5 values
        teams_played = [game['Team'] for game in games]
        won_against_star_team = [game['BeatStarTeam'] for game in games]
        
        return form_lst, teams_played, rating, won_against_star_team

    # def get_recent_form2(
    #     self,
    #     team_name: str
    # ) -> tuple[list[str], DataFrame, float, list[str]]:
    #     current_matchday = self.get_current_matchday()
    #     matchday = self._get_last_played_matchday(current_matchday, team_name)
        
    #     # Get precomputed form list and rating
    #     form_lst = self._get_form(team_name, matchday)  # List of five 'W', 'D' or 'L'
    #     rating = self._get_form_rating(team_name, matchday, 5)

    #     # Construct equivalent list to form list for other attributes
    #     matchdays = self._last_n_matchdays(team_name, matchday, 5)
    #     teams_played = self._get_latest_teams_played(team_name, matchday, matchdays)
    #     won_against_star_team = self._get_won_against_star_team(team_name, matchday, matchdays)

    #     return form_lst, teams_played, rating, won_against_star_team

    @staticmethod
    def _get_points(gd: int) -> int:
        if gd > 0:
            pts = 3
        elif gd == 0:
            pts = 1
        else:
            pts = 0
        return pts

    @staticmethod
    def _get_gd(score: str, at_home: bool) -> int:
        home, away = utils.extract_int_score(score)
        gd = home - away if at_home else away - home
        return gd

    @staticmethod
    def _append_to_from_str(form_str: list, home: int, away: int, at_home: bool):
        if home == away:
            result = 'D'
        elif (at_home and home > away) or (not at_home and home < away):
            result = 'W'
        elif (at_home and home < away) or (not at_home and home > away):
            result = 'L'
        form_str.append(result)

    @staticmethod
    def _get_idx(lst: list[any], val: any):
        idx = None
        for i, v in enumerate(lst):
            if v == val:
                idx = i
                break
        return idx

    def _last_n_matchdays(self, team_name: str, matchday_no: int, n: int):
        # All matchday numbers sorted by date
        all_matchdays = self.df.loc[team_name][(slice(None), 'Date')][self.df.loc[team_name][(slice(None), 'Score')] != None]
        all_matchdays = all_matchdays.sort_values(inplace=False)
        all_matchdays = all_matchdays.index.values
        
        matchday_no_idx = self._get_idx(all_matchdays, matchday_no)

        if matchday_no_idx is None:
            raise ValueError()

        # Slice off preceeding matchdays
        last_n_matchdays = all_matchdays[:matchday_no_idx+1]

        # Get the last n
        if len(all_matchdays) > n:
            last_n_matchdays = last_n_matchdays[-n:]  # Return last n

        return last_n_matchdays

    def _build_form_str(self, form, team, last_n_matchday_nos):
        form_str = []
        for n in reversed(last_n_matchday_nos):
            score = form.at[team, (n, 'Score')]
            if score is not None:
                home, away = utils.extract_int_score(score)
                at_home = form.at[team, (n, 'AtHome')]
                self._append_to_from_str(form_str, home, away, at_home)
            else:
                form_str.append('N')

        return ''.join(form_str)

    @staticmethod
    def _calc_form_rating(
        team_ratings: TeamRatings,
        teams_played: list[str],
        form_str: str,
        gds: list[int]
    ) -> float:
        form_rating = 0.5  # Default percentage, moves up or down based on performance
        if form_str is not None:  # If games have been played this season
            n_games = len(form_str)
            for idx, result in enumerate(form_str):
                # Convert opposition team initials to their name
                opp_team = teams_played[idx]
                opp_team_rating = team_ratings.df.at[opp_team, 'TotalRating']
                # max_team_rating = team_ratings.df['TotalRating'].iloc[0]
                gd = abs(gds[idx])

                # Increment form score based on rating of the team they've won, drawn or lost against
                if result == 'W':
                    form_rating += (opp_team_rating / n_games) * gd
                elif result == 'L':
                    form_rating -= (opp_team_rating / n_games) * gd

        form_rating = min(max(0, form_rating), 1)  # Cap rating

        return form_rating

    def _get_form_matchday_range_values(
        self,
        form: DataFrame,
        team_name: str,
        column_name: str,
        matchday_ns: list[int]
    ) -> list:
        col_headings = [(matchday, column_name) for matchday in matchday_ns]
        values = [form.at[team_name, col] for col in col_headings]
        return values

    @staticmethod
    def _get_played_matchdays(fixtures: Fixtures) -> list[int]:
        status = fixtures.df.loc[:, (slice(None), 'Status')]
        # Remove cols for matchdays that haven't played yet
        status = status.loc[:, (status == 'FINISHED').any()]
        matchday_nos = sorted(list(status.columns.get_level_values(0)))
        return matchday_nos
    
    def _insert_cum_gd_pts(self, d, gd, pts, matchday_no, teams_matchdays, idx):
        cum_gd = gd
        cum_pts = pts
        if idx > 0:
            prev_gd = d[(teams_matchdays[idx-1], 'CumGD')][-1]
            prev_pts = d[(teams_matchdays[idx-1], 'CumPoints')][-1]
            cum_gd = gd + prev_gd
            cum_pts = pts + prev_pts
        d[(matchday_no, 'CumGD')].append(cum_gd)
        d[(matchday_no, 'CumPoints')].append(cum_pts)
    
    def _insert_gd_pts(self, d, team, matchday_no, form, teams_matchdays, idx):
        gd = 0
        pts = 0
        if form.at[team, (matchday_no, 'Score')] is not None:
            at_home = form.at[team, (matchday_no, 'AtHome')]
            gd = self._get_gd(form.at[team, (matchday_no, 'Score')], at_home)
            pts = self._get_points(gd)
        d[(matchday_no, 'GD')].append(gd)
        d[(matchday_no, 'Points')].append(pts)
        
        self._insert_cum_gd_pts(d, gd, pts, matchday_no, teams_matchdays, idx)
    
    def _insert_won_against_star_team(self, d, form, team_ratings, team, matchday_no, star_team_threshold):
        won_against_star_team = False
        if form.at[team, (matchday_no, 'Score')] is not None:
            opp_team = form.at[team, (matchday_no, 'Team')]
            opp_team_rating = team_ratings.df.at[opp_team, 'TotalRating']
            won_against_star_team = opp_team_rating > star_team_threshold
        d[(matchday_no, 'BeatStarTeam')].append(won_against_star_team)
    
    def _insert_position_columns(self, df, all_matchdays):
        for matchday_no in all_matchdays:
            df.sort_values(by=[(matchday_no, 'CumPoints'),
                               (matchday_no, 'CumGD')],
                           ascending=False, 
                           inplace=True)
            df[matchday_no, 'Position'] = list(range(1, 21))
    
    def _insert_form(self, d, form, team_ratings, team, matchday_no, teams_matchdays, idx, N):
        # Get last idx of matchday that has been played
        while idx >= 0 and form.at[team, (teams_matchdays[idx], 'Score')] is None:
            idx -= 1
        
        # Insert form string for last N games
        last_n_matchday_nos = teams_matchdays[max(0, idx-N+1):idx+1]
        form_str = self._build_form_str(form, team, last_n_matchday_nos)
        d[(matchday_no, 'Form' + str(N))].append(form_str)

        # Insert form rating for last N games
        gds = [d[(md, 'GD')][-1] for md in last_n_matchday_nos]
        teams_played = self._get_form_matchday_range_values(form, team, 'Team', last_n_matchday_nos)
        form_rating = self._calc_form_rating(team_ratings, teams_played, form_str, gds)
        d[(matchday_no, 'FormRating' + str(N))].append(form_rating)

    def _form_columns(
        self,
        form: DataFrame,
        team_ratings: TeamRatings,
        star_team_threshold: float
    ):
        all_matchdays = set(form.columns.get_level_values(0).unique())
        columns = ['GD', 'Points', 'CumGD', 'CumPoints', 'BeatStarTeam', 
                   'Form5', 'FormRating5', 'Form10', 'FormRating10']
        
        d = defaultdict(lambda: [])
        for team, row in form.iterrows():
            teams_matchdays = row[(slice(None), 'Date')][row[(slice(None), 'Score')] != None]
            # Matchdays sorted by date played
            teams_matchdays = teams_matchdays.sort_values(inplace=False).index.values
            
            for idx, matchday_no in enumerate(teams_matchdays):
                self._insert_gd_pts(d, team, matchday_no, form, teams_matchdays, idx)
                self._insert_won_against_star_team(d, form, team_ratings, team, matchday_no, star_team_threshold)
                self._insert_form(d, form, team_ratings, team, matchday_no, teams_matchdays, idx, 5) 
                self._insert_form(d, form, team_ratings, team, matchday_no, teams_matchdays, idx, 10) 
            
            # Fill in any empty (non-played) matchdays
            for matchday_no in all_matchdays - set(teams_matchdays):
                for col in columns:
                    d[(matchday_no, col)].append(np.nan)
        
        df = pd.DataFrame.from_dict(d)
        df.index = form.index
        
        self._insert_position_columns(df, all_matchdays)
                
        return df

    def _clean_dataframe(self, form: DataFrame, matchday_nos: list[int]) -> DataFrame:
        # self._convert_team_cols_to_initials(form, matchday_nos)
        # Drop columns used for working
        form = form.drop(columns=['Points'], level=1)
        form = form.reindex(sorted(form.columns.values), axis=1)
        form = form.sort_values(by=[(max(matchday_nos), 'FormRating5')], ascending=False)
        return form

    @timebudget
    def build(
        self,
        fixtures: Fixtures,
        standings: Standings,
        team_ratings: TeamRatings,
        star_team_threshold: float,
        display: bool = False
    ):
        """ Assigns self.df to a dataframe containing the form data for each team
            for the matchdays played in the current season.

            Rows: the 20 teams participating in the current season.
            Columns (multi-index):
            ---------------------------------------------------------------------------------------------------------------------------------
            |                                                            [MATCHDAY NUMBER]                                                  |
            |-------------------------------------------------------------------------------------------------------------------------------|
            | Date | Team | Score | GD | Points | Position | Form5 | Form10 | FormRating5 | FormRating10 | CumGD | CumPoints | BeatStarTeam |

            [MATCHDAY NUMBER] int: the numbers of the matchdays that have been 
                played.
            Date: the datetime of the team's game played on that matchday.
            Team str: the initials of the opposition team played on that matchday.
            Score str: the score 'X - Y' of the game played on that matchday.
            GD int: the positive or negative goal difference achieved on that 
                matchday from the perspective of the team (row).
            Points int: the points achieved on that matchday from the perspective 
                of the team (row).
            Position int: the league standings position held on that matchday
            Form5 str: the form string up to the last 5 games (e.g. WWLDW) with the
                most recent result on the far left. String can take characters
                W, L, D or N (none - game not played).
            Form10: the form string up to the last 10 games (e.g. WWLDDLWLLW) with 
                the most recent result on the far left. String can take characters
                W, L, D or N (none - game not played).
            FormRating5 float: the calculated form rating based on the results of
                up to the last 5 games.
            FormRating10 float: the calculated form rating based on the results of
                up to the last 5 games.
            CumGD: the cumulative GD achieved across the current matchday
                and all matchdays prior.
            CumPoints: the cumulative points aquired across the current matchday
                and all matchdays prior.
            BeatStarTeam bool: whether the team beat the opposition team
                and that team was considered a 'star team'

        Args:
            fixtures Fixtures: a completed dataframe containing past and future
                fixtures for each team within the current season
            standings Standings: a completed dataframe filled with standings data 
                for recent seasons
            team_ratings TeamRatings: a completed dataframe filled with long-term
                ratings for each team
            star_team_threshold float: the minimum team ratings required for a team
                to be considered a star team
            display (bool, optional): flag to print the dataframe to console after 
                creation. Defaults to False.
        """
        print('🛠️  Building form dataframe... ')
        self._check_dependencies(fixtures, standings, team_ratings)

        matchday_nos = self._get_played_matchdays(fixtures)
        form = fixtures.df[matchday_nos].drop(columns=['Status'], level=1)

        form_rows = self._form_columns(form, team_ratings, star_team_threshold)
        form = pd.concat([form, form_rows], axis=1)

        form = self._clean_dataframe(form, matchday_nos)

        if display:
            print(form)

        self.df = form