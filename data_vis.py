from pandas.core.frame import DataFrame
from plotly.missing_ipywidgets import FigureWidget
from data import Fixtures, Form, HomeAdvantages, PositionOverTime, TeamRatings
import os
from typing import Optional
import plotly
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from timebudget import timebudget


class DataVis:
    def __init__(self):
        # Fixture graph
        self.fixtures_colour_scale = ['#01c626', '#08a825',  '#0b7c20', '#0a661b',
                                      '#064411', '#000000', '#5b1d15', '#85160f',
                                      '#ad1a10', '#db1a0d', '#fc1303']

        self.team_colours = {
            'Sheffield United FC': 'rgb(238, 39, 55)',
            'Leeds United FC': 'rgb(255, 205, 0)',
            'Aston Villa FC': 'rgb(103, 14, 54)',
            'Fulham FC': 'rgb(204, 0, 0)',
            'Wolverhampton Wanderers FC': 'rgb(253, 185, 19)',
            'West Ham United FC': 'rgb(122, 38, 58)',
            'West Bromwich Albion FC': 'rgb(18, 47, 103)',
            'Tottenham Hotspur FC': 'rgb(19, 34, 87)',
            'Southampton FC': 'rgb(215, 25, 32)',
            'Newcastle United FC': 'rgb(45, 41, 38)',
            'Manchester United FC':  'rgb(218, 41, 28)',
            'Manchester City FC': 'rgb(108, 171, 221)',
            'Liverpool FC': 'rgb(200, 16, 46)',
            'Leicester City FC': 'rgb(0, 83, 160)',
            'Everton FC': 'rgb(39, 68, 136)',
            'Crystal Palace FC': ' rgb(27, 69, 143)',
            'Chelsea FC': 'rgb(3, 70, 148)',
            'Burnley FC': 'rgb(108, 29, 69)',
            'Brighton and Hove Albion FC': 'rgb(0, 87, 184)',
            'Arsenal FC': 'rgb(239, 1, 7)',
            'Norwich City FC': 'rgb(0, 166, 80)',
            'Cardiff City FC': 'rgb(0, 112, 181)',
            'Watford FC': 'rgb(237, 33, 39)',
            'Swansea City FC': 'rgb(18, 18, 18)',
            'Stoke City FC': 'rgb(224, 58, 62)',
            'Huddersfield FC': 'rgb(14, 99, 173)',
            'Bournemouth FC': 'rgb(218, 41, 28)',
            'Brentford FC': 'rgb(227, 6, 19)'
        }

    # ------------ FIXTURES GRAPHS -------------

    def create_fixtures_fig(self, x: list[datetime], y: list[float], details: list[str], sizes: list[int], NOW: datetime) -> FigureWidget:
        fig = go.Figure(data=go.Scatter(x=x,
                                        y=y,
                                        mode='lines+markers',
                                        marker=dict(size=sizes,
                                                    color=y,
                                                    colorscale=self.fixtures_colour_scale),
                                        line=dict(color='#737373'),
                                        text=details,
                                        hovertemplate="<b>%{text}</b><br>%{x|%d %b %Y}<br>Team rating: <b> %{y:.1f}%</b><extra></extra>",
                                        hoverinfo=('x+y+text'),
                                        ),
                        )

        fig.add_shape(go.layout.Shape(type="line",
                                      yref="paper",
                                      xref="x",
                                      x0=NOW,
                                      y0=0.04,
                                      x1=NOW,
                                      y1=1.01,
                                      line=dict(color="black",
                                                width=1,
                                                dash="dot")))

        y_values = [i for i in range(0, 101, 10)]
        
        fig.update_layout(
            yaxis=dict(
                title_text="Calculated Team Rating",
                ticktext=[f"{val}%" for val in y_values],
                tickvals=y_values,
                gridcolor='gray',
                showline=False,
                zeroline=False,

            ),
            xaxis=dict(
                title_text="Matchday",
                linecolor="black",
                showgrid=False,
                showline=False,

                ticktext=[i for i in range(2, len(x)+2, 2)],
                tickvals=[x[i] for i in range(1, len(x)+1, 2)],
            ),
            margin=dict(
                l=50,
                r=50,
                b=10,
                t=10,
                pad=4
            ),
            plot_bgcolor='#fafafa',
            paper_bgcolor='#fafafa',
        )
        
        return fig

    def fixtures_data_points(self, team_fixtures: DataFrame, team_ratings: TeamRatings, home_advantages: HomeAdvantages, sizes: list[int], NOW: datetime, N_MATCHES: int, BIG_MARKER_SIZE: int) -> tuple[list[datetime], list[float], list[str]]:
        x, y, details = [], [], []
        for match_n in range(N_MATCHES):
            match = team_fixtures[match_n+1]

            # Append single datetime value of matchday to x-axis
            x.append(match['Date'].to_pydatetime())

            # Get rating of the opposition team
            rating = team_ratings.df.loc[match['Team'], 'TotalRating']
            # Decrease other team's rating if you're playing at home
            if match['HomeAway'] == 'Home':
                rating *= (1 -
                           home_advantages.df.loc[match['Team'], 'TotalHomeAdvantage'][0])
            # Append percentage rating value of opposition team playing on this matchday
            y.append(rating*100)

            # Add team played, home or away and the final score if game has already happened
            if match['Score'] != "None - None":
                match_detail = f"{match['Team']} ({match['HomeAway']})  {match['Score']}"
            else:
                match_detail = f"{match['Team']} ({match['HomeAway']})"
            details.append(match_detail)

            # Increase size of point marker if it's the current upcoming match
            if match_n == 0:
                # If we haven't played first game of season
                if NOW < x[-1]:
                    sizes[match_n] = BIG_MARKER_SIZE
            elif (match_n != N_MATCHES) and (x[-2] < NOW <= x[-1]):
                sizes[match_n] = BIG_MARKER_SIZE

        # Sort the data by date to remove errors due to match rescheduling
        x, y, details = zip(*sorted(zip(x, y, details)))

        return x, y, details

    def save_fig(self, fig, team_name: str, graph_type: str, path: str = './static/graphs/', auto_open: bool = False, display_mode_bar: bool = False, scroll_zoom: bool = False):
        file_team_name = '-'.join(team_name.lower().split()
                                  [:-1]).replace('&', 'and')

        temp_path = f'{path}{file_team_name}/temp-{graph_type}-{file_team_name}.html'
        path = f'{path}{file_team_name}/{graph_type}-{file_team_name}.html'

        # Save plot as HTML file
        plotly.offline.plot(
            fig,
            filename=temp_path,
            auto_open=auto_open,
            config={'displayModeBar': display_mode_bar, 'scrollZoom': scroll_zoom})

        try:
            os.rename(temp_path, path)
        except WindowsError:
            os.remove(path)
            os.rename(temp_path, path)

    @timebudget
    def update_fixtures(self, fixtures: Fixtures, team_ratings: TeamRatings, home_advantages: HomeAdvantages, team_name: str = '', display: bool = False):
        if not team_name:
            print("📊 Updating all team fixtures graphs...")
            teams_to_update = fixtures.df.index.values.tolist()
        else:
            print(f"📊 Updating {team_name} fixture graph...")
            teams_to_update = [team_name]

        DEFAULT_MARKER_SIZE = 14
        BIG_MARKER_SIZE = 26  # Used to highlight next game
        NOW = datetime.now()
        N_MATCHES = 38
        # Sizes of each data point marker
        sizes = [DEFAULT_MARKER_SIZE] * N_MATCHES

        for team in teams_to_update:
            # Get row of fixtures dataframe
            team_fixtures = fixtures.df.loc[team]
            x, y, details = self.fixtures_data_points(
                team_fixtures, team_ratings, home_advantages, sizes, NOW, N_MATCHES, BIG_MARKER_SIZE)

            fig = self.create_fixtures_fig(x, y, details, sizes, NOW)

            if display:
                fig.show()

            self.save_fig(fig, 
                          team, 
                          'fixtures',
                          path='./templates/graphs/')

    # ------------- FORM OVER TIME GRAPHS -------------

    def create_form_over_time_fig(self, x: list[datetime], ys: list[list[float]], matchday_labels: list[str], team_name: str, team_names: list[str]) -> FigureWidget:
        fig = go.Figure()

        for idx, y in enumerate(ys):
            if team_names[idx] != team_name:
                fig.add_trace(go.Scatter(x=x,
                                         y=y,
                                         name=team_names[idx],
                                         mode='lines',
                                         line=dict(color='#d3d3d3'),
                                         showlegend=False,
                                         hovertemplate=f"<b>{team_names[idx]}</b><br>" +
                                         "Matchday %{x}<br>Form: <b>%{y:.1f}%</b><extra></extra>",
                                         hoverinfo=('x+y'),
                                         ))
            else:
                # Save index the input teams is found for plotting the final line
                team_idx = idx

        # Add this as teams name last to have this line on top
        fig.add_trace(go.Scatter(x=x,
                                 y=ys[team_idx],
                                 name=team_names[team_idx],
                                 mode='lines',
                                 line=dict(color=self.team_colours[team_names[team_idx]],
                                           width=4),
                                 showlegend=False,
                                 hovertemplate=f"<b>{team_names[team_idx]}</b><br>" +
                                 "Matchday %{x}<br>Form: <b>%{y:.1f}%</b><extra></extra>",
                                 hoverinfo=('x+y'),
                                 ))
        
        y_labels = [i for i in range(0, 101, 10)]
        
        fig.update_layout(
            yaxis=dict(
                title_text="Form Rating %",
                ticktext=y_labels,
                tickvals=y_labels,
                showgrid=False,
                showline=False,
                zeroline=False,
            ),
            xaxis=dict(
                title_text="Matchday",
                linecolor="black",
                tickmode="array",
                dtick=1,
                ticktext=matchday_labels,
                tickvals=x,
                showgrid=False,
                showline=False,
            ),
            margin=dict(
                l=50,
                r=50,
                b=10,
                t=10,
                pad=4
            ),
            plot_bgcolor='#fafafa',
            paper_bgcolor='#fafafa',
        )
        
        return fig

    def form_over_time_data_points(self, form: Form) -> tuple[list[datetime], list[str], list[list[float]]]:
        x_cols = form.df.iloc[:, form.df.columns.get_level_values(1) == 'Date']
        y_cols = form.df.iloc[:, form.df.columns.get_level_values(1) == 'FormRating']

        # All ys have the same x date values
        x = []
        for _, col_data in x_cols.iteritems():
            # Take the median date for that matchday
            median_date = np.median(col_data.values.tolist())
            # Convert from numpy date to datetime format
            x.append(datetime.utcfromtimestamp(median_date/1e9))

        ys = []
        for _, row_data in y_cols.iterrows():
            y = row_data.values.tolist()
            y = list(map(lambda x: x * 100, y))  # Convert to percentages
            ys.append(y)

        # Sort the x-axis data by date to remove errors due to match rescheduling
        matchday_labels = sorted(list(form.df.columns.unique(level=0)))
        # Remove 'Matchday' prefix and just store sorted integers
        x, matchday_labels, *ys = zip(*sorted(zip(x, matchday_labels, *ys)))

        return x, matchday_labels, ys

    @timebudget
    def update_form_over_time(self, form: Form,  team_name: str = '', display: bool = False):
        if form.df.empty:
            print("Error: Cannot generate form over time graph; Form dataframe is empty")
        else:
            if not team_name:
                print("📊 Updating all teams form over time graphs...")
                teams_to_update = form.df.index.values.tolist()
            else:
                print(f"📊 Updating {team_name} form over time graph...")
                teams_to_update = [team_name]

            x, matchday_labels, ys = self.form_over_time_data_points(form)
            team_names = form.df.index.values.tolist()

            for team in teams_to_update:
                fig = self.create_form_over_time_fig(x, ys, matchday_labels, team, team_names)

                if display:
                    fig.show()

                self.save_fig(fig, team, 'form-over-time')

    # --------------------- POSITION OVER TIME GRAPHS --------------------------

    def create_position_over_time_fig(self, x: list[datetime], ys: list[list[int]], matchday_labels: list[str], team_name: str, team_names: list[str]) -> FigureWidget:
        fig = go.Figure()
        for idx, y in enumerate(ys):
            if team_names[idx] != team_name:
                fig.add_trace(go.Scatter(x=x,
                                         y=y,
                                         name=team_names[idx],
                                         mode='lines',
                                         line=dict(color='#d3d3d3'),
                                         showlegend=False,
                                         hovertemplate=f"<b>{team_names[idx]}</b><br>" +
                                         "Matchday %{x}<br>%{y}th<extra></extra>",
                                         hoverinfo=('x+y'),
                                         ))
            else:
                # Save index the input teams is found for plotting the final line
                team_idx = idx
        # Add this as teams name last to have this line on top
        fig.add_trace(go.Scatter(x=x,
                                 y=ys[team_idx],
                                 name=team_names[team_idx],
                                 mode='lines',
                                 line=dict(color=self.team_colours[team_names[team_idx]],
                                           width=4),
                                 showlegend=False,
                                 hovertemplate=f"<b>{team_names[team_idx]}</b><br>" +
                                 "Matchday %{x}<br>%{y}th<extra></extra>",
                                 hoverinfo=('x+y'),
                                 ))

        # Add background yellow zone for star teams zone
        fig.add_shape(type="rect",
                      x0=x[0],
                      y0=4,
                      x1=x[-1],
                      y1=1,
                      line=dict(
                          width=0,
                      ),
                      fillcolor="#03AC13",
                      opacity=0.3,
                      layer="below",
                      )
        fig.add_shape(type="rect",
                      x0=x[0],
                      y0=6,
                      x1=x[-1],
                      y1=4,
                      line=dict(
                          width=0,
                      ),
                      fillcolor="#008080",
                      opacity=0.3,
                      layer="below",
                      )
        fig.add_shape(type="rect",
                      x0=x[0],
                      y0=20,
                      x1=x[-1],
                      y1=17,
                      line=dict(
                          width=0,
                      ),
                      fillcolor="#800000",
                      opacity=0.3,
                      layer="below",
                      )

        positional_values = [i for i in range(1, 21)]

        fig.update_layout(
            yaxis=dict(
                title_text="League Position",
                ticktext=positional_values,
                tickvals=positional_values,
                autorange="reversed",
                showgrid=False,
                showline=False,
                zeroline=False,
            ),
            xaxis=dict(
                title_text="Matchday",
                linecolor="black",
                tickmode="array",
                dtick=1,
                ticktext=matchday_labels,
                tickvals=x,
                showgrid=False,
                showline=False,
            ),
            margin=dict(
                l=50,
                r=50,
                b=10,
                t=10,
                pad=4
            ),
            plot_bgcolor='#fafafa',
            paper_bgcolor='#fafafa',
        )
        
        return fig

    def position_over_time_data_points(self, position_over_time: PositionOverTime) -> tuple[list[datetime], list[str], list[list[int]]]:
        x_cols = position_over_time.df.iloc[:, position_over_time.df.columns.get_level_values(1) == 'Date']
        y_cols = position_over_time.df.iloc[:, position_over_time.df.columns.get_level_values(1) == 'Position']

        # All ys have the same x date values
        x = []
        for _, col_data in x_cols.iteritems():
            # Take the median date for that matchday
            median_date = np.median(col_data.values.tolist())
            # Convert from numpy date to datetime format
            x.append(datetime.utcfromtimestamp(median_date/1e9))

        ys = []
        for _, row_data in y_cols.iterrows():
            y = row_data.values.tolist()
            ys.append(y)

        # Sort the x-axis data by date to remove errors due to match rescheduling
        matchday_labels = sorted(
            list(position_over_time.df.columns.unique(level=0)))

        x, matchday_labels, *ys = zip(*sorted(zip(x, matchday_labels, *ys)))

        return x, matchday_labels, ys

    @timebudget
    def update_position_over_time(self, position_over_time: PositionOverTime, team_name: str = '', display: bool = False):
        if position_over_time.df.empty:
            print(
                "Error: Cannot generate position over time graph; position over time dataframe is empty")
        else:
            if not team_name:
                print("📊 Updating all teams positions over time graphs...")
                teams_to_update = position_over_time.df.index.values.tolist()
            else:
                print(f"📊 Updating {team_name} positions over time graph...")
                teams_to_update = [team_name]

            x, matchday_labels, ys = self.position_over_time_data_points(
                position_over_time)
            team_names = position_over_time.df.index.values.tolist()

            # Create a fig for each team
            for team in teams_to_update:
                fig = self.create_position_over_time_fig(
                    x, ys, matchday_labels, team, team_names)

                if display:
                    fig.show()

                self.save_fig(fig, team, 'position-over-time')

    # -------------------- GOALS SCORED AND CONCEDED GRAPHS --------------------

    def create_clean_sheets_fig(self, x: list[datetime], line: list[float], clean_sheets: list[Optional[float]], not_clean_sheets, matchday_labels: list[str], labels: list[str]) -> FigureWidget:
        # Plot graph
        fig = go.Figure(data=[
            go.Scatter(name='Line', 
                       x=x, 
                       y=line, 
                       mode='lines',
                       line=dict(color='#757575', width=2),
                       showlegend=False),
            go.Scatter(name='Clean Sheet', x=x, y=clean_sheets,
                       mode='markers',
                       connectgaps=True,
                       marker_color='#77DD77',
                       marker_line_color='#006400',
                       marker_line_width=1,
                       text=labels,
                       hoverinfo=('text'),
                       marker=dict(size=32),
                       showlegend=False),
            go.Scatter(name='Goals Conceded', 
                       x=x, 
                       y=not_clean_sheets,
                       mode='markers',
                       connectgaps=True,
                       marker_color='#C23B22',
                       marker_line_color='#8B0000',
                       marker_line_width=1,
                       text=labels,
                       hoverinfo=('text'),
                       marker=dict(size=10),
                       showlegend=False),
        ])

        # Ensure x axis is the same as goals scored and conceeded by adding
        # a small margin to the axis
        scale = 0.011
        margin = (x[-1] - x[0]) * scale

        # Config graph layout
        fig.update_layout(
            yaxis=dict(
                autorange=False,
                range=[0, 1],
                showgrid=False,
                showline=False,
                visible=False,
            ),
            xaxis=dict(
                title_text="Matchday",
                tickmode="array",
                ticktext=[str(i) for i in matchday_labels],
                tickvals=x,
                range=[x[0] - margin, x[-1] + margin],
                showgrid=False,
                showline=False,
                visible=False
            ),
            margin=dict(
                l=50,
                r=50,
                b=10,
                t=10,
                pad=4
            ),
            plot_bgcolor='#fafafa',
            paper_bgcolor='#fafafa',
        )
        
        return fig

    def clean_sheets_data_points(self, y_goals_conceded: list[int]) -> tuple[list[float], list[Optional[float]], list[Optional[float]], list[str]]:
        y_value = 0.5  # Line in the centre of the graph
        not_clean_sheets = [y_value if goals !=
                            0 else None for goals in y_goals_conceded]
        clean_sheets = [y_value if goals == 0 else None for goals in y_goals_conceded]
        labels = ['Clean sheet' if goals ==
                  0 else 'Goals conceded' for goals in y_goals_conceded]
        line = [y_value] * len(clean_sheets)

        return line, clean_sheets, not_clean_sheets, labels

    def create_goals_scored_and_conceded_fig(self, x: list[datetime], y_goals_scored: list[int], y_goals_conceded: list[int], y_avg: list[float], matchday_labels: list[str]) -> FigureWidget:
        # Plot graph
        fig = go.Figure(data=[
            go.Bar(name='Goals Scored', x=x, y=y_goals_scored,
                   marker_color='#77DD77',
                   marker_line_color='#006400',
                   marker_line_width=2,
                   hovertemplate="Matchday %{x}<br>%{y} goals scored<extra></extra>",
                   hoverinfo=('x+y')),
            go.Bar(name='Goals Conceded', x=x, y=y_goals_conceded,
                   marker_color='#C23B22',
                   marker_line_color='#8B0000',
                   marker_line_width=2,
                   hovertemplate="Matchday %{x}<br>%{y} goals conceded<extra></extra>",
                   hoverinfo=('x+y')),
            go.Scatter(name='Avg', x=x, y=y_avg, mode='lines',
                       hovertemplate="Matchday %{x}<br>%{y} goals scored on average<extra></extra>",
                       line=dict(color='#0080FF', width=2))
        ])

        # Get the maximum y-axis value (6 goals unless a higher value found)
        max_y = max([max(y_goals_scored), max(y_goals_conceded)])
        if max_y < 6:
            max_y = 6

        # Config graph layout
        fig.update_layout(
            barmode='group',
            yaxis=dict(
                title_text="Goals",
                autorange=False,
                range=[0, max_y],
                showgrid=False,
                showline=False,
                zeroline=False,
                dtick=1,
            ),
            xaxis=dict(
                title_text="Matchday",
                tickmode="array",
                ticktext=matchday_labels,
                tickvals=x,
                showgrid=False,
                showline=False,
            ),
            margin=dict(
                l=50,
                r=50,
                b=10,
                t=10,
                pad=4
            ),
            plot_bgcolor='#fafafa',
            paper_bgcolor='#fafafa',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
        )
        fig.update_layout(barmode='group')

        return fig

    def goals_scored_and_conceeded_data_points(self, position_over_time: PositionOverTime, team_name: str) -> tuple[list[datetime], list[int], list[int], list[float], list[str]]:
        x_cols = position_over_time.df.iloc[:, position_over_time.df.columns.get_level_values(
            1) == 'Date']
        # All ys have the same x date values
        x = [datetime.utcfromtimestamp(date/1e9)
             for date in x_cols.loc[team_name].values.tolist()]

        # Create chart y values (2 bar charts, and the average line)
        y_goals_scored = []  # type: list[int]
        y_goals_conceded = []  # type: list[int]
        y_avg = []  # type: list[float]
        team_position_over_time = position_over_time.df.loc[team_name]

        matchday_nos = sorted(
            list(position_over_time.df.columns.unique(level=0)))

        # List of matchday strings that have had all games play
        for idx, matchday_no in enumerate(matchday_nos):
            # Append the teams number of goals scored and cocneded this matchday
            team_matchday = team_position_over_time[matchday_no]
            # If match has been played
            if type(team_matchday['Score']) is str:
                # Append the average goals for this matchday to average goals list
                matchday_scorelines = position_over_time.df[matchday_no]['Score']
                goals_scored = []
                for scoreline in matchday_scorelines.values.tolist():
                    if type(scoreline) is str:
                        home, _, away = scoreline.split(' ')
                        goals_scored.extend([int(home), int(away)])
                # Append the mean goals scored (equal to mean goals conceded) this gameweek
                y_avg.append(sum(goals_scored) / len(goals_scored))

                home, _, away = team_matchday['Score'].split(' ')
                no_goals_scored, no_goals_conceded = 0, 0
                if team_matchday['HomeAway'] == 'Home':
                    no_goals_scored = int(home)
                    no_goals_conceded = int(away)
                elif team_matchday['HomeAway'] == 'Away':
                    no_goals_scored = int(away)
                    no_goals_conceded = int(home)
                y_goals_scored.append(no_goals_scored)
                y_goals_conceded.append(no_goals_conceded)
            else:
                # Do not add goals scored, goals condeded or average goals graph points
                # Remove elements from other lists to ensure all lists will be same length
                del x[idx]
                del matchday_nos[idx]

        if x != [] and y_goals_scored != [] and y_goals_conceded != [] and y_avg != []:
            x, y_goals_scored, y_goals_conceded, y_avg = map(list, zip(*sorted(zip(x, y_goals_scored, y_goals_conceded, y_avg))))

        matchday_labels = list(map(str, matchday_nos))

        return x, y_goals_scored, y_goals_conceded, y_avg, matchday_labels

    @timebudget
    def update_goals_scored_and_conceded(self, position_over_time: PositionOverTime, team_name: str = '', display: bool = False):
        if position_over_time.df.empty:
            print(
                "Error: Cannot generate goals scored and conceded graph; position over time dataframe is empty")
        else:
            if not team_name:
                print(
                    "📊 Updating all teams goals scored and conceded over time graphs...")
                teams_to_update = position_over_time.df.index.values.tolist()
            else:
                print(
                    f"📊 Updating {team_name} goals scored and conceded over time graph...")
                teams_to_update = [team_name]

            for team in teams_to_update:
                x, y_goals_scored, y_goals_conceded, y_avg, matchday_labels = self.goals_scored_and_conceeded_data_points(position_over_time, team)
                if y_goals_scored != [] and y_goals_conceded != []:
                    fig = self.create_goals_scored_and_conceded_fig(x, y_goals_scored, y_goals_conceded, y_avg, matchday_labels)

                    if display:
                        fig.show()

                    self.save_fig(fig, team, 'goals-scored-and-conceded')

                # EXTRA GRAPH FROM SAME DATA: CLEAN SHEETS
                line, clean_sheets, not_clean_sheets, labels = self.clean_sheets_data_points(y_goals_conceded)
                if x != []:
                    fig = self.create_clean_sheets_fig(x, line, clean_sheets, not_clean_sheets, matchday_labels, labels)

                    if display:
                        fig.show()

                    self.save_fig(fig, team_name, 'clean-sheets')

    def update_all(self, fixtures: Fixtures, team_ratings: TeamRatings, home_advantages: HomeAdvantages, form: Form, position_over_time: PositionOverTime, team_name: str = '', display_graphs: bool = False):
        self.update_fixtures(fixtures, 
                             team_ratings, 
                             home_advantages,
                             display=display_graphs, 
                             team_name=team_name)
        self.update_form_over_time(form, 
                                   display=display_graphs, 
                                   team_name=team_name)
        self.update_position_over_time(position_over_time, 
                                       display=display_graphs, 
                                       team_name=team_name)
        self.update_goals_scored_and_conceded(position_over_time, 
                                              display=display_graphs, 
                                              team_name=team_name)
