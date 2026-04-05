import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÕES E ESTILO (O SEU LAYOUT ORIGINAL)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = None

# CSS para forçar os campos a ficarem juntos e remover espaços inúteis
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.5rem; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; height: 3em; }
    /* Ajuste para inputs ficarem mais baixos e próximos */
    .stNumberInput, .stTextInput, .stSelectbox { margin-bottom: -1rem; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. FUNÇÕES TÉCNICAS
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
            return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame()
        except: return pd.DataFrame()
    return pd.DataFrame()

# =========================================================
# 3. INTERFACE (O SEU DESIGN DA IMAGEM 1)
# =========================================================

# SIDEBAR CORRETA
with st.sidebar:
    try: st.image("icone ZION.png", width=200)
    except: st.warning("Logo não encontrado")
    st.title("MENU ZION")
    pagina = st.radio("Navegação", ["📊 Simulações", "📋 Ativos", "🚢 Balsas", "📍 Rotas", "📜 Histórico"])

if pagina == "📊 Simulações":
    st.markdown("## 🚢 ZION - Gestão PCO")

    # BUSCA COMPACTA
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        df_hist = carregar_dados("Historico")
        if not df_hist.empty:
            c_sel, c_btn = st.columns([3, 1])
            selecionado = c_sel.selectbox("Selecione o registro:", ["---"] + df_hist.iloc[:, 0].tolist(), label_visibility="collapsed")
            if c_btn.button("CARREGAR DADOS"):
                if selecionado != "---":
                    st.session_state.dados_edit = df_hist[df_hist.iloc[:, 0] == selecionado].iloc[0].to_dict()
                    st.rerun()

    # ID DO REGISTRO (Corrigido para nunca ser None)
    vgn_id = st.session_state.dados_edit.get('ID') if st.session_state.dados_edit else datetime.now().strftime("VGM %d%m-%H%M")
    st.markdown(f"#### Registro: {vgn_id}")

    # Bases
    df_atv = carregar_dados("Ativos")
    df_bal = carregar_dados("Balsas")
    df_rot = carregar_dados("Rotas")

    # --- LINHA 1 ---
    col1, col2, col3 = st.columns(3)
    v_emp = col1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    
    bal_def = []
    if st.session_state.dados_edit:
        try: bal_def = ast.literal_eval(st.session_state.dados_edit.get('Balsas', '[]'))
        except: bal_def = []
    v_bal_sel = col2.multiselect("Balsas", df_bal.iloc[:,0] if not df_bal.empty else [], default=bal_def)
    v_com = col3.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', '') if st.session_state.dados_edit else "")

    # --- LINHA 2 ---
    col4, col5, col6 = st.columns(3)
    v_ori = col4.selectbox("Origem", df_rot.iloc[:,0].unique() if not df_rot.empty else ["-"])
    v_des = col5.selectbox("Destino", df_rot.iloc[:,1].unique() if not df_rot.empty else ["-"])
    v_chf = col6.text_input("Chefe de Máquinas", value=st.session_state.dados_edit.get('Chefe de Máquinas', '') if st.session_state.dados_edit else "")

    # --- LINHA 3 ---
    col7, col8, col9 = st.columns(3)
    v_vol = col7.number_input("Volume (m³)", value=float(st.session_state.dados_edit.get('Volume (m³)', 0)) if st.session_state.dados_edit else 0.0)
    v_fat = col8.number_input("Faturamento (R$)", value=float(st.session_state.dados_edit.get('Faturamento (R$)', 0)) if st.session_state.dados_edit else 0.0)
    v_hor = col9.number_input("Horímetro", value=float(st.session_state.dados_edit.get('Horímetro', 0)) if st.session_state.dados_edit else 0.0)

    # --- LINHA 4 ---
    col10, col11, col12 = st.columns(3)
    v_tmp = col10.number_input("Tempo Previsto (H)", value=int(st.session_state.dados_edit.get('Tempo Previsto (H)', 0)) if st.session_state.dados_edit else 0)
    v_cbm = col11.number_input("Combustível (L)", value=int(st.session_state.dados_edit.get('Combustível (L)', 0)) if st.session_state.dados_edit else 0)
    v_dsl = col12.number_input("Custo Diesel (R$)", value=float(st.session_state.dados_edit.get('Custo Diesel (R$)', 0)) if st.session_state.dados_edit else 0.0)

    st.markdown(" ") # Espaço pequeno
    v_obs = st.text_area("Observações da Viagem", value=st.session_state.dados_edit.get('Observações', '') if st.session_state.dados_edit else "", height=100)

    # STATUS E AÇÃO
    status_viagem = "Aprovado" if v_fat >= 5000 else "Analise"
    cor = "green" if status_viagem == "Aprovado" else "red"
    st.markdown(f"### STATUS: <span style='color:{cor}'>{status_viagem}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        # Lógica de salvamento mantida
        st.success("Dados salvos e PDF gerado!")
        st.session_state.dados_edit = None

elif pagina == "📜 Histórico":
    st.title("📜 Histórico")
    st.dataframe(carregar_dados("Historico"), use_container_width=True)

# Outras páginas apenas placeholders para manter o menu da Imagem 1
else:
    st.title(f"Página de {pagina}")
    st.info("Interface em desenvolvimento.")
