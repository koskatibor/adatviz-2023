import datetime
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import geopandas as gpd
from dash import Dash, dash_table, dcc, Output, Input, DiskcacheManager
import dash_mantine_components as dmc
import diskcache

# INITIALIZE CALLBACK MANAGER
cache = diskcache.Cache("./cache")
bg_callback_manager = DiskcacheManager(cache)

# Initialize Dash application
app = Dash(__name__, background_callback_manager=bg_callback_manager)
server = app.server
app.title = "Secondhand car market Hungary (2020 & 2023)"

# IMPORT 2020 DATA
dtypes = {"ad_id": int, "region_id": int, "ad_price": int, "numpictures": int, "proseller": bool, "adoldness": int, "postal_code": int, "mileage": int, "clime_id": int,  "shifter": str, "person_capacity": int,"doorsnumber": int, "color": int, "brand_id": int, "model_id": int, "ccm": int, "highlighted": bool, "description": str, "advertisement_url": str, "catalog_url": str, "is_sold": bool}
date_columns = ["production", "documentvalid", "sales_date", "download_date", "sales_update_date", "upload_date"]
na_values_list = ["", " ", "NA", None]
ads = pd.read_csv("../db_2020/advertisements_202006112147.csv", dtype=dtypes, parse_dates=date_columns, dayfirst=True, na_values=na_values_list, engine="c", )

# IMPORT 2023 DATA
dtypes = {"ad_id": int, "region": int, "ad_price": int, "numpictures": int, "proseller": bool, "adoldness": int, "postal_code": int, "mileage": int, "clime_id": int,  "shifter": str, "person_capacity": int,"doorsnumber": int, "color": int, "brand_id": int, "model_id": int, "ccm": int, "highlighted": bool, "description": str, "advertisement_url": str, "catalog_url": str, "is_sold": bool}
date_columns = ["production", "documentvalid"]
na_values_list = ["", " ", "NA", None]
ads_2023 = pd.read_csv("../db_2023/advertisements_processed.csv", dtype=dtypes, parse_dates=date_columns, na_values=na_values_list, engine="c", encoding="latin-1")

# IMPORT KEY-VALUE TABLES
dtypes = {"region_id": int, "region_name": str}
counties = pd.read_csv("../db_2020/region_202006112147.csv", dtype=dtypes, engine="c", encoding="latin-1")
dtypes = {"brand_id": int, "brand_name": str}
brands = pd.read_csv("../db_2020/brand_202006112147.csv", dtype=dtypes, engine="c", encoding="latin-1")
dtypes = {"model_id": int, "model_name": str}
models = pd.read_csv("../db_2020/model_202006112147.csv", dtype=dtypes, engine="c", encoding="latin-1")


# INITIALIZE GEOJSON
geo = gpd.read_file("../postal_codes.geojson")

# INITIALIZE DROPDOWN VALUES
region_options = [{'label': label, 'value': value} for label, value in zip(counties['region_name'], counties['region_id'])]
brand_options = [{'label': label, 'value': value} for label, value in zip(brands['brand_name'], brands['brand_id'])]
model_options = [{'label': label, 'value': value} for label, value in zip(models['model_name'], models['model_id'])]

app.layout = dmc.Container([
        dmc.Title('Magyarországi használtautó adatok (2020 - A hasznaltauto.hu hirdetései alapján)', color="blue", size="h3", style={'float': 'center'}),
        dmc.RadioGroup(
            [dmc.Radio(i, value=i) for i in ['2020', '2023']],
            id = 'radio-year',
            value = '2020',
            size = 'sm',
        ),
        dcc.Dropdown(
            id='region-dropdown',
            options=region_options,
            value=counties['region_id'][2],  # Az alapértelmezett kiválasztott érték
            style={'display': 'inline-block', 'margin-left': '10px', 'width': '250px'}
        ),
        dcc.Dropdown(
            id='proseller-dropdown',
            options=['ÖSSZES', 'True', 'False'],
            value='ÖSSZES',  # Az alapértelmezett kiválasztott érték
            style={'display': 'inline-block', 'margin-left': '10px', 'width': '250px'}
        ),
        dcc.Dropdown(
            id='brand-dropdown',
            options=brand_options,
            value=brands['brand_id'][brands.index[brands['brand_id'] == -1][0]],  # Az alapértelmezett kiválasztott érték
            style={'display': 'inline-block', 'margin-left': '10px', 'width': '250px'}
        ),
        # dcc.Dropdown(s
        #     id='model-dropdown',
        #     options=model_options,
        #     value=models['model_id'].sort_values()[0],  # Az alapértelmezett kiválasztott érték
        #     style={'display': 'inline-block', 'margin-left': '10px', 'width': '250px'}
        # ),
        dmc.Title('9336 hirdetés alapján', id='description-text', color="blue", size="h5"),
        dmc.Grid(
            [
                dmc.Col([dcc.Graph(figure={"layout": {"height": 800, 'overflowX': 'auto'}},  # px
                  id='map',
                  style={'height': '1000px'}
                  )], span=6),
                dmc.Col([dcc.Graph(figure={"layout": {"height": 800, 'overflowX': 'auto'}},  # px
                  id='scatter',
                  style={'height': '1000px'}
                  )], span=6),
            ],),
            dmc.Grid(
            [
                dmc.Col([dcc.Graph(figure={"layout": {"height": 800, 'overflowX': 'auto'}},  # px
                  id='brand-pie',
                  style={'height': '1000px'}
                  )], span=6),
                dmc.Col([dcc.Graph(figure={"layout": {"height": 800, 'overflowX': 'auto'}},  # px
                  id='heatmap',
                  style={'height': '1000px'}
                  )], span=6),
            ],
        ),
        dash_table.DataTable(id='data-table',
                             data=ads.head().to_dict('records'),
                             page_size=50,
                             style_table={'overflowX': 'auto'}
                             )
    ], fluid = True)


@app.callback(
    [Output(component_id='data-table', component_property='data'),
     Output(component_id='map', component_property='figure'),
     Output(component_id='description-text', component_property='children'),
     Output(component_id='scatter', component_property='figure'),
     Output(component_id='brand-pie', component_property='figure'),
     Output(component_id='heatmap', component_property='figure')],
    [Input(component_id='radio-year', component_property='value'),
     Input(component_id='region-dropdown', component_property='value'),
     Input(component_id='proseller-dropdown', component_property='value'),
     Input(component_id='brand-dropdown', component_property='value')],
    background=True,
    manager=bg_callback_manager
)
def filter_map(selected_year, region, pro, brand):
    data = filter_data(year=selected_year, region_id=region, proseller=pro, brand_id=brand)
    description = f'{len(data)} hirdetés alapján'
    scatter = generate_scatter(data[['ad_price', 'production', 'postal_code']])
    map = generate_map(prepare_map_data(data[['region_id', 'postal_code', 'ad_price']]))
    pie = generate_brand_pie(data[['brand_id']])
    corr_heatmap = generate_corr_heatmap(data[["region_id", "ad_price", "mileage", "production", "documentvalid", "adoldness", "ccm", "brand_id", "model_id",
         "numpictures", "proseller", "clime_id", "person_capacity", "doorsnumber", "color", "highlighted"]])
    return data.sort_values(by='ad_id').to_dict('records'), map, description, scatter, pie, corr_heatmap


def prepare_map_data(data):
    map_df = geo.merge(data, on="postal_code").sort_values(by="postal_code")

    avg_prices = map_df.groupby('postal_code')['ad_price'].mean().reset_index()
    min_price = map_df.groupby('postal_code')['ad_price'].min().reset_index()
    max_price = map_df.groupby('postal_code')['ad_price'].max().reset_index()
    map_df = map_df.drop_duplicates(subset=['postal_code'])
    map_df = map_df.merge(avg_prices, on="postal_code", suffixes=('', '_avg'))
    map_df = map_df.merge(min_price, on="postal_code", suffixes=('', '_min'))
    map_df = map_df.merge(max_price, on="postal_code", suffixes=('', '_max'))
    map_df = map_df.merge(counties, on="region_id")
    if len(map_df) < 160000:
        map_df["geometry"] = (
            map_df.to_crs(map_df.estimate_utm_crs()).simplify(25).to_crs(map_df.crs)
        )
    else:
        map_df["geometry"] = (
            map_df.to_crs(map_df.estimate_utm_crs()).simplify(50).to_crs(map_df.crs)
        )

    return map_df

def generate_map(map_df):
    fig = px.choropleth_mapbox(
        map_df,
        geojson=map_df.geometry,
        locations=map_df.index,
        color=map_df['ad_price_avg'],  # Az árnyékoláshoz használt oszlop
        color_discrete_sequence="Blues",  # Színárnyalat
        range_color=(map_df['ad_price_avg'].min(), map_df['ad_price_avg'].max()),  # Színskála tartomány
        mapbox_style="carto-positron",  # Térkép stílusa
        hover_data={'region_name', 'postal_code', 'ad_price_avg', 'ad_price_min', 'ad_price_max'},
        labels={'region_name': 'Megye', 'ad_price_avg': 'Autók átlag ára', 'postal_code': 'Irányítószám', 'region_id': 'Megye', 'ad_price_min': 'Legalacsonyabb ár', 'ad_price_max': 'Legmagasabb ár'},
        custom_data={'ad_price'},
        center={"lat": geo.geometry.centroid.y.mean(), "lon": geo.geometry.centroid.x.mean()},  # Középpont koordináták
        zoom=7,  # Kezdeti nagyítás
        opacity=0.5
    )
    return fig

def generate_scatter(data):
    scatter_data = data.query('production > "%s"' % (datetime.date(1900, 1,1))).copy()
    scatter_data.sort_values(by='ad_price')
    fig = px.scatter(x=scatter_data['production'], y=scatter_data['ad_price'], color=scatter_data['postal_code'])
    return fig


def generate_brand_pie(data):
    brand_count = pd.merge(data, brands, on='brand_id', suffixes=('', '_count'))
    brand_counted = brand_count.groupby('brand_name').count().sort_values(by='brand_id', ascending=False)
    fig = px.pie(values=brand_counted['brand_id'][0:10], names=brand_counted.index[0:10], title="Márka szerinti eloszlás - Top 10")
    return fig


def generate_corr_heatmap(data):
    corr_mx = data.corr()
    fig = ff.create_annotated_heatmap(z=corr_mx.values.round(2),
                                   x=list(corr_mx.columns),
                                   y=list(corr_mx.index),
                                   colorscale='Oranges')
    return fig


def filter_data(year='2020', region_id=None, proseller='ÖSSZES', post_code=None, brand_id=None, model_id=None):
    if year == '2020':
        filtered_df = ads.copy()
    else:
        filtered_df = ads_2023.copy()

    if region_id and region_id != -1:
        filtered_df = filtered_df.loc[filtered_df['region_id'] == region_id]
    if proseller != 'ÖSSZES':
        if proseller == 'True':
            filtered_df = filtered_df.loc[filtered_df['proseller'] == True]
        else:
            filtered_df = filtered_df.loc[filtered_df['proseller'] == False]
    if post_code:
        filtered_df = filtered_df.loc[filtered_df['postal_code'] == post_code]
    if brand_id and brand_id != -1:
        filtered_df = filtered_df.loc[filtered_df['brand_id'] == brand_id]
    if model_id and model_id != -1:
        filtered_df = filtered_df.loc[filtered_df['model_id'] == model_id]

    return filtered_df


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run_server()