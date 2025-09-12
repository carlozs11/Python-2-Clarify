from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import sqlite3
import os
import plotly.graph_objs as go
from dash import Dash, html, dcc
import dash
import numpy as np
import config
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)
DB_PATH = config.DB_PATH

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inadimplencia(
                mes TEXT PRIMARY KEY,
                inadimplencia REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selic(
                mes TEXT PRIMARY KEY,
                selic_diaria REAL
            )
        ''')

vazio = 0

@app.route('/')
def index():
    return render_template_string('''
        <h1> Upload de dados Economicos </h1>
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <label for="campo_inadimplencia"> Arquivo de Inadimplencia: (CSV)</label>
            <input name="campo_inadimplencia" type="file" required>
            <br><br>  
            <label for="campo_selic"> Arquivo de Taxa SELIC: (CSV)</label>
            <input name="campo_selic" type="file" required>
            <br><br>  
            <input type="submit" value="Fazer Upload">
        </form>
        <br><br> 
        <hr>
            <br><a href="/consultar"> Consultar dados Armazenados </a>
            <br><a href="/graficos"> Visualizar Graficos </a>
            <br><a href="/editar_inadimplencia"> Editar dados de Inadimplencia </a>
            <br><a href="/correlacao"> Analisar Correlação </a>
    ''')

@app.route('/upload', methods=["POST","GET"])
def upload():
    inad_file = request.files.get('campo_inadimplencia')
    selic_file = request.files.get('campo_selic')

    # verificar se os arquivos foram recebidos
    if not inad_file or not selic_file:
        return jsonify({'Erro':"Ambos os arquivos devem ser enviados"})
    
    inad_df = pd.read_csv(
        inad_file,
        sep = ';',
        names = ['data','inadimplencia'],
        header = 0
    )
    selic_df = pd.read_csv(
        selic_file,
        sep = ';',
        names = ['data','selic_diaria'],
        header = 0
    )
    inad_df['data'] = pd.to_datetime(inad_df['data'], format='%d/%m/%Y')
    selic_df['data'] = pd.to_datetime(selic_df['data'], format='%d/%m/%Y')

    inad_df['mes'] = inad_df['data'].dt.to_period('M').astype(str)
    selic_df['mes'] = selic_df['data'].dt.to_period('M').astype(str)

    inad_mensal = inad_df[['mes','inadimplencia']].drop_duplicates()
    selic_mensal = selic_df.groupby('mes')['selic_diaria'].mean().reset_index()

    with sqlite3.connect(DB_PATH) as conn:
        inad_mensal.to_sql('inadimplencia', conn, if_exists='replace', index=False)
        selic_mensal.to_sql('selic', conn, if_exists='replace', index=False)
    return jsonify({'Mensagem':'Dados armazenados com sucesso!'})
   
@app.route('/consultar', methods=['POST','GET'])
def consultar():
    if request.method == "POST": #fui copiado ehhehe
        tabela = request.form.get('campo_tabela')
        if tabela not in ['inadimplencia','selic']:
            return jsonify({'Erro':'Tabela inválida'}),400
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
        return df.to_html(index=False)

    return render_template_string('''
        <h1>Consulta de tabelas</h1>
        <form method='POST'>
            <label for="campo_tabela">Escolha a tabela:</label>
            <select name="campo_tabela">
                <option value="inadimplencia">Inadimplencia</option>
                <option value="selic">Taxa Selic</option>
            </select>        
            <br>
            <input type="submit" value="Consultar">
        </form>
    ''')



@app.route('/editar_inadimplecia', methods=['POST', 'GET'])
def editar_inadimplecia():
    if request.method == 'POST':
        mes = request.form.get('campo_mes')
        novo_valor = request.form.get('campo_valor')
        try:
            novo_valor = float(novo_valor)
        except:
            return jsonify({'mensagem':'Valor Invalido'})
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Inadimplencia SET inadimplencia = ?", (novo_valor, mes))
            conn.commit()
        return jsonify({"mensagem":f"Valor atualizado com sucesso para o mes {mes}"})
    
    return render_template_string('''
        <h1> Editar Inadimplencia </h1>
        <form method="post" action="/editar_inadimplencia">
            <label for>"campo_mes">Mês (AAAA-MM)</label>
            <input type="text" name="campo_mes">
                                  
            <label for="campo_valor">Novo valor de Inadimplencia</label>
            <input type="text" name="campo_valor"><br>
                                  
            input type="submit" value="Atualizar">
        </form>
                                      
          ''')

@app.route('/correlacao')
def correlacao():
    with sqlite3.connect(DB_PATH) as conn:
        inad_df = pd.read_sql_query("SELECT * FROM inadimplencia", conn)
        selic_df = pd.read_sql_query("SELECT * FROM selic", conn)

    merged = pd.merge(inad_df, selic_df, on='mes')
    # calcula a correlação entre as duas colunas, ou seja, o coeficiente de correlação de person
    # 1 é correlação positiva perfeita
    # 0 é sem correlação 
    # -1 é correlação negativa perfeita

    correl = merged['inadimplencia'].corr(merged['selic_diaria'])

    # regressão linear para a visualização 
    # o polifit encontra os coeficientes de 'm' (inclinação) e b (intercepto) da regra de regressão linear
    # Essa linha mostra a tendência geral: se a inadimplência sobe ou desce conforme a SELIC varia.

    x = merged['selic_diaria']
    y = merged['inadimplecia']

    m, b = np.polyfit(x, y, 1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x = x,
        y = y,
        mode = 'markers',
        name = 'Inadimplencia X Selic',
        marker = dict(
            color = 'rgba(0, 123, 255, 0.8)',
            size = 12,
            line = dict(width = 2, color = 'white'),
            symbol = 'circle'
        ),
        hovertemplate = 'SELIC: %{x:.2f}%<br>Inadimplencia: %{y:.2f} %<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x = x,
        y = m * x + b,
        # façamos a inclinação multiplicada pelo valor do ponto de dado mais o intercepto gerando nossa linha do gráfico
        mode = 'lines',
        nome = 'Linha de tendencia',
        line = dict(
            color = 'rgba(220, 53, 69, 1)',
            width = '4',
            dash = 'dot'
        )
    ))

    fig.update_layout(
        title = {
            'text':f'<br>Correlacao entre Selic e Inadimplencia</b><br><span style="font-size;16px">Coeficiente de Correlação:{correl:.2f}</span>',
            'y':0.95,
            'x':0.5,
            'yanchor':'center',
            'xanchor':'top',
        },
        xaxis_title = dict(
            text= 'Selic Média Mensal (%)',
            font=dict(size=12, color='gray')
        ),
        yaxis_title = dict(
            text= 'Inadimplencia (%)',
            font=dict(size=12, color='gray')
        ),
        xaxis = dict(
            tickfont=dict(size=14, color='black'),
            gridcolor= 'lightgray', 
        ),
        yaxis = dict(
            tickfont=dict(size=14, color='black'),
            gridcolor= 'lightgray',
        ),
        plot_bgcolor= '#f8f9fa',
        paper_bgcolor= 'white',
        font = dict(size = 14, color = 'black'),
        legend = dict(
            orientation = 'h',
            yanchor = 'bottom',
            y = 1.05,
            xanchor = 'center',
            x = 0.5,
            bgcolor = 'rgba(0,0,0,0)',
            borderwith = 0
        ),
        margin = dict(1=60, r=60, t=120, b=60)
    ) 
    graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    return render_template_string('''
        <html>
            <head>
                <title>Correlação Selic vs Inadimplência</title>
                <style>
                    body{background-color: #ffffff; color:#333;}
                    h1{margin-top:40px;}
                    .container{width:90%; margin: auto; text-align:center;}
                </style>                  
            </head>
            <body>
                <div class='container'>
                    <h1>Correlação entre Selic e Inadimplência</h1>
                    <div>{{ grafico|safe }}</div> 
                </div>
            </body>
        </html>                                               
                                  ''')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)                                  