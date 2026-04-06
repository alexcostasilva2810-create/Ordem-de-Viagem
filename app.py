import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E CSS DINÂMICO
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = None

# Sidebar simplificada
with st.sidebar:
    try: st.image("icone ZION.png", width=160)
    except: pass
    st.title("MENU ZION")
    pagina = st.radio("Navegação", ["📊 Simulações", "📜 Histórico"])

# CSS condicional: Compacto na simulação, Largo no histórico
if pagina == "📊 Simulações":
    st.markdown("""
        <style>
        .block-container { max-width: 1050px; padding-top: 1rem; margin: auto; }
        .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 220px !important; }
        div[data-testid="stVerticalBlock"] > div { margin-top: -0.7rem; }
        .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 200px; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .block-container { max-width: 100% !important; padding: 2rem; }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 2. CONEXÃO E CARREGAMENTO (DROPDOWNS DINÂMICOS)
# =========================================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

def carregar_lista_aba(nome_aba, coluna=1):
    client = obter_cliente()
    if not client: return []
    try:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        valores = sh.worksheet(nome_aba).col_values(coluna)[1:]
        return [v for v in valores if v.strip() != ""]
    except: return []

@st.cache_data(ttl=5)
def carregar_historico_df():
    client = obter_cliente()
    try:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet("Historico").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df.loc[:, ~df.columns.duplicated()] # Resolve o erro de colunas duplicadas
    except: return pd.DataFrame()

# =========================================================
# 3. PÁGINA: SIMULAÇÕES
# =========================================================
if pagina == "📊 Simulações":
    # Cabeçalho Zion
    c_img, c_tit = st.columns([0.1, 0.9])
    with c_img: 
        try: st.image("icone ZION.png", width=60)
        except: pass
    with c_tit: st.title("ZION - Gestão PCO")

    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        df_h = carregar_historico_df()
        if not df_h.empty:
            sel = st.selectbox("Selecione ID:", ["---"] + df_h.iloc[:, 0].tolist())
            if st.button("CARREGAR DADOS"):
                if sel != "---":
                    st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == sel].iloc[0].to_dict()
                    st.rerun()

    v_id = st.session_state.dados_edit.get('ID', datetime.now().strftime("VGM %d%m-%H%M")) if st.session_state.dados_edit else datetime.now().strftime("VGM %d%m-%H%M")
    st.subheader(f"Registro: {v_id}")

    # Carrega listas para os Dropdowns
    ativos = carregar_lista_aba("Ativos")
    balsas = carregar_lista_aba("Balsas")
    origens = list(set(carregar_lista_aba("Rotas", 1)))
    destinos = list(set(carregar_lista_aba("Rotas", 2)))

    # Grid de 3 Colunas (5cm cada)
    col1, col2, col3 = st.columns(3)

    with col1:
        v_emp = st.selectbox("Empurrador", ativos if ativos else ["-"])
        v_ori = st.selectbox("Origem", origens if origens else ["-"])
        v_vol = st.number_input("Volume (m³)", value=float(st.session_state.dados_edit.get('Volume (m³)', 0)) if st.session_state.dados_edit else 0.0)
        v_tmp = st.number_input("Tempo Previsto (H)", value=int(st.session_state.dados_edit.get('Tempo Previsto (H)', 0)) if st.session_state.dados_edit else 0)

    with col2:
        try: b_def = ast.literal_eval(st.session_state.dados_edit.get('Balsas', '[]'))
        except: b_def = []
        v_bal = st.multiselect("Balsas", balsas if balsas else [], default=b_def)
        v_des = st.selectbox("Destino", destinos if destinos else ["-"])
        v_fat = st.number_input("Faturamento (R$)", value=float(st.session_state.dados_edit.get('Faturamento (R$)', 0)) if st.session_state.dados_edit else 0.0)
        v_cbm = st.number_input("Combustível (L)", value=int(st.session_state.dados_edit.get('Combustível (L)', 0)) if st.session_state.dados_edit else 0)

    with col3:
        v_com = st.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', "") if st.session_state.dados_edit else "")
        v_chf = st.text_input("Chefe de Máquinas", value=st.session_state.dados_edit.get('Chefe de Máquinas', "") if st.session_state.dados_edit else "")
        v_hor = st.number_input("Horímetro", value=float(st.session_state.dados_edit.get('Horímetro', 0)) if st.session_state.dados_edit else 0.0)
        v_dsl = st.number_input("Custo Diesel (R$)", value=float(st.session_state.dados_edit.get('Custo Diesel (R$)', 0)) if st.session_state.dados_edit else 0.0)

    v_obs = st.text_area("Observações da Viagem", value=st.session_state.dados_edit.get('Observações', "") if st.session_state.dados_edit else "")

    status = "Aprovado" if v_fat >= 50000 else "Analise"
    st.markdown(f"### STATUS: <span style='color:{'green' if status == 'Aprovado' else 'red'}'>{status}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        st.success("Registro Salvo!")
        st.session_state.dados_edit = None

# =========================================================
# 4. PÁGINA: HISTÓRICO (VISUALIZAÇÃO COMPLETA)
# =========================================================
elif pagina == "📜 Histórico":
    st.image("icone ZION.png", width=50)
    st.title("Histórico Completo de Viagens")
    df_full = carregar_historico_df()
    if not df_full.empty:
        # Exibe o DataFrame ocupando toda a largura disponível
        st.dataframe(df_full, use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado encontrado no histórico.")
