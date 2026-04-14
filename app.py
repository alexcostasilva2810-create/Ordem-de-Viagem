import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO, CAPA E ESTILO (CSS)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# Inicializa o estado da navegação se não existir
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "Capa"
if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = {}

st.markdown("""
    <style>
    /* Ajuste de espaçamento para não ficar colado no topo */
    .block-container { max-width: 1100px; padding-top: 3rem; margin: auto; }
    
    /* Estilização da Capa */
    .capa-container {
        text-align: center;
        padding: 50px;
        background-color: #f8f9fa;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    .titulo-capa { color: #073763; font-size: 45px; font-weight: bold; margin-bottom: 10px; }
    .subtitulo-capa { color: #555; font-size: 20px; margin-bottom: 30px; }
    
    /* Botões e Inputs */
    [data-testid="column"] { min-width: 250px !important; }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.8rem; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; height: 3em; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. FUNÇÕES DE DADOS (VERSÃO BLINDADA)
# =========================================================
@st.cache_data(ttl=2)
def carregar_dados_seguro():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        ativos = sh.worksheet("Ativos").col_values(1)[1:] or ["Nenhum"]
        balsas = sh.worksheet("Balsas").col_values(1)[1:] or ["Nenhuma"]
        rotas = sh.worksheet("Rotas").get_all_values()[1:] or [["-", "-"]]
        hist_raw = sh.worksheet("Historico").get_all_values()
        df_h = pd.DataFrame(hist_raw[1:], columns=hist_raw[0]).loc[:, ~pd.Series(hist_raw[0]).duplicated()] if len(hist_raw) > 1 else pd.DataFrame()
        return ativos, balsas, rotas, df_h
    except:
        return ["Erro"], ["Erro"], [["-", "-"]], pd.DataFrame()

# =========================================================
# 3. NAVEGAÇÃO E TELAS
# =========================================================

# --- TELA 1: CAPA DE APRESENTAÇÃO ---
if st.session_state.pagina_atual == "Capa":
    st.markdown("""
        <div class="capa-container">
            <h1 class="titulo-capa">ZION - Gestão PCO</h1>
            <p class="subtitulo-capa">Sistema Inteligente de Simulação e Controle de Viagens - Transdourada</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        st.write("") # Espaçador
        if st.button("🚀 ENTRAR NO SISTEMA"):
            st.session_state.pagina_atual = "Simulações"
            st.rerun()

# --- TELA 2: SISTEMA PRINCIPAL ---
else:
    with st.sidebar:
        st.title("Menu")
        if st.button("🏠 Voltar para Capa"):
            st.session_state.pagina_atual = "Capa"
            st.rerun()
        
        pagina = st.radio("NAVEGAÇÃO", ["📊 Simulações", "📜 Histórico"])

    ativos, lista_balsas, lista_rotas, df_h = carregar_dados_seguro()
    d = st.session_state.dados_edit

    if pagina == "📊 Simulações":
        st.title("📊 Simulações de Viagem")
        
        with st.expander("🔍 BUSCAR REGISTRO"):
            if not df_h.empty:
                id_sel = st.selectbox("ID:", ["---"] + df_h.iloc[:, 0].tolist())
                if st.button("CARREGAR"):
                    st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
                    st.rerun()

        # --- GRID 4X3 ---
        l1c1, l1c2, l1c3 = st.columns(3)
        v_emp = l1c1.selectbox("Empurrador", ativos, index=0)
        v_bal = l1c2.multiselect("Balsas", lista_balsas, default=[])
        v_com = l1c3.text_input("Comandante", value=d.get('Comandante', ""))

        l2c1, l2c2, l2c3 = st.columns(3)
        oris = sorted(list(set([r[0] for r in lista_rotas if r])))
        dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
        v_ori = l2c1.selectbox("Origem", oris if oris else ["-"], index=0)
        v_des = l2c2.selectbox("Destino", dess if dess else ["-"], index=0)
        v_chf = l2c3.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

        l3c1, l3c2, l3c3 = st.columns(3)
        v_vol = l3c1.number_input("Volume (M³)", value=0.0, format="%.3f")
        v_fat = l3c2.number_input("Faturamento (R$)", value=0.0, format="%.2f")
        v_hor = l3c3.number_input("Horímetro", value=0.0)

        l4c1, l4c2, l4c3 = st.columns(3)
        v_tmp = l4c1.number_input("Tempo (H)", value=0)
        v_cbm = l4c2.number_input("Combustível (L)", value=0)
        v_dsl = l4c3.number_input("Custo Diesel (R$)", value=0.0, format="%.2f")

        v_obs = st.text_area("Observações", value=d.get('Observações', ""))
        
        status = "Aprovado" if v_fat >= 50000 else "Análise"
        st.markdown(f"### STATUS: <span style='color:{'green' if status == 'Aprovado' else 'red'}'>{status}</span>", unsafe_allow_html=True)

        if st.button("✅ FINALIZAR E SALVAR"):
            st.success("Dados salvos com sucesso!")

    elif pagina == "📜 Histórico":
        st.title("📜 Histórico de Lançamentos")
        st.dataframe(df_h, use_container_width=True, hide_index=True)
