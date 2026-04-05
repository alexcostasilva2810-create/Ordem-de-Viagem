import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# CSS para forçar a largura de 5cm (aprox 200px) nos inputs e fixar o layout
st.markdown("""
    <style>
    .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { 
        width: 200px !important; 
    }
    .block-container { padding-top: 1rem; }
    h1 { margin-top: -1rem; }
    </style>
""", unsafe_allow_html=True)

# SIDEBAR (Restaurada conforme pedido)
with st.sidebar:
    st.image("icone ZION.png", width=150)
    st.title("MENU ZION")
    pagina = st.radio("Navegação", ["📊 Simulações", "📋 Ativos", "🚢 Balsas", "📍 Rotas", "📜 Histórico"])

# TÍTULO (Restaurado)
st.image("icone ZION.png", width=50) # Ícone pequeno ao lado do título se desejar
st.title("ZION - Gestão PCO")

# ÁREA DE BUSCA
with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
    st.text_input("Digite o ID da Viagem (ex: VGM 0504-1816)")
    st.button("BUSCAR NA BASE")

# FORMULÁRIO COM LARGURA CONTROLADA (3 Colunas de 200px)
c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    st.selectbox("Empurrador", ["Jacaranda"])
    st.selectbox("Origem", ["STM"])
    st.number_input("Volume (m³)", value=0.0)
    st.number_input("Tempo Previsto (H)", value=0)

with c2:
    st.multiselect("Balsas", ["Balsa 1", "Balsa 2"])
    st.selectbox("Destino", ["MIR"])
    st.number_input("Faturamento (R$)", value=0.0)
    st.number_input("Combustível (L)", value=0)

with c3:
    st.text_input("Comandante")
    st.text_input("Chefe de Máquinas")
    st.number_input("Horímetro", value=0.0)
    st.number_input("Custo Diesel (R$)", value=0.0)

st.text_area("Observações da Viagem")

# STATUS E SALVAR
st.markdown("### STATUS: <span style='color:red'>Analise</span>", unsafe_allow_html=True)
st.button("FINALIZAR E SALVAR")
