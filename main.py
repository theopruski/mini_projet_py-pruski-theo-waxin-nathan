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
import dash_bootstrap_components as dbc

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
    {'label': 'Score', 'value': 'Score'},
    {'label': 'Political indicator', 'value': 'Political Context'},
    {'label': 'Economic indicator', 'value': 'Economic Context'},
    {'label': 'Legislative indicator', 'value': 'Legal Context'},
    {'label': 'Social indicator', 'value': 'Social Context'},
    {'label': 'Security indicator', 'value': 'Safety'},
]

# Fusion des DataFrames contenant les coordonnées et le classement
merged_df = pd.merge(df_selected, df_selected_cla,
                     how='inner', left_on='name', right_on='Country_EN')

geolocation_clicked = False

# Initialisation de l'application Dash
app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP]
                )

# Callback pour mettre à jour la carte du monde en fonction de la sélection


@app.callback(
    Output('world-map', 'figure'),
    Input('world-map', 'clickData'),
    Input('map-dropdown', 'value'),
    Input('geolocation', 'position'),
    Input('update_btn', 'n_clicks')
)
def update_geos(clickData, selected_variable, geolocation_position, geolocation_btn_clicks):
    global geolocation_clicked
    # Échelles de couleurs pour chaque variable
    color_scale = {
        'Score': ['black', 'red', 'orange', 'yellow', 'green'],
        'Political Context': ['black', 'MediumSlateBlue', 'MediumTurquoise', 'PaleTurquoise', 'LightCyan'],
        'Economic Context': ['black', 'DarkGreen', 'ForestGreen', 'DarkSeaGreen', 'MediumAquamarine'],
        'Legal Context': ['black', 'Sienna', 'Peru', 'tan', 'Cornsilk'],
        'Social Context': ['black', 'RebeccaPurple', 'MediumOrchid', 'Orchid', 'Lavender'],
        'Safety': ['black', 'Gold', 'Yellow', 'Khaki', 'LightYellow']
    }
    # Titres pour chaque variable
    title_map = {
        'Score': 'World map with global score by country',
        'Political Context': 'World map with political indicators by country',
        'Economic Context': 'World map with economic indicators by country',
        'Legal Context': 'World map with legislative indicators by country',
        'Social Context': 'World map with social indicators by country',
        'Safety': 'World map with safety indicators by country'
    }

    hover_data_mapping = {
        'Score': {'ISO': False, 'Country_FR': False, 'Country_EN': False, 'Score': True, 'Rank': True},
        'Political Context': {'ISO': False, 'Country_FR': False, 'Country_EN': False, 'Political Context': True, 'Rank_Pol': True},
        'Economic Context': {'ISO': False, 'Country_FR': False, 'Country_EN': False, 'Economic Context': True, 'Rank_Eco': True},
        'Legal Context': {'ISO': False, 'Country_FR': False, 'Country_EN': False, 'Legal Context': True, 'Rank_Leg': True},
        'Social Context': {'ISO': False, 'Country_FR': False, 'Country_EN': False, 'Social Context': True, 'Rank_Soc': True},
        'Safety': {'ISO': False, 'Country_FR': False, 'Country_EN': False, 'Safety': True, 'Rank_Saf': True}
    }
    # Création de la carte
    fig = px.choropleth(merged_df,
                        locations='ISO',
                        color=selected_variable,
                        hover_name='Country_EN',
                        hover_data=hover_data_mapping[selected_variable],
                        title=title_map[selected_variable],
                        projection='natural earth',
                        color_continuous_scale=color_scale[selected_variable],
                        scope='world',
                        width=1200,
                        height=650,
                        )

    # Gestion du zoom si un pays est sélectionné ou si la géolocalisation est disponible
    if clickData is not None:
        country_iso = clickData['points'][0]['location']
        selected_country = merged_df[merged_df['ISO'] == country_iso]
        country_lat = selected_country['latitude'].values[0]
        country_lon = selected_country['longitude'].values[0]
    elif geolocation_position is not None and geolocation_btn_clicks:
        country_lat = geolocation_position['lat']
        country_lon = geolocation_position['lon']
        # Réinitialisez la variable d'état après avoir utilisé le clic
        geolocation_clicked = False
    else:
        return fig  # Si aucune information de zoom n'est disponible, retournez simplement la figure sans modification

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
        return html.Div("Click on a country to see more information.",
                        className="mr-3",
                        style={'marginLeft': 100})
    else:
        country_iso = clickData['points'][0]['location']
        country_row = df_selected_cla[df_selected_cla['ISO'] == country_iso]
        country_name = country_row['Country_EN'].values[0]
        commun_style = {"margin-left": "10px"}
        border_style = {
            'border': 'solid grey',
            'borderRadius': '10px',
            'boxShadow': '2px 2px 4px 0 rgba(0,0,0,0.5)',
            'margin-left': '5rem',
            'margin-left': '5rem',
            'margin-bottom:': '5rem',
            'display': 'flex',
            'backgroundColor': '#d5e3ff'}

        # Affichage des informations en fonction de la variable sélectionnée
        if selected_variable == 'Score':
            country_score = country_row['Score'].values[0]
            country_rank = country_row['Rank'].values[0]
            return html.Div([
                html.P(
                    f"You have selected {country_name}.", style=commun_style, className="d-flex pl-5"),
                html.Br(),
                html.P(
                    f"Its score is {country_score}.", style=commun_style),
                html.P(f"Rank : {country_rank}.", style=commun_style)
            ], style={**border_style, })
        elif selected_variable == 'Political Context':
            country_political = country_row['Political Context'].values[0]
            country_rank_pol = country_row['Rank_Pol'].values[0]
            return html.Div([
                html.P(
                    f"You have selected {country_name}.", style=commun_style),
                html.P(
                    f"Its political indicator is {country_political}.", style=commun_style),
                html.P(f"Rank : {country_rank_pol}.", style=commun_style)
            ], style=border_style)
        elif selected_variable == 'Economic Context':
            country_economical = country_row['Economic Context'].values[0]
            country_rank_eco = country_row['Rank_Eco'].values[0]
            return html.Div([
                html.P(
                    f"You have selected {country_name}.", style=commun_style),
                html.P(
                    f"Its economic indicator is {country_economical}.", style=commun_style),
                html.P(f"Rank : {country_rank_eco}.", style=commun_style)
            ], style=border_style)
        elif selected_variable == 'Legal Context':
            country_legal = country_row['Legal Context'].values[0]
            country_rank_leg = country_row['Rank_Leg'].values[0]
            return html.Div([
                html.P(
                    f"You have selected {country_name}.", style=commun_style),
                html.P(
                    f"Its legislative indicator is {country_legal}.", style=commun_style),
                html.P(f"Rank : {country_rank_leg}.", style=commun_style)
            ], style=border_style)
        elif selected_variable == 'Social Context':
            country_social = country_row['Social Context'].values[0]
            country_rank_soc = country_row['Rank_Soc'].values[0]
            return html.Div([
                html.P(
                    f"You have selected {country_name}.", style=commun_style),
                html.P(
                    f"Its social indicator is {country_social}.", style=commun_style),
                html.P(f"Rank : {country_rank_soc}.", style=commun_style)
            ], style=border_style)
        elif selected_variable == 'Safety':
            country_safety = country_row['Safety'].values[0]
            country_rank_saf = country_row['Rank_Saf'].values[0]
            return html.Div([
                html.P(
                    f"You have selected {country_name}.", style=commun_style),
                html.P(
                    f"Its safety indicator is {country_safety}.", style=commun_style),
                html.P(f"Rank : {country_rank_saf}.", style=commun_style)
            ], style={**border_style, **{'margin-top': '10px'}})

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
            f"You are located in {country_name} (latitude {pos['lat']}, longitude {pos['lon']}).",
        )
    return "Please enable localization"


# Configuration de l'application
if __name__ == '__main__':

    # Ajout du style CSS
    app.css.append_css({
        'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
    })

    # Mise en page de l'application
    app.layout = html.Div([
        html.H1("Global ranking 2023 by country according to political, economic, legislative, social and security indicators for the press"
                " (Reporters Without Borders (RWB))", className='text-center', style={'backgroundColor': "#d5e3ff"}),
        html.Div([
            dash_table.DataTable(
                id='table-classement',
                columns=[
                    {"id": "Country_EN", "name": "Name", "hideable": False},
                    {"id": "Score", "name": "Global Score",
                     "hideable": False},
                    {"id": "Rank", "name": "Global Rank", "hideable": False},
                    {"id": "Political Context",
                     "name": "Political indicator", "hideable": True},
                    {"id": "Rank_Pol", "name": "Political rank", "hideable": True},
                    {"id": "Economic Context",
                     "name": "Economic indicator", "hideable": True},
                    {"id": "Rank_Eco", "name": "Economic rank", "hideable": True},
                    {"id": "Legal Context",
                        "name": "Legislative indicator", "hideable": True},
                    {"id": "Rank_Leg", "name": "Legislative rank", "hideable": True},
                    {"id": "Social Context",
                        "name": "Social indicator", "hideable": True},
                    {"id": "Rank_Soc", "name": "Social rank", "hideable": True},
                    {"id": "Safety", "name": "Security", "hideable": True},
                    {"id": "Rank_Saf", "name": "Security indicator", "hideable": True}
                ],
                sort_action='native',
                page_action='native',
                page_current=0,
                page_size=15,
                style_cell={'textAlign': 'left', 'minWidth': '150px',
                            'width': '150px', 'maxWidth': '150px'},
                hidden_columns=['Political Context', 'Rank_Pol', 'Economic Context', 'Rank_Eco',
                                'Legal Context', 'Rank_Leg', 'Social Context', 'Rank_Soc', 'Safety', 'Rank_Saf'],
                data=df_selected_cla.to_dict('records'),
                style_data={
                    'backgroundColor': 'lightblue',  # Exemple de couleur de fond pour les cellules
                    'color': 'black'  # Couleur du texte des cellules
                },
            ),
        ], style={'marginRight': 150}),
        html.H1("World map with country GPS coordinates",
                className='text-center'),
        html.Div([

            dbc.Button("Geolocation", id="update_btn",
                       color="primary", className="mt-3"),
            dcc.Geolocation(id="geolocation"),
            html.Div(id="text_position", className="mt-1"),
            dcc.Dropdown(
                id='map-dropdown',
                options=dropdown_options,
                value='Score',  # Valeur par défaut
                multi=False  # Permettre la sélection unique
            ),
        ],
            style={'border': 'solid grey',
                   'boxShadow': '2px 2px 4px 0 rgba(0,0,0,0.5)',
                   'margin-bottom:': '5rem',
                   'marginLeft': 60,
                   'marginRight': 150,
                   'backgroundColor': '#d5e3ff',
                   'padding': '1rem',
                   'border-radius': '1rem'}),

        dcc.Graph(
            id='world-map',
            # figure=fig,
        ),
        html.Div(id='country-info')
    ])

    app.css.append_css({
        'external_url': 'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'
    })

    app.run_server(debug=True)
