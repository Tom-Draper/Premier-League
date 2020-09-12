import plotly
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime 

class GenDataVis:
    def genFixturesGraph(self, team_name, fixtures, team_ratings, home_advantage):
        team_fixtures = fixtures.loc[team_name]  # Get row of fixtures dataframe
            
        now = datetime.now()
        sizes = [15] * len(fixtures)
        x, y, teams = [], [], []
        for i, match in enumerate(team_fixtures):
            x.append(match['Date'])
            # Get rating of the opposition team
            rating = team_ratings.loc[match['Team'], 'Total Rating']
            # Decrease other team's rating if you're playing at home
            if match['HomeAway'] == 'Home':
                rating *= (1 - home_advantage)
            y.append(rating)
            teams.append(match['Team'] + " (" + match['HomeAway'] + ")")
            

            
            # Increase size of point marker if it's the current upcoming match
            # now = datetime(2020, 11, 6)
            # now = datetime(2021, 5, 23)
            if i == 0:
                if now < match['Date']:
                    sizes[i] = 30
            elif i != len(team_fixtures) and x[-2] < now < match['Date']:
                sizes[i] = 30
            
        y = list(map(lambda x : x*100, y))  # Convert to percentages
        df = pd.DataFrame({'Date': x, 'Ratings': y, 'Teams': teams})
        
        # fig = px.line(df, x="Date", y="Match", color='country')
        colour_scale = ['#01c626', '#08a825',  '#0b7c20', '#0a661b', '#064411', '#000000', '#85160f', '#5b1d15', '#ad1a10', '#db1a0d', '#fc1303']
        fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines+markers', 
                                        marker=dict(size=sizes,
                                                    color=y,
                                                    colorscale=colour_scale),
                                        line=dict(color='#737373'),
                                        text=teams,
                                        hovertemplate="<b>%{text}</b> <br>%{x|%d %B, %Y}<br>Rating: %{y:.2f}%<extra></extra>",
                                        hoverinfo=('x+y+text'),
                                        ))

        fig.add_shape(go.layout.Shape(type="line",
                                      yref="paper",
                                      xref="x",
                                      x0=now,
                                      y0=0.04,
                                      x1=now,
                                      y1=1.01,
                                      #line=dict(color="RoyalBlue", width=3),),
                                      line=dict(color="black", 
                                                width=1,
                                                dash="dot")))
        
        # fig = px.scatter(df, x='Date', y='Ratings', labels={'x':'Date', 'y':'Team Rating'},
        #                   color=y, color_continuous_scale=colour_scale, 
        #                   hover_name=teams)
        # fig = px.line(x=x, y=y)
        
        # Annotations
        # annotations = []
        # Title
        # annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.03,
        #                       xanchor='left', yanchor='bottom',
        #                       text=f'{team_name} Fixtures',
        #                       font=dict(family='Arial',
        #                                 size=32,
        #                                 color='rgb(37,37,37)'),
        #                       showarrow=False))
        
        
        # fig.update_layout(annotations=annotations)
        # fig.update_layout({
        #     'plot_bgcolor': '#fafafa',
        #     'paper_bgcolor': '#fafafa',
        # })
        fig.update_layout(
            yaxis=dict(
                title_text="Team Rating %",
                ticktext=[str(i) + "%" for i in range(0, 101, 10)],
                tickvals=[i for i in range(0, 101, 10)],
                gridcolor='gray',
                showline=False,
                # color="black"
                zeroline=False,
            ),
            xaxis=dict(
                title_text="Date",
                linecolor="black",
                showgrid=False,
                showline=False,
            ),
            plot_bgcolor='#fafafa',
            paper_bgcolor='#fafafa',
        )
        
        # fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='gray')
        # fig.update_xaxes(showgrid=False)

        # fig.show()
        # Convert team name into suitable use for filename
        file_team_name = '_'.join(team_name.lower().split()[:-1])
        plotly.offline.plot(fig, filename=f'./templates/graphs/{file_team_name}/fixtures_{file_team_name}.html', auto_open=False)