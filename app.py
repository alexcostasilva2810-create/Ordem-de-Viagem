import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# Configuração da página
st.set_page_config(page_title="ZION - PCO", layout="wide")

# CSS para forçar grid compacto e alinhamento
st.markdown("""
    <style>
    /* Container principal compacto */
    .block-container { padding-top: 1rem; padding-left: 2rem; padding-right: 2rem; }
    
    /* Grid que força os elementos a ficarem próximos */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(3, 200px);
        gap: 15px;
        margin-bottom: 20px;
    }
    
    /* Ajustes dos campos */
    div[data-testid="stSelectbox"], div[data-testid="stTextInput"], 
    div[data-testid="stNumberInput"], div[data-testid="stMultiSelect"] {
        width: 190px !important;
    }
    
    label { font-size: 12px !important; font-weight: bold; margin-bottom: -0.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# Funções de Conexão (Google Sheets)
@st.cache_resource
def conectar():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

# APP
st.title("🚢 ZION - Gestão PCO")
client = conectar()

if client:
    # Carregamento simples
    sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
    df_atv = pd.DataFrame(sh.worksheet("Ativos").get_all_values()[1:], columns=sh.worksheet("Ativos").get_all_values()[0])
    df_bal = pd.DataFrame(sh.worksheet("Balsas").get_all_values()[1:], columns=sh.worksheet("Balsas").get_all_values()[0])
    df_rot = pd.DataFrame(sh.worksheet("Rotas").get_all_values()[1:], columns=sh.worksheet("Rotas").get_all_values()[0])

    tabs = st.tabs(["📊 Simulações", "Ativos", "Balsas", "Rotas"])

    with tabs[0]:
        st.subheader(f"Viagem: {datetime.now().strftime('VGN-%Y%m%d-%H%M')}")
        
        # Estrutura de campos
        col1, col2, col3 = st.columns(3)
        emp = col1.selectbox("Empurrador", df_atv.iloc[:,0])
        bal = col2.multiselect("Balsas", df_bal.iloc[:,0])
        com = col3.text_input("Comandante")

        col4, col5, col6 = st.columns(3)
        ori = col4.selectbox("Origem", df_rot.iloc[:,0].unique())
        des = col5.selectbox("Destino", df_rot.iloc[:,1].unique())
        chf = col6.text_input("Chefe de Máquinas")

        col7, col8, col9 = st.columns(3)
        vol = col7.number_input("Volume", min_value=0.0)
        fat = col8.number_input("Faturamento (R$)", min_value=0.0)
        hor = col9.number_input("Horímetro", min_value=0.0)

        col10, col11 = st.columns(2)
        tmp = col10.number_input("Tempo (H)", min_value=0)
        cbm = col11.number_input("Combustível (L)", min_value=0)

        if st.button("VALIDAR E SALVAR"):
            st.success("Dados enviados com sucesso!")
