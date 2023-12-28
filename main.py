# Import des bibliothèques nécessaires
import dash
from dash import dcc
from dash import html
from dash import dash_table
import io
from geopy.geocoders import Nominatim
from dash.dependencies import Input, Output
import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Fonction pour récupérer et stocker les coordonnées GPS de tous les pays dans un fichier CSV


def recup_contry(url, name_csv):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    df = pd.read_html(str(table))
    df = pd.DataFrame(df[0])
    df.to_csv(name_csv, index=False)


# Lien contenant les informations sur les pays
# Appel de la fonction pour récupérer les coordonnées des pays et les stocker dans un fichier CSV
# Lecture du fichier CSV contenant les coordonnées des pays
info_pays = 'https://developers.google.com/public-data/docs/canonical/countries_csv'
recup_contry(info_pays, "./data/country_coord.csv")
df = pd.read_csv("./data/country_coord.csv")
selected_columns = ['name', 'latitude', 'longitude']
df_selected = df[selected_columns]

# url_classement = 'https://rsf.org/sites/default/files/import_classement/2023.csv'
# Lecture du fichier CSV contenant le classement global des pays selon plusieurs critères pour 2023
df_classement = pd.read_csv(
    "./data/country_rsf_global_score_2023.csv", delimiter=';', decimal=',')
selected_columns_classement = [
    'ISO', 'Country_FR', 'Country_EN', 'Score', 'Rank', 'Political Context', 'Rank_Pol',
    'Economic Context', 'Rank_Eco', 'Legal Context', 'Rank_Leg', 'Social Context', 'Rank_Soc', 'Safety', 'Rank_Saf']
df_selected_cla = df_classement[selected_columns_classement]

# Colonnes par défaut
default_columns = ['Country_EN', 'Score', 'Rank']
data_table = df_selected_cla[default_columns].to_dict('records')

# Options pour la liste déroulante
dropdown_options = [
    {'label': 'Score global', 'value': 'Score'},
    {'label': 'Indicateur politique', 'value': 'Political Context'},
    {'label': 'Indicateur économique', 'value': 'Economic Context'},
    {'label': 'Indicateur législatif', 'value': 'Legal Context'},
    {'label': 'Indicateur social', 'value': 'Social Context'},
    {'label': 'Indicateur sécurité', 'value': 'Safety'},
]

# Fusion des DataFrames contenant les coordonnées et le classement
merged_df = pd.merge(df_selected, df_selected_cla,
                     how='inner', left_on='name', right_on='Country_EN')

# Initialisation de l'application Dash
app = dash.Dash(__name__)

# Callback pour mettre à jour la carte du monde en fonction de la sélection


@app.callback(
    Output('world-map', 'figure'),
    Input('world-map', 'clickData'),
    Input('map-dropdown', 'value')
)
def update_geos(clickData, selected_variable):
    # Échelles de couleurs pour chaque variable
    color_scale = {
        'Score': ['black', 'red', 'orange', 'yellow', 'green'],
        'Political Context': ['black', 'red', 'orange', 'yellow', 'green'],
        'Economic Context': ['black', 'red', 'orange', 'yellow', 'green'],
        'Legal Context': ['black', 'red', 'orange', 'yellow', 'green'],
        'Social Context': ['black', 'red', 'orange', 'yellow', 'green'],
        'Safety': ['black', 'red', 'orange', 'yellow', 'green']
    }
    # Titres pour chaque variable
    title_map = {
        'Score': 'Carte du monde avec score global par pays',
        'Political Context': 'Carte du monde avec indicateur politique par pays',
        'Economic Context': 'Carte du monde avec indicateur économique par pays',
        'Legal Context': 'Carte du monde avec indicateur législatif par pays',
        'Social Context': 'Carte du monde avec indicateur social par pays',
        'Safety': 'Carte du monde avec indicateur sécurité par pays'
    }
    # Création de la carte
    fig = px.choropleth(merged_df,
                        locations='ISO',
                        color=selected_variable,
                        hover_name='Country_EN',
                        hover_data={'ISO': False, 'Country_FR': False, 'Country_EN': False,
                                    selected_variable: True, 'Rank': True, 'Political Context': True, 'Rank_Pol': True, 'Economic Context': True,
                                    'Rank_Eco': True, 'Legal Context': True, 'Rank_Leg': True, 'Social Context': True, 'Rank_Soc': True,
                                    'Safety': True, 'Rank_Saf': True, 'latitude': False, 'longitude': False},
                        title=title_map[selected_variable],
                        projection='natural earth',
                        color_continuous_scale=color_scale[selected_variable],
                        scope='world',
                        width=1200,
                        height=700,
                        )

    # Gestion du zoom si un pays est sélectionné
    if clickData is None:
        return fig

    country_iso = clickData['points'][0]['location']
    selected_country = merged_df[merged_df['ISO'] == country_iso]
    country_lat = selected_country['latitude'].values[0]
    country_lon = selected_country['longitude'].values[0]

    fig_zoom = go.Figure(fig)

    fig_zoom.update_geos(
        center={'lon': country_lon, 'lat': country_lat},
        projection_scale=5
    )

    return fig_zoom


# Géolocalisation
geolocator = Nominatim(user_agent="geo")

# Callback pour mettre à jour les informations sur le pays sélectionné


@app.callback(
    Output('country-info', 'children'),
    Input('world-map', 'clickData'),
    Input('map-dropdown', 'value'))
def update_country_info(clickData, selected_variable):
    if clickData is None:
        return "Cliquez sur un pays pour voir plus d'informations."
    else:
        country_iso = clickData['points'][0]['location']
        country_row = df_selected_cla[df_selected_cla['ISO'] == country_iso]
        country_name = country_row['Country_FR'].values[0]
        commun_style = {"margin-left": "10px"}
        border_style = {
            'border': 'solid grey',
            'borderRadius': '10px',
            'boxShadow': '2px 2px 4px 0 rgba(0,0,0,0.5)',
            'padding-bottom': '10px'}

        # Affichage des informations en fonction de la variable sélectionnée
        if selected_variable == 'Score':
            country_score = country_row['Score'].values[0]
            country_rank = country_row['Rank'].values[0]
            return html.Div([
                html.P(
                    f"Vous avez sélectionné {country_name}.", style=commun_style),
                html.P(
                    f"Son score global est {country_score}.", style=commun_style),
                html.P(f"Rang : {country_rank}.", style=commun_style)
            ], style=border_style)
        elif selected_variable == 'Political Context':
            country_political = country_row['Political Context'].values[0]
            country_rank_pol = country_row['Rank_Pol'].values[0]
            return html.Div([
                html.P(
                    f"Vous avez sélectionné {country_name}.", style=commun_style),
                html.P(
                    f"Son indicateur politique est {country_political}.", style=commun_style),
                html.P(f"Rang : {country_rank_pol}.", style=commun_style)
            ], style=border_style)
        elif selected_variable == 'Economic Context':
            country_economical = country_row['Economic Context'].values[0]
            country_rank_eco = country_row['Rank_Eco'].values[0]
            return html.Div([
                html.P(
                    f"Vous avez sélectionné {country_name}.", style=commun_style),
                html.P(
                    f"Son indicateur économique est {country_economical}.", style=commun_style),
                html.P(f"Rang : {country_rank_eco}.", style=commun_style)
            ], style=border_style)
        elif selected_variable == 'Legal Context':
            country_legal = country_row['Legal Context'].values[0]
            country_rank_leg = country_row['Rank_Leg'].values[0]
            return html.Div([
                html.P(
                    f"Vous avez sélectionné {country_name}.", style=commun_style),
                html.P(
                    f"Son indicateur législatif est de {country_legal}.", style=commun_style),
                html.P(f"Rang : {country_rank_leg}.", style=commun_style)
            ], style=border_style)
        elif selected_variable == 'Social Context':
            country_social = country_row['Social Context'].values[0]
            country_rank_soc = country_row['Rank_Soc'].values[0]
            return html.Div([
                html.P(
                    f"Vous avez sélectionné {country_name}.", style=commun_style),
                html.P(
                    f"Son indicateur social est de {country_social}.", style=commun_style),
                html.P(f"Rang : {country_rank_soc}.", style=commun_style)
            ], style=border_style)
        elif selected_variable == 'Safety':
            country_safety = country_row['Safety'].values[0]
            country_rank_saf = country_row['Rank_Saf'].values[0]
            return html.Div([
                html.P(
                    f"Vous avez sélectionné {country_name}.", style=commun_style),
                html.P(
                    f"Son indicateur de sécurité est de {country_safety}.", style=commun_style),
                html.P(f"Rang : {country_rank_saf}.", style=commun_style)
            ], style=border_style)

# Callback pour mettre à jour la géolocalisation en temps réel


@app.callback(Output("geolocation", "update_now"), Input("update_btn", "n_clicks"))
def update_now(click):
    return True if click and click > 0 else False

# Callback pour afficher les informations de géolocalisation


@app.callback(
    Output("text_position", "children"),
    Input("geolocation", "position"),
)
def display_output(pos):
    if pos:
        location = geolocator.reverse((pos['lat'], pos['lon']), language='en')
        country_name = location.raw['address'].get('country', '')
        return html.P(
            f"Vous êtes localiser  en {country_name} (latitude {pos['lat']}, longitude {pos['lon']}).",
        )
    return "Veuillez autoriser la localisation"


# Configuration de l'application
if __name__ == '__main__':

    # Ajout du style CSS
    app.css.append_css({
        'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
    })

    # Mise en page de l'application
    app.layout = html.Div([
        html.H1("Classement global 2023 par pays selon indicateurs politique, économique, législatif, social et de sécurité pour la presse"
                " (Reporters Sans Frontières (RFS))"),
        dash_table.DataTable(
            id='table-classement',
            columns=[
                {"id": "ISO", "name": "ISO", "hideable": False},
                {"id": "Country_EN", "name": "Nom", "hideable": False},
                {"id": "Score", "name": "Score Global",
                 "hideable": False},
                {"id": "Rank", "name": "Rang Global", "hideable": False},
                {"id": "Political Context",
                    "name": "Indicateur politique", "hideable": True},
                {"id": "Rank_Pol", "name": "Rang politique", "hideable": True},
                {"id": "Economic Context",
                    "name": "Indicateur économique", "hideable": True},
                {"id": "Rank_Eco", "name": "Rang economique", "hideable": True},
                {"id": "Legal Context", "name": "Indicateur législatif", "hideable": True},
                {"id": "Rank_Leg", "name": "Rang législatif", "hideable": True},
                {"id": "Social Context", "name": "Indicateur sociale", "hideable": True},
                {"id": "Rank_Soc", "name": "Rang sociale", "hideable": True},
                {"id": "Safety", "name": "Securite", "hideable": True},
                {"id": "Rank_Saf", "name": "Indicateur sécurité", "hideable": True}
            ],
            sort_action='native',
            page_action='native',
            page_current=0,
            page_size=15,
            style_cell={'textAlign': 'left'},
            hidden_columns=['Political Context', 'Rank_Pol', 'Economic Context', 'Rank_Eco',
                            'Legal Context', 'Rank_Leg', 'Social Context', 'Rank_Soc', 'Safety', 'Rank_Saf'],
            data=df_selected_cla.to_dict('records'),
        ),
        html.Button("Géolocalisation", id="update_btn"),
        dcc.Geolocation(id="geolocation"),
        html.Div(id="text_position"),
        dcc.Dropdown(
            id='map-dropdown',
            options=dropdown_options,
            value='Score',  # Valeur par défaut
            multi=False  # Permettre la sélection unique
        ),
        html.H1("Carte du monde avec les coordonnées GPS des pays"),
        dcc.Graph(
            id='world-map',
            # figure=fig,
        ),
        html.Div(id='country-info')
    ], style={'marginRight': 150})

    app.run_server(debug=True)
