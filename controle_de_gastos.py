import streamlit as st
import sqlite3
import pandas as pd
import datetime
import requests
import base64
import os
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

# CONFIGURAÇÕES DE INTEGRAÇÃO COM GITHUB
GITHUB_TOKEN = st.secrets["github_token"]
REPO = "henrysasson/controle_de_gastos"
FILE_PATH = "controle_pessoal.db"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title='Controle de Gastos', layout='wide')
options = ['Input', 'Dashboard']
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
            "Alimentação", "Compras", "Estética", "Farmácia", "Future Me", "Investimento", "Lazer", "Outros", "Transporte"))
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

    df_gastos = pd.read_sql_query("SELECT * FROM gastos ORDER BY data DESC", conn)
    df_receitas = pd.read_sql_query("SELECT * FROM receitas ORDER BY data DESC", conn)

    st.subheader("Gastos")
    st.dataframe(df_gastos)

    st.subheader("Receitas")
    st.dataframe(df_receitas)

    col1, col2 = st.columns(2)
    with col1:
        total_gastos = df_gastos['valor'].sum()
        st.metric("Total Gastos", f"R$ {total_gastos:.2f}")
    with col2:
        total_receitas = df_receitas['valor'].sum()
        st.metric("Total Receitas", f"R$ {total_receitas:.2f}")
