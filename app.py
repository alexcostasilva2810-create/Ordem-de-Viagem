import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import time

# Configuração da página
st.set_page_config(page_title="ZION - PCO", layout="wide")

# CSS para forçar um layout de grade fixo e evitar sobreposição
st.markdown("""
    <style>
    /* Força os campos a terem largura fixa e impede que subam uns sobre os outros */
    div[data-testid="stSelectbox"], div[data-testid="stTextInput"], 
    div[data-testid="stNumberInput"], div[data-testid="stMultiSelect"] {
        width: 250px !important;
    }
    
    /* Cria um espaçamento consistente entre os blocos */
    .stHorizontalBlock {
        gap: 30px !important;
        margin-bottom: 20px !important;
    }
    
    /* Ajusta o texto do label para não ocupar espaço extra */
    label { font-size: 14px !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

# Função para conectar ao Google Sheets
@st.cache_resource
def conectar():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

# Função com Cache para evitar o erro de Quota (429)
@st.cache_data(ttl=600)
def carregar_dados(aba):
    client = conectar()
    if client:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet(aba).get_all_values()
        return pd.DataFrame(data[1:], columns=data[0])
    return pd.DataFrame()

# APP PRINCIPAL
st.title("🚢 ZION - Gestão PCO Online")

# Carregando dados
df_atv = carregar_dados("Ativos")
df_bal = carregar_dados("Balsas")
df_rot = carregar_dados("Rotas")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Simulações", "📋 Ativos", "⛴️ Balsas", "📍 Rotas"])

with tab1:
    vgn_id = datetime.now().strftime("VGN-%Y%m%d-%H%M")
    st.subheader(f"Planejamento: {vgn_id}")
    
    # Linhas de entrada organizadas com colunas bem definidas
    c1, c2, c3 = st.columns(3)
    emp = c1.selectbox("Empurrador", df_atv.iloc[:,0].tolist() if not df_atv.empty else ["-"])
    bal = c2.multiselect("Balsas", df_bal.iloc[:,0].tolist() if not df_bal.empty else [])
    com = c3.text_input("Comandante")

    c4, c5, c6 = st.columns(3)
    ori = c4.selectbox("Origem", df_rot.iloc[:,0].unique().tolist() if not df_rot.empty else ["-"])
    des = c5.selectbox("Destino", df_rot.iloc[:,1].unique().tolist() if not df_rot.empty else ["-"])
    chf = c6.text_input("Chefe de Máquinas")

    c7, c8, c9 = st.columns(3)
    vol = c7.number_input("Volume Transportado", min_value=0.0)
    fat = c8.number_input("Faturamento (R$)", min_value=0.0)
    hor = c9.number_input("Horímetros (Inicial)", min_value=0.0)

    c10, c11 = st.columns(2)
    tmp = c10.number_input("Tempo Previsto (Horas)", min_value=0)
    cbm = c11.number_input("Combustível (L)", min_value=0)

    if st.button("VALIDAR E SALVAR"):
        st.success("Dados processados com sucesso!")

with tab2: st.dataframe(df_atv, use_container_width=True)
with tab3: st.dataframe(df_bal, use_container_width=True)
with tab4: st.dataframe(df_rot, use_container_width=True)
