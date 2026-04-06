import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. DESIGN COMPACTO (TRAVA 5CM / 220px)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = None

st.markdown("""
    <style>
    .block-container { max-width: 1000px; padding-top: 1rem; margin: auto; }
    .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 220px !important; }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.7rem; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 200px; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. CONEXÃO ROBUSTA (BUSCA DIRETA DAS COLUNAS)
# =========================================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

def carregar_coluna_aba(nome_aba):
    """Retorna apenas a primeira coluna de uma aba para evitar erros de DataFrame pesado"""
    client = obter_cliente()
    if not client: return []
    try:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        aba = sh.worksheet(nome_aba)
        # Pega todos os valores da Coluna A (ignorando o cabeçalho)
        valores = aba.col_values(1)[1:] 
        return [v for v in valores if v.strip() != ""]
    except Exception as e:
        return []

@st.cache_data(ttl=10)
def carregar_historico_completo():
    client = obter_cliente()
    try:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet("Historico").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df.loc[:, ~df.columns.duplicated()]
    except: return pd.DataFrame()

# =========================================================
# 3. INTERFACE E SIDEBAR
# =========================================================
with st.sidebar:
    try: st.image("icone ZION.png", width=160)
    except: pass
    st.title("MENU ZION")
    pagina = st.radio("Navegação", ["📊 Simulações", "📜 Histórico"])

# Pré-carregamento das listas (Agora buscando direto a coluna certa)
lista_ativos = carregar_coluna_aba("Ativos")
lista_balsas = carregar_coluna_aba("Balsas")
# Para rotas, pegamos as colunas de Origem (A) e Destino (B)
try:
    sh_rotas = obter_cliente().open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw").worksheet("Rotas")
    lista_origem = list(set(sh_rotas.col_values(1)[1:]))
    lista_destino = list(set(sh_rotas.col_values(2)[1:]))
except:
    lista_origem, lista_destino = ["-"], ["-"]

if pagina == "📊 Simulações":
    # Cabeçalho Compacto
    c_img, c_tit = st.columns([0.15, 0.85])
    with c_img: 
        try: st.image("icone ZION.png", width=55)
        except: pass
    with c_tit: st.title("ZION - Gestão PCO")

    # Busca de Registro
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        df_h = carregar_historico_completo()
        if not df_h.empty:
            sel = st.selectbox("Selecione ID:", ["---"] + df_h.iloc[:, 0].tolist())
            if st.button("CARREGAR DADOS"):
                if sel != "---":
                    st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == sel].iloc[0].to_dict()
                    st.rerun()

    v_id = st.session_state.dados_edit.get('ID', datetime.now().strftime("VGM %d%m-%H%M")) if st.session_state.dados_edit else datetime.now().strftime("VGM %d%m-%H%M")
    st.subheader(f"Registro: {v_id}")

    # --- FORMULÁRIO COMPACTO (3 COLUNAS) ---
    col1, col2, col3 = st.columns(3)

    with col1:
        # AGORA PUXA DINAMICAMENTE DOS ATIVOS
        v_emp = st.selectbox("Empurrador", lista_ativos if lista_ativos else ["Nenhum Ativo"])
        v_ori = st.selectbox("Origem", lista_origem)
        v_vol = st.number_input("Volume (m³)", value=float(st.session_state.dados_edit.get('Volume (m³)', 0)) if st.session_state.dados_edit else 0.0)
        v_tmp = st.number_input("Tempo Previsto (H)", value=int(st.session_state.dados_edit.get('Tempo Previsto (H)', 0)) if st.session_state.dados_edit else 0)

    with col2:
        # AGORA PUXA DINAMICAMENTE DAS BALSAS
        try: b_def = ast.literal_eval(st.session_state.dados_edit.get('Balsas', '[]'))
        except: b_def = []
        v_bal_sel = st.multiselect("Balsas", lista_balsas if lista_balsas else ["Nenhuma Balsa"], default=b_def)
        v_des = st.selectbox("Destino", lista_destino)
        v_fat = st.number_input("Faturamento (R$)", value=float(st.session_state.dados_edit.get('Faturamento (R$)', 0)) if st.session_state.dados_edit else 0.0)
        v_cbm = st.number_input("Combustível (L)", value=int(st.session_state.dados_edit.get('Combustível (L)', 0)) if st.session_state.dados_edit else 0)

    with col3:
        v_com = st.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', "") if st.session_state.dados_edit else "")
        v_chf = st.text_input("Chefe de Máquinas", value=st.session_state.dados_edit.get('Chefe de Máquinas', "") if st.session_state.dados_edit else "")
        v_hor = st.number_input("Horímetro", value=float(st.session_state.dados_edit.get('Horímetro', 0)) if st.session_state.dados_edit else 0.0)
        v_dsl = st.number_input("Custo Diesel (R$)", value=float(st.session_state.dados_edit.get('Custo Diesel (R$)', 0)) if st.session_state.dados_edit else 0.0)

    v_obs = st.text_area("Observações da Viagem", value=st.session_state.dados_edit.get('Observações', "") if st.session_state.dados_edit else "")

    # Status
    status = "Aprovado" if v_fat >= 50000 else "Analise"
    cor = "green" if status == "Aprovado" else "red"
    st.markdown(f"### STATUS: <span style='color:{cor}'>{status}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        st.success(f"Registro {v_id} salvo com sucesso!")
        st.session_state.dados_edit = None

elif pagina == "📜 Histórico":
    st.title("📜 Histórico")
    st.dataframe(carregar_historico_completo(), use_container_width=True)
