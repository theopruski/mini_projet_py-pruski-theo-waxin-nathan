import dash
from dash import dcc
from dash import html
from dash import dash_table
import io

# from dash.dependencies import Input, Output
import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px

# récupére et stocke les coordonnées gps de tous les pays dans un fichier csv


def recup_contry(url, name_csv):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    df = pd.read_html(str(table))
    df = pd.DataFrame(df[0])
    df.to_csv(name_csv, index=False)

# def recup_liberte_press(url, name_csv):
    # response = requests.get(url)
    # soup = BeautifulSoup(response.text, 'html.parser')
    # table_liberte = soup.find('table')
    # df = pd.read_html(str(table_liberte))
    # df.to_csv(name_csv, index=False)


info_pays = 'https://developers.google.com/public-data/docs/canonical/countries_csv'

# fig = px.scatter_geo(df_selected, lat='latitude', lon='longitude',
# text='name', projection='natural earth')

# url_classement = 'https://rsf.org/sites/default/files/import_classement/2023.csv'
df_classement = pd.read_csv(
    "./data/country_press_global_score_2023_fr.csv", delimiter=';', decimal=',')
selected_columns_classement = ['ISO','Country_FR', 'Score', 'Rank']
df_selected_cla = df_classement[selected_columns_classement]
fig = px.choropleth(df_selected_cla,
                    locations='ISO', 
                    color='Score',
                    hover_name='Country_FR',
                    hover_data={'ISO': False, 'Country_FR': False, 'Score': True, 'Rank': True},
                    title='Carte du Monde avec Frontières et Scores de Liberté de la Presse',
                    projection='natural earth',
                    color_continuous_scale=[
                        'purple', 'red', 'orange', 'yellow', 'green'], 
                    scope='world',
                    )

# info_press = 'https://rsf.org/sites/default/files/import_classement/2023.csv'
# recup_liberte_press(info_press, ".data/country_press.csv")

if __name__ == '__main__':
    app = dash.Dash(__name__)
    app.css.append_css({
        'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
    })
    app.layout = html.Div([
        html.H1("Classement 2023 de la liberté de la presse"),
        dash_table.DataTable(
            id='table-classement',
            columns=[
                {"name": "Nom", "id": "Country_FR"}, 
                {"name": "Score", "id": "Score"}, 
                 {"name": "Rang", "id": "Rank"}, 
            ],
            data=df_selected_cla[['Country_FR', 'Score', 'Rank']].to_dict('records'), 
            sort_action='native',
            page_action='native',
            page_current=0, 
            page_size=15,
            style_cell={'textAlign': 'left'},
        ), 
        html.H1("Carte du monde avec les coordonnées GPS des pays"),
        dcc.Graph(
            id='world-map',
            figure=fig,
        ),
    ], style={'marginRight': 200})

    app.run_server(debug=True)
