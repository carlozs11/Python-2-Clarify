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

dfDrinks = pd.read_csv(f'{caminhoBanco}{tabelaA}')
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
            <li><a href="{rotas[1]}"> Top 10 paises em consumo de alcool </a></li>
            <li><a href="{rotas[2]}"> Media de consumo por Tipo </a></li>
            <li><a href="{rotas[3]}"> Consumo total por Região </a></li>
            <li><a href="{rotas[4]}"> Comparativo entre tipos de bebidas </a></li>
        </ul>
    <h2> Parte 02 </h2>
        <ul>
            <li><a href="{rotas [5]}"> Comparar </a></li>
            <li><a href="{rotas [6]}"> Upload CSV Vingadores </a></li>
            <li><a href="{rotas [7]}> Apagar Tabela </a></li>
            <li><a href="{rotas [8]}"> Ver Tabela </a></li>
            <li><a href="{rotas [9]}"> V.A.A (Vingadores Alcolicos Anonimos) </a></li>
        </ul>
   '''

# iniciar o flask

app = Flask(__name__)

def getDbConnect():
    conn = sqlite3.connect(f'{caminhoBanco}{nomeBanco}')
    conn.row_factory = sqlite3.Row 
    return conn

@app.route(rotas[1])
def index():
    return render_template_string(html_template)

@app.route(rotas[2])
def grafico1():
    with sqlite3.connect(f'{caminhoBanco}{nomeBanco}') as conn:
        df = pd.read_sql_query(consultas.consulta01, conn)
    figuraGrafico1 = px.bar(
        df,
        x = 'country',
        y = 'total_litres_of_pure_alcohol',
        title = 'Top 10 países em consumo de alcool'
    )
    return figuraGrafico1.to_html()

@app.route(rotas[3])
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

@app.route(rotas[4])
def grafico():
    regioes = {
        "Europa": ['France', 'Germany', 'Spain', 'Italy','Portugal'],
        "Asia": ['China', 'Japan', 'India', 'Thailand'],
        "Africa": ['Angola', 'Nigéria', 'Egypt', 'Algeria'],
        "Americas": ['USA', 'Brazil', 'Canada', 'Argentina', 'México']
    }
    dados = []
    with sqlite3.connect(f'{caminhoBanco} {nomeBanco}') as conn:
        # intera sobre o dicionário de regiões onde cada chave (região tem uma lista de países)
        for regiao, paises in regioes.items():
            # criando a lista de placeholders para os países dessa região, isso vai ser usado na consulta SQL para filtrar o
            # país da região
            placeholders = ",".join([f"'{p}'" for p in paises])
            query = f"""
                SELECT SUM(total_litres_of_pure_alcohol) AS total FROM bebidas 
                WHERE country in({placeholders})
            """
            total = pd.real_sql_query(query, conn).iloc[0,0]
            dados.append(
                    {
                        "Regiao": regiao,
                          "Consumo total": total})
    dfRegioes = pd.DataFrame(dados)
    figuraGrafico3 = px.pie(
        dfRegioes,
        names = "Região",
        values = "Consumo Total",
        title = "Consumo total por Região"
    )
    return figuraGrafico3.to_html() + "<br><a href='{rotas[0]}'>Voltar</a>"

@app.route(rotas[5])
def grafico4():
    with sqlite3.connect(f'{caminhoBanco}{nomeBanco}') as conn:
        df = pd.real_sql_query(consultas.consulta03,conn)
        medias = df.mean().reset_index()
        medias.columns = ['Tipo','Média']
        figuraGrafico4 = px.pie(
            medias,
            names = "Tipo",
            values = "Média",
            title = "Proporção média entre os tipos de bebidas!"
        )

        return figuraGrafico4.to_html() + f"<br><a href= '{rotas[0]}'>Voltar</a>"
    
@app.route(rotas[5], methods=["POST", "GET"])
def comparar():
    opcoes = [
        'beer_servings',
        'spirit_servings',
        'wine_servings'
    ]

    if request.method == "POST":
        eixoX = request.form.get('eixo_x')
        eixoY = request.form.get('eixo_y')
        if eixoX == eixoY:
            return "<h3> Selecione campos diferentes! </h3><br><a href='{rotas[0]}'>Voltar</a>"
        conn = sqlite3.connect(f'{caminhoBanco}{nomeBanco}')
        df = pd.real_sql_query("SELECT country, {}, {} FROM bebidas".format(eixoX,eixoY), conn)
        conn.close()
        figuraComparar = px.scatter(
            df,
            x = eixoX,
            y = eixoY,
            title = f"Comparação entre {eixoX} VS {eixoY}"
        )
        figuraComparar.update_traces(textposition = 'top center')
        return figuraComparar.to_html() + f"<br><a href='{rotas[0]}'>Voltar</a>"

    return render_template_string('''
        <h2> Comparar campos </h2>
        <form method="POST">
            <label> Eixo X: </label>
            <select name="eixo_x">
                    {% for opcao in opcoes %}
                        <option value='{{opcao}}'>{{opcao}}</option>
                    {% endfor %}      
            </select>
            <br><br>  
                                  
            <label> Eixo Y: </label>
            <select name="eixo_y">
                      {% for opcao in opcoes %}
                        <option value='{{opcao}}'>{{opcao}}</option>
                    {% endfor %}             
            </select>
            <br><br> 
                                                                          
            <input type="submit" value="-- Comparar --">
        </form>
        <br><a href="{{rotaInterna}}">Voltar</a>
                                  
    ''', opcoes = opcoes, rotaInterna = rotas[0])

@app.route(rotas[6], methods=['GET', 'POST'])
def upload():
    if request.method == "POST":
        recebido = request.files['c_arquivo']
        if not recebido: 
            return f"<h3> Nenhum arquivo enviado! </h3><br><a href='{rotas[6]}'>Voltar</a>"
        dfAvengers = pd.read_csv(recebido, encoding='latin1')
        conn = sqlite3.connect(f'{caminhoBanco}{nomeBanco}')
        dfAvengers.to_sql("vingadores", conn, if_exists="replace", index=False)
        conn.commit()
        conn.close()
    return '''
        <h2> Upload da tabela Avengers! </h2>
        <form method="POST" enctype="multipart/form-data">
            <!-- Isso é um comentário no HTML -->
            <input type="file" name="c_arquivo" accept=".csv">
            <input type="submit"> value="--Carregar --">
        </form>
    '''

@app.route('/apagar_tabela/nome_tabela>', methods=['DELETE'])
def apagarTabela(nome_tabela):
    conn = getDbConnect()
    cursor = conn.cursor()
    # confirmar se a tabela existe
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{nome_tabela}'")
    existe = cursor.fetchone()[0]
    if not existe :
        conn.close()
        return "Tabela não encontrada"
    

    try:
        cursor.execute(f'DROP TABLE "{nome_tabela}"')
        conn.commit()
        conn.close()

    except Exception as erro:
        conn.close()
        return f"Não foi possível apagar a tabela erro: {erro}"
    
@app.route(rotas[8], methods=["POST","GET"])
def ver_tabela():
    if request.method == "POST":
        nome_tabela = request.form.get('tabela')
        if nome_tabela not in ['bebidas', 'vingadores']:
            return f"<h3>Tabela {nome_tabela} não encontrada!<h3><br><a href={rotas[8]}>Voltar</a>"

        conn =getDbConnect()
        df = pd.real__sql_query(f"SELECT * from {nome_tabela}", conn)
        conn.close()
        tabela_html = df.to_html(classes='table table-striped')
        return f'''
            <h3>Conteudo da tabela {nome_tabela}:</h3>
            {tabela_html}
            <br><a href={rotas[8]}>Voltar</a>
        '''

    
    return render_template_string('''
        <h2>Selecione a tabela a ser visualizada:</marquee>
        <form method="POST">
            <label for="tabela">Escolha a tabela abaixo:</label>
            <select> name="tabela">
                <option value="bebidas">Bebidas</option>
                <option value="vingadores">Vingadores</option>
            </select>
        <input type="submit"  value="Consultar tabela">
        </form>
        <hr>
        <br><a href={{rotas[0]}} >Voltar</a>
    ''', rotas=rotas)

app.route(rotas[7], methods=['POST', 'GET'])
def apagarV2():
    if request.method == "POST":
        nome_tabela = request.form.get('tabela')
        if nome_tabela not in ['bebidas','vingadores']:
            return f"<h3>Tabela {nome_tabela} não encontrada!<h3><br><a href={rotas[7]}>Voltar</a>"
        confirmacao = request.form.get('confirmacao')
        conn = getDbConnect()
        if confirmacao == "Sim":

            try:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', (nome_tabela,))
                if cursor.fetchone() is None:
                    return f"<h3>Tabela {nome_tabela} nome não encontrada no banco de dados! </h3><br><a href={rotas[7]}>Voltar</a>"
                cursor.execute(f'DROP TABLE IF EXISTS "{nome_tabela}"')
                conn.commit()
                conn.close()
                return f"<h3>Tabela {nome_tabela} Excluída com sucesso! </h3><br><a href={rotas[7]}>Voltar</a>"



            except Exception as erro:
                conn.close()
                return f"</h3>Erro ao apagar a tabela {nome_tabela} Erro:{erro} </h3><br><a href={rotas[7]}>Voltar</a>"
        


    
    return f'''
    <html>
        <head>
        <title><marquee> CUIDADO!- Apagar tabela  </marquee></
        title>
        </head>
        <body>
        <h2> Selecione a tabela para apagar </h1>
        <form method="POST" id="formApagar">
            <label for= "tabela"> Escolha na tabela abaixo: </label>
            <select name="table" id="tabela">
            <option> value="bebidas">Bebidas</option>
            <option value="vingadores">Vingadores</option>
            <option value="vingadores">Usuarios</option>
            <select>
            <input type="hidden" name="confirmacao" value=""id="confirmacao">
            <input type="submit" value="-- Apagar! --" onclick="return)

        <form>
        <br><a href={{rotas[0]}} >Voltar</a>
        <script type="text/javascript">
            function confirmarExclusao(){{
                var ok = confirm('Tem certeza de que deja apagar a tabela selecionada?');
                if(ok) {{
                    document.getElementById
                    ('confirmacao').value = 'Não';
                    return false;
                }}
            }}
        </script>
        </body>
    </html>
        '''

@app.route(rotas[9], methods=['GET', 'POST'])
def vaa_mortes_consumo():
    # cada dose corresponde a 14g de alcool puro!
    metricas_beb = {
        "Total (L de Alcool)":"total_litres_of_pure_alcohol",
        "Cerveja":"bee_servings",
        "Destilados (Doses)":"spirit_servings",
        "Vinho":"wine_servings"
    }

    if request.method == "POST":
        met_beb_key = request.form.get("metrica_beb") or "Total (L de Alcool)"
        met_beb = metricas_beb.get(met_beb_key, "total_litres_of_pure_alcohol")

        # semente opcional para reproduzir a mesma distribuição de países nos vingadores
        try:
            semente  = int(request.form.get("semente"))
        except:
            semente = 42
        sementeAleatoria = random.Random(semente) # agora o valor aleatório baseado na semente escolhida.

        # lê os dados do SQL
        with getDbConnect() as conn:
            dfA = pd.read_sql_query('SELECT * FROM vingadores', conn)
            dfB = pd.real_sql_query('SELECT country, beer_servings, spirit_servings, wine_servings, total_litres_of_pure_alcohol FROM bebidas', conn)

    # ---- Mortes dos vingadores
    # estratégia: somar colunas que contenha o death como true (case-insensitive)
    # contaremos não-nulos como 1, ou seja, death1 tem True? vale 1, não tem nada? vale 0
    death_cols = [c for c in df.columns if "death" in c.lower()]
    if death_cols:
        dfA["Mortes"] = dfA[death_cols].notna().astype(int).sum(axis=1)
    elif "Deaths" in dfA.columns:
        # fallback óbvio
        dfA["Mortes"] = pd.to_numeric(dfA["Deaths"], errors="coerce").fillna(0).astype(int)
    else:
        dfA["Mortes"] = 0

    if "Name/Alias" in dfA.columns:
        col_name = "Name/Alias"
    elif "Name" in dfA.columns:
        col_name = "Name"
    elif "Alias" in dfA.columns:
        col_name = "Alias"
    else:
        possivel_texto = [c for c in dfA.columns if dfA[c].dtype == "object"]
        col_name = possivel_texto[0] if possivel_texto else dfA.columns [0]

    dfA.rename(columns={col_name: "Personagem"}, inplace=True)

    # ---- sortear um país para cada vingador
    paises = dfB["country"].dropna().astype(str).to_list()
    if not paises:
        return "<h3>Não há países na tabela de bebidas!</h3><a href={{rotas[9]}}>Voltar</a>"
    dfA["Pais"]  = [sementeAleatoria.choice(paises) for _ in range(len(dfA))]
    dfB_cons = dfB[["country",met_beb]].rename(columns={"country":"Pais",
    met_beb : "Consumo"
    })
    base = dfA[["Personagem", "Mortes", "Pais"]].merge(dfB_cons, on="Pais", how="left")

    # filtrar apenas linhas válidas 
    base = base.dropna(subset=['Consumo'])
    base["Mortes"] = pd.to_numeric(base["Mortes"], errors="coerse").fillna(0).astype(int)
    base = base[base["Mortes"] >= 0]
    # correlação (se possível) 
    corr_txt = ""
    if base["Consumo"].notna().sum() >= 3 and base["Mortes"].notna().sum() >= 3:
        try:
            corr = base["Consumo"].corr(base["Mortes"])
            corr-txt = f"  • r   = {corr:.3f} "
        except Exception:
            pass
    


    # ---------- FRAFICO SCATTER 2D: CONSUMO X MORTES (cor = pais) -------------

    fig2d = px.scatter(
        base,
        x = "Consumo",
        y = "Mortes",
        color = "Pais",
        hover_name = "Personagem",
        hover_data = {
            "Pais": True,
            "Consumo": True,
            "Mortes": True
        },
        title =f"Vingadores - Mortes VS consumo de Alcool do pais ({met_beb_key}){corr_txt}"
    )
    fig2d.update_layout(
        xaxis_title = f"{met_beb_key}",
        yaxis_title = "Mortes (contagem)",
        margin = dict(1=40, r=20, t=70, b=40)
    )
    return(
        "<h3> --- Grafico 2D --- </h3>"
        +fig2d.to_html(full_html= False)
        + "<hr>"
        + "<h3> --- Grafico 3D --- </h3>"
        + "<p> Em breve </p>"
        + "<hr>"
        + "<h3> --- Preview dos dados --- </h3>"
        + "<p> Em breve </p>"
        + "<hr>"
        + f"<a href={rotas[9]}>Voltar</a>"
        + "<br>"
        + f"<a href={rotas[0]}>Menu Inicial</a>" 
    )


    return render_template_string('''

    <style>
    body {
    margin: 0;
    padding: 0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f4f7fa;
    color: #333;
}

/* Container geral */
body {
    padding: 40px 20px;
    max-width: 800px;
    margin: auto;
}

/* Título */
h2 {
    text-align: center;
    font-size: 28px;
    color: #2c3e50;
    margin-bottom: 30px;
}

/* Formulário */
form {
    background-color: #fff;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    margin-bottom: 30px;
}

/* Labels */
label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #34495e;
}

/* Campos de entrada */
select,
input[type="number"] {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 6px;
    margin-bottom: 20px;
    box-sizing: border-box;
    font-size: 14px;
    transition: border-color 0.3s ease;
}

select:focus,
input[type="number"]:focus {
    border-color: #2980b9;
    outline: none;
}

/* Botão */
input[type="submit"] {
    background-color: #3498db;
    color: white;
    padding: 12px 20px;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.3s ease;
    width: 100%;
}

input[type="submit"]:hover {
    background-color: #2980b9;
}

/* Parágrafo explicativo */
p {
    font-size: 15px;
    line-height: 1.6;
    background-color: #ecf0f1;
    padding: 15px 20px;
    border-radius: 6px;
    color: #2c3e50;
}

/* Link Voltar */
a {
    display: inline-block;
    margin-top: 15px;
    text-decoration: none;
    color: #3498db;
    font-weight: 600;
    transition: color 0.3s ease;
}

a:hover {
    color: #1f618d;
}
    </style>                             
     <h2> V.A.A - País X Consumo X Mortes </h2>
        <form method="POST">
            <label for="metrica_beb"> Metrica de Consumo: </label>
            <select name="metrica_beb" id="metrica_beb">
                {% for metrica in metricas_beb.keys() %}
                        <option value="{{metrica}}"> {{metrica}}
                        </option>
                {% endfor %}
            </select>
            <br><br>
            <label> <b>Semente: (<i>opcional,,p/ reprodutibilidade</i>) </label>
            <input type="number" name="semente" id="semente" value="42">
            <br><br>
            <input type="submit" value="--Gerar Graficos--">
        </form>
        <p>
                Esta visão sortei um país para cada vingador, soma as mortes dos personagens(Usando todas as colunas
                que contenham Death) e anexa o consumo de alcool do país, ao fim plota um Scatter 2D (Consumo X Mortes) e um Gráfico 3D
                (Pais X Mortes)
        </p>
        <br>
        <a href={{rotas[0]}}>Voltar</a>
        ''', metricas_beb = metricas_beb, rotas=rotas)


 # inica o servidor
     

    if __name__ == '__main__':
        app.run(
            debug=config.FLASK_DEBUG,
            host = config.FLASK_HOST,
            port = config.FLASK_PORT
        )
    