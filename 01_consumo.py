from flask import Flask, request, render_template_string
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.io as pio
import random
import Config_PythonDeElite as config
import consultas

caminhoBanco = config.DB_PATH 
pio.renderers.default = 'browser'
nomeBanco = config.NOMEBANCO
rotas = config.ROTAS
tabelaA = config.TABELA_A
tabelaB = config.TABELA_B

# Arquivos a serem carregados

dfDrinks = pd.read_csv(f'{caminhoBanco} {tabelaA}')
dfAvengers = pd.read_csv(f'{caminhoBanco}{tabelaB}', encoding='latin1')

# outros exemplos de encodings: utf-8, cp1256, iso 8859-1

# criamos o banco de dados em SQL caso não exista
conn = sqlite3.connect(f'{caminhoBanco} {nomeBanco}')

dfDrinks.to_sql("bebidas", conn, if_exists="replace", index=False)
dfAvengers.to_sql("vingadores", conn, if_exists="replace", index=False)
conn.commit()
conn.close()

html_template = f'''
 <h1> Dashboards - Consumo de Alcool </h1>
    <h2> Parte 01 </h2>
        <ul>
            <li><a href="/grafico1"> Top 10 paises em consumo de alcool </a></li>
            <li><a href="/grafico2"> Media de consumo por Tipo </a></li>
            <li><a href="/grafico3"> Consumo total por Região </a></li>
            <li><a href="/grafico4"> Comparativo entre tipos de bebidas </a></li>
            <li><a href="/pais"> Insights por pais </a></li>
        </ul>
    <h2> Parte 02 </h2>
        <ul>
            <li><a href="/comparar"> Comparar </a></li>
            <li><a href="/upload"> Upload CSV Vingadores </a></li>
            <li><a href="/apagar"> Apagar Tabela </a></li>
            <li><a href="/ver"> Ver Tabela </a></li>
            <li><a href="/vaa"> V.A.A (Vingadores Alcolicos Anonimos) </a></li>
        </ul>
   '''

# iniciar o flask

app = Flask(__name__)

@app.route(rotas[0])
def index():
    return render_template_string("html_template")

@app.route(rotas[1])
def grafico1():
    with sqlite3.connect(f'{caminhoBanco} {nomeBanco}') as conn:
        df = pd.read_sql_query(consultas.consulta01, conn)
    figuraGrafico1 = px.bar(
        df,
        x = 'country',
        y = 'total_litres_of_pure_alcohol',
        title = 'Top 10 países em consumo de alcool'
    )
    return figuraGrafico1.to_html()

@app.route(rotas[2])
def grafico2():
    with sqlite3.connect(f'{caminhoBanco} {nomeBanco}') as conn:
        df = pd.read_sql_query(consultas.consulta02, conn)
    # transforma as colunas cerveja, destilados e vinhos e linhas criando no fim duas colunas, uma chmada bebidas com 
    # nomes originais das colunas e outra com a média de porções com seus  valoress correspondentes
    df_melted = df.melt(var_name='Bebidas', value_name= 'Média de Porções')
    figuraGrafico2 = px.bar(
        df_melted,
        x = 'Bebidas',
        y = 'Média de Porções',
        title = 'Média de consumo por tipo'
    )
    return figuraGrafico2.to_html()




 # inica o servidor
     

if __name__ == '__main__':
    app.run(
            debug=config.FLASK_DEBUG,
            host = config.FLASK_HOST,
            port = config.FLASK_PORT
        )
    