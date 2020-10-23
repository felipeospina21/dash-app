from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import dash
import dash_auth 
import dash_core_components as dcc 
import dash_html_components as html
import plotly.express as px
import plotly.graph_objs as go
import plotly.offline as pyo
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
from datetime import datetime
from get_spredsheet import get_google_sheet, gsheet2df
from credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
MAPBOX_API_TOKEN = Credentials.MAPBOX_API_TOKEN

id_me2n = '1HUxbZV0dYAytXzG9zUFmpLkfLliSTK18QLiVCHU3zEY'
range_me2n = 'Sheet1'
id_entregas = '1qArjrPF4eifdYpHKB7eiq0-9o4VLDlQUimuEsj75Yz0'
range_entregas = 'entregas'
id_correos = '1Vw7KVh0UmaGWyuqkWpI5z5Ij9E_Z6uoKkgVoAlAn2Ic'
range_correos = 'correos'
id_tasa_cambio = '1QzJsSH9pY5SIKbmAiUwaLLWC8cz6EBMO7sOXAvYqHOY'
range_tasa_cambio = 'Hoja1'
id_clase_doc = '1GewcBjxUi_H6tngR-sBscyh8QM7vQDZsWne2CA4LRFo'
range_clase_doc = 'Hoja1'
id_tasa_serv = '1faeXHDD6omq9YmbBW1f2clF5r9PVNdcFSGAQjttzE2s'
range_tasa_serv = 'Hoja1'
id_grup_art = '18iXurXuZSPEwIzkCDCnb9W3f4SUpcFVgpCIPmX5koxs'
range_grup_art ='Hoja1'

me2nValues = get_google_sheet(id_me2n, range_me2n)
entregasValues = get_google_sheet(id_entregas, range_entregas)
correosValues = get_google_sheet(id_correos, range_correos)
cambioValues = get_google_sheet(id_tasa_cambio, range_tasa_cambio)
claseDocValues = get_google_sheet(id_clase_doc, range_clase_doc)
tasaServValues = get_google_sheet(id_tasa_serv, range_tasa_serv)
grupArtValues = get_google_sheet(id_grup_art, range_grup_art)

df = gsheet2df(me2nValues)
df['Precio neto'] = pd.to_numeric(df['Precio neto'], errors='raise')
df['Valor neto de pedido'] = pd.to_numeric(df['Valor neto de pedido'], errors='raise')
df['Fecha documento'] = pd.to_datetime(df['Fecha documento'], errors='raise')
df_ent = gsheet2df(entregasValues)
df_ent['Precio Unitario'] = pd.to_numeric(df_ent['Precio Unitario'], errors='raise')
df_ent['Subtotal'] = pd.to_numeric(df_ent['Subtotal'], errors='raise')
df_ent['Fecha Contabilidad MIGO'] = pd.to_datetime(df_ent['Fecha Contabilidad MIGO'], errors='raise')
df_tasa = gsheet2df(cambioValues)
df_tasa.set_index("divisa", inplace = True)
df_tasa['cambio'] = pd.to_numeric(df_tasa['cambio'], errors='raise')
tipo_proveedor = gsheet2df(correosValues)
tipo_proveedor.set_index("CODIGO SAP", inplace = True)
tasa_serv = gsheet2df(tasaServValues)
tasa_serv['entregas_a_tiempo'] = pd.to_numeric(tasa_serv['entregas_a_tiempo'], errors='raise')
tasa_serv['entregas_totales'] = pd.to_numeric(tasa_serv['entregas_totales'], errors='raise')
tasa_serv['tasa_servicio'] = tasa_serv['entregas_a_tiempo'] / tasa_serv['entregas_totales']
clases_doc = gsheet2df(claseDocValues)
clases_doc.set_index("Clase doc", inplace = True)
grupos_articulos = gsheet2df(grupArtValues)
grupos_articulos.set_index("Grupo de artículos", inplace = True)

# Filter Compras
df = df[df['Indicador de borrado'] != 'L']
df['Year']=df['Fecha documento'].dt.year
df['Month']=df['Fecha documento'].dt.year
df['total_cop'] = pd.Series(df['Valor neto de pedido'], df.index)
df['total_cop'] = np.where(df['Moneda'] == 'USD', df['total_cop'] * df_tasa['cambio'].loc['USD'], df['total_cop'])
df['total_cop'] = np.where(df['Moneda'] == 'EUR', df['total_cop'] * df_tasa['cambio'].loc['EUR'], df['total_cop'])
df['total_cop'] = np.where(df['Moneda'] == 'AUD', df['total_cop'] * df_tasa['cambio'].loc['AUD'], df['total_cop'])
df['total_cop'] = np.where(df['Moneda'] == 'CAD', df['total_cop'] * df_tasa['cambio'].loc['CAD'], df['total_cop'])
df[['CODIGO SAP','NOMBRE PROVEEDOR']] = df['Proveedor/Centro suministrador'].str.split(' ', 1, expand=True)
df = pd.merge(tipo_proveedor['TIPO'], df, on='CODIGO SAP')
df = pd.merge(grupos_articulos['descripcion_ga'], df, on='Grupo de artículos')
grupos_articulos.sort_values(by='descripcion_ga', ascending=True, inplace=True)

# Filter Entregas
df_ent['Fecha Contabilidad MIGO']= pd.to_datetime(df_ent['Fecha Contabilidad MIGO'], yearfirst=True)
df_ent = df_ent[df_ent['Fecha Contabilidad MIGO'] >= '2019-01-01']
df_ent['Numero Material'] = df_ent['Numero Material'].astype(str)
df_ent['tipo_entrega'] = df_ent['Numero Material'].str.extract(r'([1-9])', expand=True)
df_ent['total_cop'] = pd.Series(df_ent['Subtotal'], df_ent.index)
df_ent['total_cop'] = np.where(df_ent['Moneda'] == 'USD', df_ent['total_cop'] * df_tasa['cambio'].loc['USD'], df_ent['total_cop'])
df_ent['total_cop'] = np.where(df_ent['Moneda'] == 'EUR', df_ent['total_cop'] * df_tasa['cambio'].loc['EUR'], df_ent['total_cop'])
df_ent['total_cop'] = np.where(df_ent['Moneda'] == 'AUD', df_ent['total_cop'] * df_tasa['cambio'].loc['AUD'], df_ent['total_cop'])
df_ent['total_cop'] = np.where(df_ent['Moneda'] == 'CAD', df_ent['total_cop'] * df_tasa['cambio'].loc['CAD'], df_ent['total_cop'])
df_ent['precio_unit_cop'] = pd.Series(df_ent['Precio Unitario'], df_ent.index)
df_ent['precio_unit_cop'] = np.where(df_ent['Moneda'] == 'USD', df_ent['precio_unit_cop'] * df_tasa['cambio'].loc['USD'], df_ent['precio_unit_cop'])
df_ent['precio_unit_cop'] = np.where(df_ent['Moneda'] == 'EUR', df_ent['precio_unit_cop'] * df_tasa['cambio'].loc['EUR'], df_ent['precio_unit_cop'])
df_ent['precio_unit_cop'] = np.where(df_ent['Moneda'] == 'AUD', df_ent['precio_unit_cop'] * df_tasa['cambio'].loc['AUD'], df_ent['precio_unit_cop'])
df_ent['precio_unit_cop'] = np.where(df_ent['Moneda'] == 'CAD', df_ent['precio_unit_cop'] * df_tasa['cambio'].loc['CAD'], df_ent['precio_unit_cop'])

# Variables
lista_gc_mat = []
lista_gc_serv = []
lista_grupo_art_mat = []
lista_grupo_art_serv = []
lista_sociedades = []
lista_clases_doc = []
lista_tipo_compra = []
users=[]
# for organizacion in sociedades.index:
#     lista_sociedades.append(organizacion)

for clase in clases_doc.index:
    lista_clases_doc.append(clase)

lista_grupo_art = sorted(list(df['descripcion_ga'].unique()))
curr_year = datetime.now().year
last_month = datetime.now().month - 3

# external CSS stylesheets
# external_stylesheets = [
#     'https://codepen.io/chriddyp/pen/bWLwgP.css',
#     {
#         'href': 'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css',
#         'rel': 'stylesheet',
#         'integrity': 'sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO',
#         'crossorigin': 'anonymous'
#     }
# ]

with open('data/users.txt', 'r') as f:
    lista = [line.strip() for line in f]
for element in lista:
    a,b = element.split()
    a = a.replace(',', '')
    users.append([a,b])

app = dash.Dash(__name__) #, external_stylesheets=external_stylesheets)
auth = dash_auth.BasicAuth(app, users)
server = app.server

app.layout = html.Div([
    html.Header([
        html.Div(
            html.Img(
                id='Logo',
                src='/assets/Logo-Mineros-2018.png',
                style={'width':'100%','display':'inline-block','padding-bottom':'2%'}
            ), style={'width':'20%', 'padding-top':'1%', 'display':'inline-block'}),
        html.Div(
            html.H1(
                children='DASHBOARD COMPRAS', 
                style={'color':'rgb(66,109,97)','padding-bottom':'3%','padding-top':'1%','margin-block-start':'0',
                    'margin-block-end':'0','font-family': 'Roboto, Segoe UI, sans-serif', 'font-style':'oblique'}
            ), style={'width':'60%', 'padding-top':'3%', 'display':'inline-block','float':'right'}),
    ]),
    dcc.Tabs([
        dcc.Tab(label='Compras', children=[
            html.Div([
                html.Div([
                    html.Div(
                        dcc.DatePickerRange(
                            id='Selector Fecha',
                            display_format='DD/MM/YYYY',
                            min_date_allowed=df['Fecha documento'].min(),
                            max_date_allowed=df['Fecha documento'].max(),
                            initial_visible_month=datetime(curr_year, last_month, 1),
                            start_date='2020-01-01',
                            end_date=df['Fecha documento'].max(),
                            start_date_placeholder_text='Fecha Inicial',
                            end_date_placeholder_text='Fecha Final',
                            number_of_months_shown=4 
                        ), style={'width': '100%','padding-bottom':'1%','padding-top':'2%','text-align':'center'}),
                    html.Div([                       
                        html.Div(
                            dcc.Dropdown(
                                id='Sociedades',
                                options=[
                                        {'label': 'Mineros Aluvial', 'value': '1300'},
                                        {'label': 'Operadora Minera', 'value': '1100'},
                                        {'label': 'Mineros S.A', 'value': '1001'},
                                        {'label': 'Negocios Agroforestales', 'value': '1200'}
                                        ],
                                placeholder='Sociedades',
                                value=[1100,1300],
                                multi=True
                            ), style={'width': '30%','padding-top':'1%', 'padding-left':'2%','display':'inline-block'}),  
                        html.Div(
                            dcc.Dropdown(
                                id='Tipo Compra',
                                options=[
                                    {'label':'Internacionales','value':'I'},
                                    {'label':'Nacionales','value':'N'},
                                    {'label':'Locales','value':'B'}                                    
                                ],
                                placeholder='Tipo Compra',
                                value=['N','I','B'],
                                multi=True
                            ), style={'width': '30%','padding-top':'1%', 'padding-left':'1%', 'display':'inline-block'}),
                        html.Div(
                            dcc.Dropdown(
                                id='Clase Documento',
                                placeholder='Clase De Documento',
                                value=['ZMAT','ZIMP','ZSEC','ZSER'], 
                                multi=True
                            ), style={'width': '33%','padding-top':'1%', 'padding-right':'2%', 'padding-left':'1%', 
                            'display':'inline-block'})
                    ], style={'width': '100%','padding-bottom':'1%', 'padding-top':'1%', 'display':'inline-block',
                    'border-style':'solid','border-width':'thin', 'border-color':'#b3b3b3 #ccc #d9d9d9','border-radius':'6px'})]),

            html.Div([
                html.Div(
                    id='Titulo Total Compras',
                    children='Total Compras',
                    style={'width': '30%', 'height':'300%','font-size':'1.5em',
                        'display':'inline-block'} 
                ),
                html.Div( 
                    id='Titulo Compras Nacionales',
                    children='Compras Nacionales',
                    style={'width': '20%','height':'300%','font-size':'1em',
                        'display':'inline-block'}
                ),
                html.Div(
                    id='Titulo Compras Locales',
                    children='Compras Locales',
                    style={'width': '20%', 'height':'300%','font-size':'1em',
                        'display':'inline-block'}
                ),
                html.Div(
                    id='Titulo Compras Internacionales',
                    children='Compras Internacionales',
                    style={'width': '20%', 'height':'300%','font-size':'1em',
                        'display':'inline-block'}
                ),

                html.Div(
                    id='Total Compras',
                    title='Total Compras',
                    style={'width': '30%', 'height':'300%','font-size':'2em',
                        'display':'inline-block'}
                ),
                html.Div( 
                    id='Compras Nacionales',
                    style={'width': '20%','height':'300%','font-size':'1.5em',
                        'display':'inline-block'}
                ),
                html.Div(
                    id='Compras Locales',
                    style={'width': '20%', 'height':'300%','font-size':'1.5em',
                        'display':'inline-block'}
                ),
                html.Div(
                    id='Compras Internacionales',
                    style={'width': '20%', 'height':'300%','font-size':'1.5em',
                        'display':'inline-block'}
                )              
            ], style={'width': '98%', 'height':'100%', 'padding':'1%', 'text-align': 'center',
            'border-style':'solid','border-width':'thin', 'border-color':'black','font-family': 'Roboto, Segoe UI, sans-serif', 'font-style':'oblique'}),    
            html.Div(
                dcc.Graph(id='Top Grupos Articulos'),
                style={'width': '98%', 'bottom':'2%', 'padding':'1%','display':'block','border-style':'solid','border-width':'thin', 'border-color':'#b3b3b3 #ccc #d9d9d9','border-radius':'4px'}),
            html.Div(
                dcc.Graph(id='Top Proveedores'),
                style={'width': '98%', 'bottom':'2%', 'padding':'1%','display':'block','border-style':'solid','border-width':'thin', 'border-color':'#b3b3b3 #ccc #d9d9d9','border-radius':'4px'}),
            html.Div(
                dcc.Graph(id='Pie Chart Driver'),
                style={'width': '48%', 'height':'50%', 'padding':'1%',
                'display':'inline-block','border-style':'solid','border-width':'thin', 'border-color':'#b3b3b3 #ccc #d9d9d9','border-radius':'4px'}),
            html.Div(
                dcc.Graph(id='Pie Chart GC'),
                style={'width': '48%', 'height':'50%', 'padding-bottom':'1%', 'padding-top':'1%','padding-right':'1%',
                'display':'inline-block','border-style':'solid','border-width':'thin', 'border-color':'#b3b3b3 #ccc #d9d9d9','border-radius':'4px'}),
        ])]), 
        dcc.Tab(label='Entregas', children=[
            html.Div([
                html.Div(
                    dcc.DatePickerRange(
                        id='Fecha Entregas',
                        display_format='DD/MM/YYYY',
                        min_date_allowed=df_ent['Fecha Contabilidad MIGO'].min(),
                        max_date_allowed=df_ent['Fecha Contabilidad MIGO'].max(),
                        initial_visible_month=datetime(curr_year, last_month, 1),
                        start_date='2020-01-01',
                        end_date=df_ent['Fecha Contabilidad MIGO'].max(),
                        start_date_placeholder_text='Fecha Inicial',
                        end_date_placeholder_text='Fecha Final',
                        number_of_months_shown=4 
                    ), style={'width': '40%','padding-bottom':'1%','padding-top':'2%','display':'inline-block'}),
                # html.Div(
                #     dcc.Dropdown(
                #         id='Sociedad Entregas',
                #         options=[{'label':'Mineros Aluvial', 'value':'1300'}, {'label':'Operadora Minera', 'value':'1100'}],
                #         placeholder='Seleccione Sociedad',
                #         #value=[1100,1300],
                #         multi=True
                #     ), style={'width': '40%','padding-top':'1%', 'padding-left':'2%','display':'inline-block'})
              ], style={'width': '97%','padding-bottom':'1%','padding-top':'2%','text-align':'center'}),
            html.Div([
                html.Div(
                    id='Entregas Inventario',
                    children='Entregas Inventario',
                    style={'width': '33%', 'height':'300%','font-size':'1.5em',
                        'display':'inline-block'} 
                ),
                html.Div( 
                    id='Entregas Gasto',
                    children='Entregas Gasto',
                    style={'width': '33%','height':'300%','font-size':'1.5em',
                        'display':'inline-block'}
                ),
                html.Div(
                    id='Entregas Activos',
                    children='Entregas Activos',
                    style={'width': '33%', 'height':'300%','font-size':'1.5em',
                        'display':'inline-block'}
                ),
                html.Div(
                    id='Total Inventario',
                    title='Total Inventario',
                    style={'width': '33%', 'height':'300%','font-size':'2em',
                        'display':'inline-block'}
                ),
                html.Div( 
                    id='Total Gasto',
                    style={'width': '33%','height':'300%','font-size':'2em',
                        'display':'inline-block'}
                ),
                html.Div(
                    id='Total Activos',
                    style={'width': '33%', 'height':'300%','font-size':'2em',
                        'display':'inline-block'}
                ),             
            ], style={'width': '98%', 'height':'100%', 'padding':'1%', 'text-align': 'center',
            'border-style':'solid','border-width':'thin', 'border-color':'black','font-family': 'Roboto, Segoe UI, sans-serif', 'font-style':'oblique'}),
            html.Div(
                dcc.Graph(id='Grafica Entregas Por Centro'),
                style={'width': '98%', 'height':'50%', 'padding-bottom':'1%', 'padding-top':'1%', 'padding-left':'1%', 'padding-right':'1%',
                'display':'inline-block','border-style':'solid','border-width':'thin', 'border-color':'#b3b3b3 #ccc #d9d9d9','border-radius':'4px'}),
            # html.Div(
            #     dcc.Graph(id='Grafica Entregas Por Indicador'),
            #     style={'width': '47%', 'height':'50%', 'padding-bottom':'1%', 'padding-top':'1%', 'padding-left':'1%', 'padding-right':'1%',
            #     'display':'inline-block','border-style':'solid','border-width':'thin', 'border-color':'green'}),

        
        ]),
        dcc.Tab(label='Tasa Servicio', children=[
            html.Div([                       
                html.Div(
                    dcc.Dropdown(
                        id='Proveedor',
                        options=[{'label':str(x), 'value': x} for x in tasa_serv['nombre_proveedor'].unique()],
                        placeholder='Seleccione Proveedor',
                        #value=[1100,1300],
                        multi=False
                    ), style={'width': '40%','padding-top':'1%', 'padding-left':'2%','display':'inline-block'}),  
                html.Div(
                    dcc.Dropdown(
                        id='Año',
                        options=[{'label':str(x), 'value': x} for x in tasa_serv['año'].unique()],
                        placeholder='Seleccione Año',
                        #value=[curr_year],
                        multi=False
                    ), style={'width': '30%','padding-top':'1%', 'padding-left':'1%', 'display':'inline-block'}),

            ], style={'width': '100%','padding-bottom':'1%', 'padding-top':'1%', 'display':'inline-block', 'text-align': 'center',
            'border-style':'solid','border-width':'thin', 'border-color':'#b3b3b3 #ccc #d9d9d9','border-radius':'6px'}),
            html.Div(
                dcc.Graph(id='Grafica Tasa'),
                style={'width': '98%', 'bottom':'2%', 'padding':'1%','display':'block',
                    'border-style':'solid','border-width':'thin', 'border-color':'#b3b3b3 #ccc #d9d9d9','border-radius':'4px'}),
        ])
], 
style={'padding-left':'40', 'background-color':'#f5f6f7'})])

# Compras Callbacks

# Load Dropdowns:
@app.callback(
    Output('Clase Documento', 'options'),
    [Input('Selector Fecha', 'start_date'),
    Input('Selector Fecha', 'end_date')]
)
def load_dropdowns(start_date, end_date): # Cambiar los label para que sean los nombres
    filter_1 = df[(df['Fecha documento'] >= start_date) & (df['Fecha documento'] <= end_date)] 
    clase = [{'label': i, 'value': i} for i in list(filter_1['Cl.documento compras'].unique())]

    return clase

# Info Cards
@app.callback(
    [Output('Total Compras', 'children'),
    Output('Compras Nacionales','children'),
    Output('Compras Locales','children'),
    Output('Compras Internacionales','children')],
    [Input('Sociedades', 'value'),
    Input('Tipo Compra', 'value'),
    Input('Clase Documento', 'value'),
    Input('Selector Fecha', 'start_date'),
    Input('Selector Fecha', 'end_date')]
)
def create_value_cards(sociedad, tipo_comp, clase_doc, start_date, end_date):
    filter_1 = df[(df['Fecha documento'] >= start_date) & (df['Fecha documento'] <= end_date)]
    filter_2 = filter_1[
        (filter_1['Organización compras'].isin(sociedad)) & 
        (filter_1['TIPO'].isin(tipo_comp)) & (filter_1['Cl.documento compras'].isin(clase_doc))
        ]
    
    total = filter_2['total_cop'].sum()
    total_nal = filter_2[filter_2['TIPO'] == 'N']['total_cop'].sum()
    total_local = filter_2[filter_2['TIPO'] == 'B']['total_cop'].sum()
    total_int = filter_2[filter_2['TIPO'] == 'I']['total_cop'].sum()
    if total >= 10000000:
        text_total = f'{total/1000000:,.0f} Mill. COP'
    else:
        text_total = f'{total/1000000:,.2f} Mill. COP'
    if total_nal >= 10000000:
        text_total_nal = f'{total_nal/1000000:,.0f} Mill. COP'
    else:
        text_total_nal = f'{total_nal/1000000:,.2f} Mill. COP'
    if total_local >= 10000000:
        text_total_local = f'{total_local/1000000:,.0f} Mill. COP'
    else:
        text_total_local = f'{total_local/1000000:,.2f} Mill. COP'
    if total_int >= 10000000:
        text_total_int = f'{total_int/1000000:,.0f} Mill. COP'
    else:
        text_total_int = f'{total_int/1000000:,.2f} Mill. COP'
    

    return text_total, text_total_nal , text_total_local, text_total_int

# Pie Chart Driver and GC Figure
@app.callback(
    [Output('Pie Chart Driver', 'figure'),
    Output('Pie Chart GC', 'figure')],
    [Input('Sociedades', 'value'),
    Input('Tipo Compra', 'value'),
    Input('Clase Documento', 'value'),
    Input('Selector Fecha', 'start_date'),
    Input('Selector Fecha', 'end_date')]
)
def create_figure_pie(sociedad, tipo_comp, clase_doc, start_date, end_date):
    filter_1 = df[(df['Fecha documento'] >= start_date) & (df['Fecha documento'] <= end_date)]
    filter_2 = filter_1[
        (filter_1['Organización compras'].isin(sociedad)) & 
        (filter_1['TIPO'].isin(tipo_comp)) & (filter_1['Cl.documento compras'].isin(clase_doc))
        ]
    d_total = {}
    d_total_gc = {}
    for sociedad in filter_2['Organización compras'].unique():
        filter_3 = filter_2[filter_2['Organización compras'] == sociedad]
        df_total = filter_3['total_cop'].sum()
        d_total.update({sociedad:df_total})

    total_sociedad = pd.DataFrame(data = d_total, index = ['total']).transpose()
    total_sociedad.reset_index(level=0, inplace=True)
    total_sociedad.rename(columns={'index':'Organización compras'},inplace=True)
    total_sociedad.sort_values(by='total', ascending=False, inplace=True)
    fig = px.pie(total_sociedad, values='total', names='Organización compras', title='Driver')

    for gc in filter_2['Grupo de compras'].unique():
        filter_4 = filter_2[filter_2['Grupo de compras'] == gc]
        df_total_gc = filter_4['total_cop'].sum()
        d_total_gc.update({gc:df_total_gc})

    total_gc = pd.DataFrame(data = d_total_gc, index = ['total']).transpose()
    total_gc.reset_index(level=0, inplace=True)
    total_gc.rename(columns={'index':'Grupo de compras'},inplace=True)
    total_gc.sort_values(by='Grupo de compras', ascending=True, inplace=True)
    fig2 = px.pie(total_gc, values='total', names='Grupo de compras', title='GC')

    return fig, fig2

# Top GA Figure
@app.callback(
    Output('Top Grupos Articulos', 'figure'),
    [Input('Sociedades', 'value'),
    Input('Tipo Compra', 'value'),
    Input('Clase Documento', 'value'),
    Input('Selector Fecha', 'start_date'),
    Input('Selector Fecha', 'end_date')]
)
def create_figure_top_articulo(sociedad, tipo_comp, clase_doc, start_date, end_date): 
    filter_1 = df[(df['Fecha documento'] >= start_date) & (df['Fecha documento'] <= end_date)]
    filter_2 = filter_1[
        (filter_1['Organización compras'].isin(sociedad)) & 
        (filter_1['TIPO'].isin(tipo_comp)) & (filter_1['Cl.documento compras'].isin(clase_doc))
        ]
    traces = []
    d_total = {}
    for g_art in filter_2['Grupo de artículos'].unique():
        filter_3 = filter_2[filter_2['Grupo de artículos'] == g_art]
        df_total = filter_3['total_cop'].sum()
        d_total.update({g_art:df_total})

    total_grup_art = pd.DataFrame(data = d_total, index = ['total']).transpose()
    total_grup_art.reset_index(level=0, inplace=True)
    total_grup_art.rename(columns={'index':'Grupo de artículos'},inplace=True)
    total_grup_art.sort_values(by='total', ascending=False, inplace=True)
    top_15=total_grup_art.head(15)
    for g_art in top_15['Grupo de artículos'].unique():
        d_total = {}
        filter_3 = top_15[top_15['Grupo de artículos'] == g_art]
        traces.append(go.Bar(
                x=filter_3['Grupo de artículos'],
                y=filter_3['total'],
                #text=df_gc['total_cop'],
                opacity=0.6,
                name=g_art
        ))
    return {
        'data': traces,
        'layout': go.Layout(
            title='Top 15 Grupos De Artículos',
            xaxis={'type': 'category', 'categoryorder':'total descending', 'automargin':True},
            yaxis={'title': 'Total COP'},
            #legend={'orientation':'h', 'y':'1.1'},
            # autosize='True',
            # height='500'
        )
    }

# Top Prov Figure
@app.callback(
    Output('Top Proveedores', 'figure'),
    [Input('Sociedades', 'value'),
    Input('Tipo Compra', 'value'),
    Input('Clase Documento', 'value'),
    Input('Selector Fecha', 'start_date'),
    Input('Selector Fecha', 'end_date')]
)
def create_figure_top_proveedores( sociedad, tipo_comp, clase_doc, start_date, end_date): 
    filter_1 = df[(df['Fecha documento'] >= start_date) & (df['Fecha documento'] <= end_date)]
    filter_2 = filter_1[
        (filter_1['Organización compras'].isin(sociedad)) & 
        (filter_1['TIPO'].isin(tipo_comp)) & (filter_1['Cl.documento compras'].isin(clase_doc))
        ]
    traces = []
    d_total = {}
    for proveedor in filter_2['NOMBRE PROVEEDOR'].unique():
        filter_3 = filter_2[filter_2['NOMBRE PROVEEDOR'] == proveedor]
        df_total = filter_3['total_cop'].sum()
        d_total.update({proveedor:df_total})

    total_grup_art = pd.DataFrame(data = d_total, index = ['total']).transpose()
    total_grup_art.reset_index(level=0, inplace=True)
    total_grup_art.rename(columns={'index':'NOMBRE PROVEEDOR'},inplace=True)
    total_grup_art.sort_values(by='total', ascending=False, inplace=True)
    top_15=total_grup_art.head(15)

    for proveedor in top_15['NOMBRE PROVEEDOR'].unique():
        d_total = {}
        filter_3 = top_15[top_15['NOMBRE PROVEEDOR'] == proveedor]
        traces.append(go.Bar(
                y=filter_3['NOMBRE PROVEEDOR'],
                x=filter_3['total'],
                orientation='h',
                #text=df_gc['total_cop'],
                opacity=0.6,
                name=proveedor
        ))
    return {
        'data': traces,
        'layout': go.Layout(
            title='Top 15 Proveedores',
            yaxis={'type': 'category', 'categoryorder':'total ascending', 'automargin':True},
            xaxis={'title': 'Total COP'},
            #legend={'orientation':'h'},
            # autosize='True',
            # height='500'
        )
    }

# Entregas Callbacks

# Info Cards
@app.callback(
    [Output('Total Inventario', 'children'),
    Output('Total Gasto','children'),
    Output('Total Activos','children'),
    Output('Grafica Entregas Por Centro', 'figure')],
    [Input('Fecha Entregas', 'start_date'),
    Input('Fecha Entregas', 'end_date'),
    ]
    )
def create_value_cards_entregas(start_date, end_date):
    filter_1 = df_ent[(df_ent['Fecha Contabilidad MIGO'] >= start_date) & (df_ent['Fecha Contabilidad MIGO'] <= end_date)]
    #filter_1 = filter_1[filter_1['Organizacion Compra'] == sociedad]
    total_invent = filter_1[filter_1['tipo_entrega'] == '1']['total_cop'].sum()
    total_gasto = filter_1[filter_1['tipo_entrega'] == '5']['total_cop'].sum()
    total_activo = filter_1[filter_1['tipo_entrega'].isnull()]['total_cop'].sum()
    if total_invent >= 10000000:
        text_invent = f'{total_invent/1000000:,.0f} Mill. COP'
    else:
        text_invent = f'{total_invent/1000000:,.2f} Mill. COP'
    if total_gasto >= 10000000:
        text_gasto = f'{total_gasto/1000000:,.0f} Mill. COP'
    else:
        text_gasto = f'{total_gasto/1000000:,.2f} Mill. COP'
    if total_activo >= 10000000:
        text_activo = f'{total_activo/1000000:,.0f} Mill. COP'
    else:
        text_activo = f'{total_activo/1000000:,.2f} Mill. COP'

    top_invent = filter_1[filter_1['tipo_entrega'] == '1']
    top_invent.sort_values(by='precio_unit_cop', ascending=False, inplace=True)
    top_invent = top_invent.head()

    top_gasto = filter_1[filter_1['tipo_entrega'] == '5']
    top_gasto.sort_values(by='precio_unit_cop', ascending=False, inplace=True)
    top_gasto = top_gasto.head()

    top_activo = filter_1[filter_1['tipo_entrega'].isnull()]
    top_activo.sort_values(by='precio_unit_cop', ascending=False, inplace=True)
    top_activo = top_activo.head()

    trace3 = go.Bar(
                y=top_invent['Texto Breve'],
                x=top_invent['precio_unit_cop'],
                orientation='h',
                opacity=0.6,
                name='Inventario'
                
        )
    trace2 = go.Bar(
                y=top_gasto['Texto Breve'],
                x=top_gasto['precio_unit_cop'],
                orientation='h',
                opacity=0.6,
                xaxis="x2",
                yaxis="y2",
                name='Gasto'
        )
    trace1 = go.Bar(
                y=top_activo['Texto Breve'],
                x=top_activo['precio_unit_cop'],
                orientation='h',
                opacity=0.6,
                xaxis="x3",
                yaxis="y3",
                name='Activos'                
        )

    data = [trace1, trace2, trace3]
    layout = go.Layout(
        title=dict(text='Top Materiales Entregados Según Tipo', xanchor='center', yanchor='top', x=0.5, y=0.97),
        height=800,
        xaxis=dict(anchor='y1'), yaxis=dict(domain=[0, 0.30], anchor='x1', type= 'category', categoryorder='total ascending'),
        xaxis2=dict(anchor='y2'), yaxis2=dict(domain=[0.35, 0.65], anchor='x2', type= 'category', categoryorder='total ascending'),
        xaxis3=dict(anchor='y3'), yaxis3=dict(domain=[0.70, 1], anchor='x3', type= 'category', categoryorder='total ascending')
    )
    fig = go.Figure(data=data, layout=layout)
    # fig = make_subplots(rows=3, cols=1, subplot_titles=('Top Materiales Inventario', 'Top Materiales Gasto', 'Top Materiales Activo'))
    #fig =[]
    return text_invent, text_gasto, text_activo, fig

# Tasa Servicio
@app.callback(
    Output('Grafica Tasa', 'figure'),
    [Input('Proveedor', 'value'),
    Input('Año', 'value')]
)
def create_figure_tasa_servicio(proveedor, año):
    filter_1 = tasa_serv[(tasa_serv['nombre_proveedor'] == proveedor) & (tasa_serv['año'] == año)]
    meta = 0.95
    meta_año = []
    for i in range (0,12):
        meta_año.append(meta)
    data=go.Scatter(
            x=filter_1['mes'],
            y=filter_1['tasa_servicio'],
            mode='lines+markers',
            #text=df_gc['total_cop'],
            opacity=0.6,
            name='Cumplimiento'
    )
    goal=go.Scatter(
            x=filter_1['mes'],
            y=meta_año,
            mode='lines',
            #text=df_gc['total_cop'],
            opacity=0.6,
            name='Meta'
    )
    return {
        'data': [data, goal],
        'layout': go.Layout(
            title='Tasa Servicio Proveedor',
            xaxis={'title':'Meses', 'automargin':True},
            yaxis={'title':'Cumplimiento','tickformat': ',.0%','range':[0,1.2]},       
            #legend={'orientation':'h', 'y':'1.1'},
            # autosize='True',
            # height='500'
        )
    }

# Add the server clause:
if __name__ == '__main__':
    app.run_server()

