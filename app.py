import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# =========================================================
# BLOCO 1: CONFIGURAÇÕES DE TELA E ESTILO (UI)
# =========================================================
st.set_page_config(page_title="ZION - PCO", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-left: 2rem; }
    .stSelectbox, .stTextInput, .stNumberInput, .stMultiSelect { max-width: 200px !important; }
    .element-container { margin-bottom: -0.3rem !important; }
    label { font-size: 13px !important; font-weight: bold; }
    .stButton > button { width: 200px !important; background-color: #073763; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# BLOCO 2: FUNÇÕES DE CONEXÃO E DADOS (BACKEND)
# =========================================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except:
        return None

@st.cache_data(ttl=300)
def carregar_dados_planilha(aba):
    client = obter_cliente()
    if client:
        try:
            sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
            data = sh.worksheet(aba).get_all_values()
            return pd.DataFrame(data[1:], columns=data[0])
        except: return pd.DataFrame()
    return pd.DataFrame()

# =========================================================
# BLOCO 3: INTERFACE DE ENTRADA (FORMULÁRIO)
# =========================================================
st.title("🚢 ZION - Gestão PCO")

# Carregamento prévio dos dados para os menus
df_atv = carregar_dados_planilha("Ativos")
df_bal = carregar_dados_planilha("Balsas")
df_rot = carregar_dados_planilha("Rotas")

vgn_id = datetime.now().strftime("VGN-%Y%m%d-%H%M")
st.subheader(f"Registro: {vgn_id}")

# --- LINHA 1 ---
c1, c2, c3, _ = st.columns([1, 1, 1, 5])
v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
v_bal_sel = c2.multiselect("Balsas", df_bal.iloc[:,0] if not df_bal.empty else [])
v_com = c3.text_input("Comandante")

# --- LINHA 2 ---
c4, c5, c6, _ = st.columns([1, 1, 1, 5])
v_ori = c4.selectbox("Origem", df_rot.iloc[:,0].unique() if not df_rot.empty else ["-"])
v_des = c5.selectbox("Destino", df_rot.iloc[:,1].unique() if not df_rot.empty else ["-"])
v_chf = c6.text_input("Chefe de Máquinas")

# --- LINHA 3 ---
c7, c8, c9, _ = st.columns([1, 1, 1, 5])
v_vol = c7.number_input("Volume (m³)", min_value=0.0, max_value=2000000.0, step=100.0)
v_fat = c8.number_input("Faturamento (R$)", min_value=0.0)
v_hor = c9.number_input("Horímetro", min_value=0.0)

# --- LINHA 4 ---
c10, c11, c12, _ = st.columns([1, 1, 1, 5])
v_tmp = c10.number_input("Tempo Previsto (H)", min_value=0)
v_cbm = c11.number_input("Combustível (L)", min_value=0)
v_custo_diesel = c12.number_input("Custo Diesel (R$)", min_value=0.0)

# --- OBSERVAÇÕES ---
st.markdown("---")
v_obs = st.text_area("Observações da Viagem", placeholder="Digite aqui ocorrências ou notas importantes...")

# =========================================================
# BLOCO 4: LÓGICA DE STATUS E SALVAMENTO
# =========================================================
# Regra temporária: Se faturamento < 5000 = Analise
status_viagem = "Aprovado" if v_fat >= 5000 else "Analise"
cor = "green" if status_viagem == "Aprovado" else "red"

st.markdown(f"### STATUS: <span style='color:{cor}'>{status_viagem}</span>", unsafe_allow_html=True)

if st.button("FINALIZAR E SALVAR"):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Montagem da linha para o Google Sheets (Ordem exata das colunas)
    # Certifique-se de que sua planilha tenha essas colunas em ordem.
    lista_final = [
        vgn_id, v_emp, ", ".join(v_bal_sel), v_com, v_ori, v_des, 
        v_vol, v_fat, v_hor, v_tmp, v_cbm, v_custo_diesel, status_viagem, v_obs, agora
    ]
    
    client = obter_cliente()
    if client:
        try:
            sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
            sh.worksheet("Historico").append_row(lista_final)
            st.success(f"✅ Dados enviados! Status: {status_viagem}")
            if status_viagem == "Analise":
                st.warning("🚨 Alerta gerado para a central.")
        except Exception as e:
            st.error(f"Erro ao acessar planilha: {e}")
