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
recup_contry(info_pays, "./data/country_coord.csv")
df = pd.read_csv("./data/country_coord.csv")
selected_columns = ['name', 'latitude', 'longitude']
df_selected = df[selected_columns]
fig = px.choropleth(df_selected,
                    locations='name',  # Utilisez le nom du pays comme identifiant de lieu
                    # Colorez en fonction de la latitude (ajustez en fonction de vos besoins)
                    color='latitude',
                    hover_name='name',  # Affichez le nom du pays au survol
                    title='Carte du Monde avec Frontières et Scores de Liberté de la Presse',
                    projection='natural earth',  # Projection de la carte
                    color_continuous_scale=[
                        'green', 'yellow', 'orange', 'red', 'purple'],
                    )
fig.update_geos(showcountries=True, countrycolor="Black")
fig.add_trace(px.scatter_geo(df_selected, lat='latitude',
              lon='longitude').data[0])
graph_component = dcc.Graph(id='world-map', figure=fig)

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
    app.layout = html.Div([
        html.H1("Tableau des libertés"),
        dash_table.DataTable(
            id='table',
            columns=[{"name": col, "id": col} for col in df_selected.columns],
            data=df_selected.to_dict('records'),
            style_cell_conditional=[
                {'if': {'column_id': 'name'}, 'width': '10%'},
            ],
            style_table={'width': '30%'},
            style_cell={'textAlign': 'left'},
        ),
        html.H1("Carte du monde avec les coordonnées GPS des pays"),
        dcc.Graph(
            id='world-map',
            figure=fig,
        ),

        html.H1("Classement 2023 de la liberté de la presse"),
        dash_table.DataTable(
            id='table-classement',
            columns=[{"name": col, "id": col}
                     for col in df_selected_cla.columns],
            data=df_selected_cla.to_dict('records'),
            style_table={'width': '30%'},
            style_cell={'textAlign': 'left'},
        ),
    ])

    app.run_server(debug=True)
