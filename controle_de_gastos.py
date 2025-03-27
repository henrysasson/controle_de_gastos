import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import streamlit as st

import pandas as pd

import plotly.graph_objects as go
import datetime

import warnings

# Suppress FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)


st.set_page_config(page_title='Controle de Gastos', layout='wide')


options = ['Input', 'Dashboard']
selected = st.sidebar.selectbox('Main Menu', options)


if selected == 'Input':

    st.title('Input')
    st.markdown('##')


    input_type = st.radio(
    " ",
    ["Gasto", "Receita"])

    st.markdown('##')

    if input_type == "Gasto":

        # DATA
        date = d = st.date_input("Data", datetime.datetime.now(), format="DD.MM.YYYY")

        # st.markdown('##')

        # VALOR
        value = st.number_input("Valor (R$)", value=0.00, format="%0.2f")

        st.markdown('##')

        # CATEGORIA
        category = st.selectbox("Categoria",
                    ("Alimentação", "Compras", "Estética", "Farmácia", "Future Me", "Investimento", "Lazer", "Outros", "Transporte"),
                    placeholder="Selecione a categoria",
                    )
        
        # st.markdown('##')

        # DESCRIÇÃO
        description = st.text_input("Descrição",
                                    label_visibility="visible",
                                    placeholder="Descrição curta do gasto (Ifood, Cinema, ...)",
                                )

        # st.markdown('##')

        # FORMA DE PAGAMENTO
        payment = st.selectbox("Forma de Pagamento",
                    ("Crédito", "PIX", "Dinheiro", "Débito"),
                    placeholder="Selecione a forma de pagamento",)
        
        # st.markdown('##')

        # RECORRNTE
        recurrence = st.selectbox("Recorrente?",
                    ("Não", "Sim"))



    if input_type == "Receita":

        # DATA
        date = d = st.date_input("Data", datetime.datetime.now(), format="DD.MM.YYYY")

        # st.markdown('##')

        # VALOR
        value = st.number_input("Valor (R$)", value=0.00, format="%0.2f")

        # st.markdown('##')

        # CATEGORIA
        category = st.selectbox("Categoria",
                    ("Salário", "Comissão", "Outros"),
                    placeholder="Selecione a categoria",
                    )
