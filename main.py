import pandas as pd
import numpy as np 
import plotly.graph_objs as go

folder = 'C:/Users/noturno/Desktop/Airbnb/'
t_ny = 'ny.csv'
t_rj = 'rj.csv'

def standartize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    lat_candidates = ['lat', 'latitude', 'Latitude', 'Lat', 'LAT','LATITUDE']
    lon_candidates =['lon', 'LON', 'Lon', 'Longitude', 'LONGITUDE', 'Long', 'Lng']
    cost_candidates = ['custo', 'valor', 'coust', 'cost', 'price', 'preço']
    name_candidates =['nome', 'name', 'titulo', 'title', 'local', 'place', 'descricao']

    def pick(colnames, candidates):
        # colanmes: lista de nomes das colunas da tabela
        # candidates: lista de possíveis nomes das colunas a serem encontradas
        for c in candidates:
            # percorre cada candidato (c) dentro da lista de candidatos
            if c in colnames:
                # se o candidato for exatamente igual a um dos nomes em colnames (tabela)
                return c
            # retorna esse candidato imediatamente
        for c in candidates:
            # se não encontrou a correspondência percorre novamente cada coluna
            for col in colnames:
                # aqui percorre cada nome de coluna
                if c.lower() in col.lower():
                    # faz igual ao de cima, mas trabalhando em minusculas apenas
                    return col
                # retorna a coluna imediatamente
        return None 
    # se não encontrou nenhuma coluna, nem exato nem parcial, retorna none (nenhum match encontrado)
    lat_col = pick(df.columns, lat_candidates)
    lon_col = pick(df.columns, lon_candidates)
    cost_col = pick(df.columns, cost_candidates)
    name_col = pick(df.columns, name_candidates)

    if lat_col is None or lon_col is None:
        raise ValueError(f"Não encontrei a Latitude e Longitude:{list(df.columns)}")
    
    out = pd.DataFrame()
    out['lat'] =    pd.to_numeric(df[lat_col], errors='coerce')
    out['lon'] =    pd.to_numeric(df[lon_col], errors='coerce')
    out['custo'] =  pd.to_numeric(df[cost_col], errors='coerce')
    out['nome'] =   pd.to_numeric(df[name_col], errors='coerce')

    # remove as linhas sem coordenadas
    out = out.dropna(subset=['lat','lon']).reset_index(drop=True)

    # preenche o custo se for ausente
    if out['custo'].notna().any():
    
        med = float(out['custo'].median())
        if not np.isfinite(med):
            med = 1.0
        out['custo'] = out['custo'].fillna(med)
    else:
        out['custo'] = 1.0
    return out 

def city_center(df: pd.DataFrame) -> dict:
    """
        define a função citycenter que encontra a latitude e longitude media de um grande volume de dados
        --- recebe como parâmetro um dataframe pandas
        --- deve retornar um dicionário (-> dict)
    """
    return dict(
        lat = float(df['lat'].mean()),
        lon = float(df['lon'].mean())
    )

# ----------------------- traces ---------------------------------

def make_point_trace(df:pd.DataFrame,name:str)->go.Scattermapbox:
    hover = (
        "<b>%{customdata[0]}</br><br>"
        "Custo: %{customdata[1]}<br>"
        "Lat: %{lat:.5f}<br>"
        "Lon: %{lon:.5f}"
    )
    # tamanho dos marcadores (normalizados pelo custo)

    c = df['custo'].astype(float).values
    c_min, c_max = float(np.min(c)), float(np.max(c))

    # CASO ESPECIAL: se não existirem valores numéricos válidos ou se todos os custos forem praticamente iguais (diferença <1e-9)
    # cria um array de tamanho fixo 10 para todos os pontos

    if not np.isfinite(c_min) or not np.isfinite(c_max) or abs(c_max - c_min) < 1e-9:
        size = np.full_like(c, 10.0, dtype=float)
    else: 
    # CASO NORMAL: NORMALIZAR OS CUSTOS PARA UM INTERVALO [0,1] E A ESCALA PODE VARIAR ENTRE 6 E 26 (20 DE AMPLITUDE MAIS DESLOCAMENTO DE 6)
    # PONTOS DE CUSTOS BAIXOS ~6 PONTOS DE CUSTO ALTO ~26

        size = (c - c_min) / (c_max - c_min) * 20 + 6
    # mesmo que os dados estejam fora da faixa de 6 a 26 ele evita sua apresentação, forçando a ficar entre o intervalo
    sizes = np.clip(size, 6,26)
    # axis 1 empilha as colunas lado a lado
    custom = np.stack([df['nome'].values, df['custo'].values], axis=1)

    return go.Scattermapbox(
        lat = df['lat'],
        lon = df['lon'],
        mode = 'markers',
        marker = dict(
            size = sizes,
            color = df['custo'],
            colorscale = "Viridis",
            colorbar = dict(title='Custo')
        ),
        name = f'{name} • Pontos',
        hovertemplate = hover,
        customdata = custom
    )

def make_density_trace(df: pd.DataFrame, name: str) -> go.Densitymapbox:
    return go.Densitymapbox(
        lat = df['lat'],
        lon = df['lon'],
        z = df['custo'],
        radius = 20,
        colorscale = "Inferno",
        name = f'{name} • Pontos',
        showscale = True,
        colorbar= dict(title='Custo')
    )

# --------------------------- Main ------------------------------------

def main():
# carregadno so dados e padronizando 
    ny = standartize_columns(pd.read_csv(f'{folder}{t_ny}'))
    rj = standartize_columns(pd.read_csv(f'{folder}{t_rj}'))

    # cria os 4 traces (NY pontos e calor, RJ pontos e calor)
    ny_point = make_point_trace(ny, 'Nova York')
    ny_heat = make_density_trace(ny, 'Nova York')
    rj_point = make_point_trace(rj, 'Rio de Janeiro')
    rj_heat = make_density_trace(rj, 'Rio de Janeiro')

    fig = go.Figure([ny_point, ny_heat, rj_point, rj_heat])

    def center_zoom(df, zoom):
        return dict(
            center = city_center(df),
            zoom = zoom 
        )
    
    buttons = [
        dict(
            label = 'Nova York • Pontos',
            method = "update",
            args = [
                {'visible':[True, False, False, False]},
                {'mapbox': center_zoom(ny, 9)}
            ]
        ),
        dict(
            label = 'Nova York • Calor',
            method = "update",
            args = [
                {'visible':[False, True, False, False]},
                {'mapbox': center_zoom(ny, 9)}
            ]
        ),
        dict(
            label = 'Rio de Janeiro • Pontos',
            method = "update",
            args = [
                {'visible':[False, False, True, False]},
                {'mapbox': center_zoom(ny, 10)}
            ]
        ),
        dict(
            label = 'Rio de Janeiro • Calor',
            method = "update",
            args = [
                {'visible':[False, False, False, True]},
                {'mapbox': center_zoom(ny, 10)}
            ]

        )
    ]

    fig.update_layout(
        title = 'Mapa Interativo de Custos ○ Pontos e mapa de Calor',
        mapbox_style = 'open-street-map', # satellite-streets
        mapbox = dict(center=city_center(rj), zoom=10),
        margin = dict(l=10, r=10, t=50, b=10),
        updatemenus = [dict(
            buttons = buttons,
            direction = 'down',
            x = 0.01,
            y = 0.99,
            xanchor = 'left',
            yanchor = 'top',
            bgcolor = 'white',
            bordercolor = 'lightgrey'

        )],
        legend = dict(
            orientation = 'h',
            yanchor = 'bottom',
            xanchor = 'right',
            y = 0.01,
            x = 0.99
        )
    )

    # Vamos salvar em HTML criando uma página com os dados sem precisar de um servidor para rodar

    fig.write_html(f'{folder}mapa_interativo.html', full_html = True, include_plotlyjs = 'cdn')
    print(f'Arquivo gerado com sucesso! \nSalvo em: {folder}mapa_custos_interativo.html')

    # Inicia o servidor

if __name__ == '__main__':
    main()
                   


