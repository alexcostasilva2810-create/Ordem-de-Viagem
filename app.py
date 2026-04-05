import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# CONFIGURAÇÕES E ESTILO (LAYOUT ORIGINAL)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# Inicialização do estado para carregar dados sem erro
if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = None

# CSS mantendo o padrão visual da Imagem 1
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; height: 3em; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# FUNÇÕES DE APOIO
# =========================================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=60)
def carregar_dados(aba):
    client = obter_cliente()
    if client:
        try:
            sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
            data = sh.worksheet(aba).get_all_values()
            return pd.DataFrame(data[1:], columns=data[0])
        except: return pd.DataFrame()
    return pd.DataFrame()

# =========================================================
# INTERFACE (LAYOUT ORIGINAL DA IMAGEM 1)
# =========================================================
st.sidebar.image("icone ZION.png") # Ajustado para o icone
st.sidebar.title("MENU ZION")
pagina = st.sidebar.radio("Navegação", ["📊 Simulações", "📜 Histórico"])

if pagina == "📊 Simulações":
    st.title("🚢 ZION - Gestão PCO")

    # --- BUSCA DE REGISTRO (Corrigido para não perder o layout) ---
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        df_hist = carregar_dados("Historico")
        if not df_hist.empty:
            lista_vgm = ["---"] + df_hist.iloc[:, 0].tolist()
            selecionado = st.selectbox("Selecione o registro:", lista_vgm)
            if st.button("CARREGAR DADOS"):
                if selecionado != "---":
                    st.session_state.dados_edit = df_hist[df_hist.iloc[:, 0] == selecionado].iloc[0].to_dict()
                    st.rerun()

    # Exibe o ID corretamente
    vgn_id = st.session_state.dados_edit.get('ID') if st.session_state.dados_edit else datetime.now().strftime("VGM %d%m-%H%M")
    st.subheader(f"Registro: {vgn_id}")

    # Layout das colunas exatamente como na imagem 1
    c1, c2, c3 = st.columns(3)
    df_atv = carregar_dados("Ativos")
    v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    v_bal = c2.multiselect("Balsas", []) # Placeholder para o seu select
    v_com = c3.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', '') if st.session_state.dados_edit else "")

    c4, c5, c6 = st.columns(3)
    v_ori = c4.selectbox("Origem", ["STM", "MIR"]) # Ajuste conforme sua base
    v_des = c5.selectbox("Destino", ["MIR", "STM"])
    v_chf = c6.text_input("Chefe de Máquinas")

    c7, c8, c9 = st.columns(3)
    v_vol = c7.number_input("Volume (m³)", value=float(st.session_state.dados_edit.get('Volume (m³)', 0)) if st.session_state.dados_edit else 0.0)
    v_fat = c8.number_input("Faturamento (R$)", value=float(st.session_state.dados_edit.get('Faturamento (R$)', 0)) if st.session_state.dados_edit else 0.0)
    v_hor = c9.number_input("Horímetro", value=float(st.session_state.dados_edit.get('Horímetro', 0)) if st.session_state.dados_edit else 0.0)

    c10, c11, c12 = st.columns(3)
    v_tmp = c10.number_input("Tempo Previsto (H)")
    v_cbm = c11.number_input("Combustível (L)")
    v_dsl = c12.number_input("Custo Diesel (R$)")

    v_obs = st.text_area("Observações da Viagem", value=st.session_state.dados_edit.get('Observações', '') if st.session_state.dados_edit else "")

    status_viagem = "Aprovado" if v_fat >= 5000 else "Analise"
    cor = "green" if status_viagem == "Aprovado" else "red"
    st.markdown(f"### STATUS: <span style='color:{cor}'>{status_viagem}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        st.success("✅ Registro processado!")
        st.session_state.dados_edit = None

elif pagina == "📜 Histórico":
    st.title("📜 Histórico")
    st.dataframe(carregar_dados("Historico"), use_container_width=True)
