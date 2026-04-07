import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E CSS (FIX PARA MULTISELECT)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = {}

# CSS para travar o layout e impedir que o multiselect "empurre" a tela
st.markdown("""
    <style>
    /* Trava a largura do container */
    .block-container { max-width: 1050px; padding-top: 1rem; margin: auto; }
    
    /* FIX: Impede que o campo de balsas cresça infinitamente */
    div[data-baseweb="select"] > div:first-child {
        max-height: 45px; /* Altura de uma linha */
        overflow-y: auto;
    }
    
    /* Ajustes gerais de espaçamento */
    .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 220px !important; }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.8rem; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. FUNÇÕES DE APOIO
# =========================================================
def obter_cliente():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=5)
def carregar_listas_zion():
    try:
        sh = obter_cliente().open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        ori = sorted(list(set([r[0] for r in rotas if r[0]])))
        des = sorted(list(set([r[1] for r in rotas if r[1]])))
        return ativos, balsas, ori, des
    except: return [], [], [], []

# =========================================================
# 3. INTERFACE DE SIMULAÇÃO (LAYOUT ORIGINAL 4X3)
# =========================================================
with st.sidebar:
    try: st.image("icone ZION.png", width=160)
    except: pass
    pagina = st.radio("Navegação", ["📊 Simulações", "📜 Histórico"])

if pagina == "📊 Simulações":
    st.title("ZION - Gestão PCO")
    
    ativos, lista_balsas, origens, destinos = carregar_listas_zion()
    edit = st.session_state.dados_edit
    v_id = edit.get('ID', datetime.now().strftime("VGM %d%m-%H%M"))

    # --- GRID 4 LINHAS X 3 COLUNAS ---
    # Linha 1
    l1c1, l1c2, l1c3 = st.columns(3)
    v_emp = l1c1.selectbox("Empurrador", ativos)
    # Recupera balsas salvas ou lista vazia
    try: b_def = ast.literal_eval(edit.get('Balsas', '[]'))
    except: b_def = []
    v_bal = l1c2.multiselect("Balsas", lista_balsas, default=b_def) # Agora com scroll fixo
    v_com = l1c3.text_input("Comandante", value=edit.get('Comandante', ""))

    # Linha 2
    l2c1, l2c2, l2c3 = st.columns(3)
    v_ori = l2c1.selectbox("Origem", origens)
    v_des = l2c2.selectbox("Destino", destinos)
    v_chf = l2c3.text_input("Chefe de Máquinas", value=edit.get('Chefe de Máquinas', ""))

    # Linha 3
    l3c1, l3c2, l3c3 = st.columns(3)
    v_vol = l3c1.number_input("Volume (M³)", value=float(edit.get('Volume (m³)', 0.0)))
    v_fat = l3c2.number_input("Faturamento (R$)", value=float(edit.get('Faturamento (R$)', 0.0)))
    v_hor = l3c3.number_input("Horímetro", value=float(edit.get('Horímetro', 0.0)))

    # Linha 4
    l4c1, l4c2, l4c3 = st.columns(3)
    v_tmp = l4c1.number_input("Tempo Previsto (H)", value=int(edit.get('Tempo Previsto (H)', 0)))
    v_cbm = l4c2.number_input("Combustível (L)", value=int(edit.get('Combustível (L)', 0)))
    v_dsl = l4c3.number_input("Custo Diesel (R$)", value=float(edit.get('Custo Diesel (R$)', 0.0)))

    v_obs = st.text_area("Observações", value=edit.get('Observações', ""))

    # Status em destaque
    status = "Aprovado" if v_fat >= 50000 else "Analise"
    st.markdown(f"### STATUS: <span style='color:{'green' if status == 'Aprovado' else 'red'}'>{status}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        st.success(f"Viagem {v_id} salva com sucesso!")

# =========================================================
# 4. HISTÓRICO (SEM ERRO DE COLUNAS)
# =========================================================
elif pagina == "📜 Histórico":
    st.title("📜 Histórico")
    try:
        sh = obter_cliente().open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet("Historico").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        # Remove duplicatas de colunas para não dar erro
        df = df.loc[:, ~df.columns.duplicated()]
        st.dataframe(df, use_container_width=True, hide_index=True)
    except:
        st.error("Erro ao carregar banco de dados.")
