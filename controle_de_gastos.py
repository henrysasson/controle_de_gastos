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
FILE_PATH = "gastos.db"
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
        "message": "update gastos.db",
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
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        valor REAL,
        categoria TEXT,
        descricao TEXT,
        forma_pagamento TEXT,
        recorrente TEXT,
        tipo TEXT
    )
''')
conn.commit()

# INTERFACE DE INPUT
if selected == 'Input':
    st.title('Adicionar Transação')
    st.markdown('---')

    input_type = st.radio("Tipo:", ["Gasto", "Receita"])
    date = st.date_input("Data", datetime.datetime.now(), format="DD.MM.YYYY")
    valor = st.number_input("Valor (R$)", value=0.00, format="%.2f")

    if input_type == "Gasto":

        # DATA
        date = d = st.date_input("Data", datetime.datetime.now(), format="DD.MM.YYYY")

        st.markdown('##')

        # VALOR
        value = st.number_input("Valor (R$)", value=0.00, format="%0.2f")

        st.markdown('##')

        # CATEGORIA
        category = st.selectbox("Categoria",
                    ("Alimentação", "Compras", "Estética", "Farmácia", "Future Me", "Investimento", "Lazer", "Outros", "Transporte"),
                    placeholder="Selecione a categoria",
                    )
        
        st.markdown('##')

        # DESCRIÇÃO
        description = st.text_input("Descrição",
                                    label_visibility="visible",
                                    placeholder="Descrição curta do gasto (Ifood, Cinema, ...)",
                                )

        st.markdown('##')

        # FORMA DE PAGAMENTO
        payment = st.selectbox("Forma de Pagamento",
                    ("Crédito", "PIX", "Dinheiro", "Débito"),
                    placeholder="Selecione a forma de pagamento",)
        
        st.markdown('##')

        # RECORRNTE
        recurrence = st.selectbox("Recorrente?",
                    ("Não", "Sim"))


    if input_type == "Receita":

        # DATA
        date = d = st.date_input("Data", datetime.datetime.now(), format="DD.MM.YYYY")

        st.markdown('##')

        # VALOR
        value = st.number_input("Valor (R$)", value=0.00, format="%0.2f")

        st.markdown('##')

        # CATEGORIA
        category = st.selectbox("Categoria",
                    ("Salário", "Comissão", "Outros"),
                    placeholder="Selecione a categoria",
                    )
    

    if st.button("Salvar"):
        cursor.execute('''
            INSERT INTO transacoes (data, valor, categoria, descricao, forma_pagamento, recorrente, tipo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(date), valor, categoria, descricao, forma_pagamento, recorrente, input_type))
        conn.commit()
        upload_db()
        st.success("Transação salva com sucesso!")

# DASHBOARD BÁSICO
if selected == 'Dashboard':
    st.title("Dashboard")
    df = pd.read_sql_query("SELECT * FROM transacoes ORDER BY data DESC", conn)
    st.dataframe(df)

    col1, col2 = st.columns(2)
    with col1:
        total_gastos = df[df['tipo'] == 'Gasto']['valor'].sum()
        st.metric("Total Gastos", f"R$ {total_gastos:.2f}")
    with col2:
        total_receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        st.metric("Total Receitas", f"R$ {total_receitas:.2f}")
