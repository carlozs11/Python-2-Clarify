import pandas as pd
import numpy as np 
import plotly.graph_objs as go

folder = 'C:\Users\noturno\Desktop\Airbnb'
t_ny = 'ny.csv'
t_rj = 'rj.csv'

def standartize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    lat_candidate = ['lat', 'latitude', 'Latitude', 'Lat', 'LAT','LATITUDE']
    lon_candidate =['lon', 'LON', 'Lon', 'Longitude', 'LONGITUDE', 'Long', 'Lng']
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