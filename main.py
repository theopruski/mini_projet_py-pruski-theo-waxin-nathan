import dash
from dash import dcc
from dash import html
from dash import dash_table
import io

from dash.dependencies import Input, Output
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
recup_contry(info_pays, "./data/country_coord.csv")
df = pd.read_csv("./data/country_coord.csv")
selected_columns = ['name', 'latitude', 'longitude']
df_selected = df[selected_columns]

# fig = px.scatter_geo(df_selected, lat='latitude', lon='longitude',
# text='name', projection='natural earth')

# url_classement = 'https://rsf.org/sites/default/files/import_classement/2023.csv'
df_classement = pd.read_csv(
    "./data/country_press_global_score_2023.csv", delimiter=';', decimal=',')
selected_columns_classement = [
    'ISO', 'Country_FR', 'Country_EN', 'Score', 'Rank']
df_selected_cla = df_classement[selected_columns_classement]

merged_df = pd.merge(df_selected, df_selected_cla,
                     how='inner', left_on='name', right_on='Country_EN')

fig = px.choropleth(merged_df,
                    locations='ISO',
                    color='Score',
                    hover_name='Country_EN',
                    hover_data={'ISO': False, 'Country_FR': False, 'Country_EN': False,
                                'Score': True, 'Rank': True, 'latitude': False, 'longitude': False},
                    title='Carte du Monde avec Frontières et Scores de Liberté de la Presse',
                    projection='natural earth',
                    color_continuous_scale=[
                        'black', 'red', 'orange', 'yellow', 'green'],
                    scope='world',
                    width=1200,
                    height=800,
                    )

# info_press = 'https://rsf.org/sites/default/files/import_classement/2023.csv'
# recup_liberte_press(info_press, ".data/country_press.csv")

app = dash.Dash(__name__)


@app.callback(
    Output('country-info', 'children'),
    Input('world-map', 'clickData'))
def update_country_info(clickData):
    if clickData is None:
        return "Cliquez sur un pays pour voir plus d'informations."
    else:
        country_iso = clickData['points'][0]['location']
        country_row = df_selected_cla[df_selected_cla['ISO'] == country_iso]
        country_name = country_row['Country_FR'].values[0]
        country_score = country_row['Score'].values[0]
        country_rank = country_row['Rank'].values[0]
        return f"Vous avez sélectionné {country_name}. Son score de liberté de la presse est {country_score} et son rang est {country_rank}."


if __name__ == '__main__':
    app.css.append_css({
        'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
    })
    app.layout = html.Div([
        html.H1("Classement 2023 de la liberté de la presse"),
        dash_table.DataTable(
            id='table-classement',
            columns=[
                {"name": "Nom", "id": "Country_EN"},
                {"name": "Score", "id": "Score"},
                {"name": "Rang", "id": "Rank"},
            ],
            data=df_selected_cla[['Country_EN',
                                  'Score', 'Rank']].to_dict('records'),
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
        html.Div(id='country-info')
    ], style={'marginRight': 200})

    app.run_server(debug=True)
