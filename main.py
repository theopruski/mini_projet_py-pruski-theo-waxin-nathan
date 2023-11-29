import dash
from dash import dcc
from dash import html

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
    # df


info_pays = 'https://developers.google.com/public-data/docs/canonical/countries_csv'
recup_contry(info_pays, "./data/country_coord.csv")
# info_press = 'https://rsf.org/sites/default/files/import_classement/2023.csv'
# recup_liberte_press(info_press, ".data/country_press.csv")

if __name__ == '__main__':
    app = dash.Dash(__name__)

    app.run_server(debug=True)
