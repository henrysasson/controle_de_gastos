import streamlit as st
import sqlite3
import pandas as pd
import datetime
import requests
import base64
import os
import warnings
import calendar
import plotly.express as px

warnings.simplefilter(action='ignore', category=FutureWarning)

# CONFIGURAÇÕES DE INTEGRAÇÃO COM GITHUB
GITHUB_TOKEN = st.secrets["github_token"]
REPO = "henrysasson/controle_de_gastos"
FILE_PATH = "controle_pessoal.db"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title='Controle de Gastos', layout='wide')
options = ['Adicionar Transação', 'Dashboard']
selected = st.sidebar.selectbox('Menu Principal', options)

# FUNÇÕES AUXILIARES

def download_db():
    r = requests.get(GITHUB_API_URL, headers=HEADERS)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content'])
        with open(FILE_PATH, "wb") as f:
            f.write(content)

def upload_db():
    with open(FILE_PATH, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")
    r_get = requests.get(GITHUB_API_URL, headers=HEADERS)
    sha = r_get.json().get("sha") if r_get.status_code == 200 else None

    payload = {
        "message": "update controle_pessoal.db",
        "content": content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    requests.put(GITHUB_API_URL, headers=HEADERS, json=payload)

# BAIXAR O BANCO CASO NÃO EXISTA
if not os.path.exists(FILE_PATH):
    download_db()

# CONEXÃO COM SQLITE
conn = sqlite3.connect(FILE_PATH)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        valor REAL,
        categoria TEXT,
        descricao TEXT,
        forma_pagamento TEXT,
        recorrente TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS receitas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        valor REAL,
        categoria TEXT,
        descricao TEXT
    )
''')
conn.commit()

# INTERFACE DE INPUT
if selected == 'Adicionar Transação':
    st.title('Adicionar Transação')
    st.markdown('---')

    input_type = st.radio("Tipo:", ["Gasto", "Receita"])
    date = st.date_input("Data", datetime.datetime.now(), format="DD.MM.YYYY")
    valor = st.number_input("Valor (R$)", value=0.00, format="%.2f")

    if input_type == "Gasto":
        categoria = st.selectbox("Categoria", (
            "Alimentação", "Compras", "Estética", "Future Me", "Investimento", "Lazer", "Outros", "Saúde","Transporte"))
        descricao = st.text_input("Descrição", placeholder="Ex: Uber, iFood, Cinema...")
        forma_pagamento = st.selectbox("Forma de Pagamento", ("Crédito", "PIX", "Dinheiro", "Débito"))
        recorrente = st.selectbox("Recorrente?", ("Não", "Sim"))

        if st.button("Salvar"):
            cursor.execute('''
                INSERT INTO gastos (data, valor, categoria, descricao, forma_pagamento, recorrente)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(date), valor, categoria, descricao, forma_pagamento, recorrente))
            conn.commit()
            upload_db()
            st.success("Gasto salvo com sucesso!")

    if input_type == "Receita":
        categoria = st.selectbox("Categoria", ("Salário", "Comissão", "Outros"))
        descricao = st.text_input("Descrição", placeholder="Ex: Bônus, Projeto Freelancer...")

        if st.button("Salvar"):
            cursor.execute('''
                INSERT INTO receitas (data, valor, categoria, descricao)
                VALUES (?, ?, ?, ?)
            ''', (str(date), valor, categoria, descricao))
            conn.commit()
            upload_db()
            st.success("Receita salva com sucesso!")

# DASHBOARD BÁSICO
if selected == 'Dashboard':
    st.title("Dashboard")

    # Baixar dados
    df_gastos = pd.read_sql_query("SELECT * FROM gastos ORDER BY data DESC", conn)
    df_receitas = pd.read_sql_query("SELECT * FROM receitas ORDER BY data DESC", conn)
    
    # Converter datas
    df_gastos['data'] = pd.to_datetime(df_gastos['data'])
    df_receitas['data'] = pd.to_datetime(df_receitas['data'])
    
    df_gastos = df_gastos.set_index('data')
    df_receitas = df_receitas.set_index('data')
    
    # Datas padrão
    hoje = datetime.date.today()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
    
 
    # Filtro
    col1, col2= st.columns(2)

    with col1:
        initial_period = st.date_input("Início", primeiro_dia, format="DD.MM.YYYY")

    with col2:    
        final_period = st.date_input("Fim", ultimo_dia, format="DD.MM.YYYY")



      
    temp_df_gastos = df_gastos.loc[(df_gastos.index >= pd.to_datetime(initial_period)) & (df_gastos.index <= pd.to_datetime(final_period))]
    temp_df_receitas = df_receitas.loc[(df_receitas.index >= pd.to_datetime(initial_period)) & (df_receitas.index <= pd.to_datetime(final_period))]
    


    st.markdown('##')

    # Filtro
    temp_df_gastos = df_gastos.loc[(df_gastos.index >= pd.to_datetime(initial_period)) & (df_gastos.index <= pd.to_datetime(final_period))]
    temp_df_receitas = df_receitas.loc[(df_receitas.index >= pd.to_datetime(initial_period)) & (df_receitas.index <= pd.to_datetime(final_period))]

    st.markdown('#')
    
    # Exibição
    col3, col3 = st.columns(2)
    with col1:
        st.metric("Total Gastos", f"R$ {temp_df_gastos['valor'].sum():.2f}")
    with col2:
        st.metric("Total Receitas", f"R$ {temp_df_receitas['valor'].sum():.2f}")




    # Resetar o índice para trabalhar com a coluna 'data'
    temp_df_gastos = temp_df_gastos.reset_index()
    
    # Formatar a data como string no formato DD-MM-YYYY
    temp_df_gastos['data_formatada'] = temp_df_gastos['data'].dt.strftime('%d-%m-%Y')
    
    # Agrupamento por data formatada e categoria
    gastos_agrupados = temp_df_gastos.groupby(['data_formatada', 'categoria'])['valor'].sum().reset_index()
    
    # Gráfico de barras empilhadas
    fig = px.bar(
        gastos_agrupados,
        x='data_formatada',
        y='valor',
        color='categoria',
        title='Gastos Diários por Categoria',
        labels={'data_formatada': 'Data', 'valor': 'Valor (R$)', 'categoria': 'Categoria'},
        text_auto=True
    )
    
    fig.update_layout(
        xaxis_title='Data',
        yaxis_title='Valor (R$)',
        legend_title='Categoria',
        barmode='stack'
    )
    
    st.plotly_chart(fig, use_container_width=True)





    # Resetar o índice
    temp_df_receitas = temp_df_receitas.reset_index()
    
    # Formatar a data como string no formato DD-MM-YYYY
    temp_df_receitas['data_formatada'] = temp_df_receitas['data'].dt.strftime('%d-%m-%Y')
    
    # Agrupamento por data formatada e categoria
    receitas_agrupadas = temp_df_receitas.groupby(['data_formatada', 'categoria'])['valor'].sum().reset_index()
    
    # Gráfico de barras empilhadas
    fig_receitas = px.bar(
        receitas_agrupadas,
        x='data_formatada',
        y='valor',
        color='categoria',
        title='Receitas Diárias por Categoria',
        labels={'data_formatada': 'Data', 'valor': 'Valor (R$)', 'categoria': 'Categoria'},
        text_auto=True
    )
    
    fig_receitas.update_layout(
        xaxis_title='Data',
        yaxis_title='Valor (R$)',
        legend_title='Categoria',
        barmode='stack'
    )
    
    st.plotly_chart(fig_receitas, use_container_width=True)

    


    col4, col5 = st.columns(2)

    with col4:

        # Agrupa os gastos por categoria no período
        gastos_por_categoria = temp_df_gastos.groupby('categoria')['valor'].sum().reset_index()
        
        # Gráfico de pizza
        fig_pizza = px.pie(
            gastos_por_categoria,
            values='valor',
            names='categoria',
            title='Distribuição dos Gastos por Categoria no Período',
            hole=0.3  # donut chart (ou remova para pizza tradicional)
        )
        
        fig_pizza.update_traces(textinfo='percent+label')
        
        st.plotly_chart(fig_pizza, use_container_width=True)


    with col5:

        # Agrupa as receitas por categoria no período
        receitas_por_categoria = temp_df_receitas.groupby('categoria')['valor'].sum().reset_index()
        
        # Gráfico de pizza (formato donut)
        fig_pizza_receitas = px.pie(
            receitas_por_categoria,
            values='valor',
            names='categoria',
            title='Distribuição das Receitas por Categoria no Período',
            hole=0.3  # Donut (opcional)
        )
        
        fig_pizza_receitas.update_traces(textinfo='percent+label')
        
        st.plotly_chart(fig_pizza_receitas, use_container_width=True)


