import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# =========================================================
# BLOCO 1: CONFIGURAÇÕES DE TELA E NAVEGAÇÃO LATERAL
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# CSS para esconder o menu superior padrão e ajustar a estética
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    /* Ajuste de largura dos campos */
    .stSelectbox, .stTextInput, .stNumberInput, .stMultiSelect { max-width: 210px !important; }
    /* Estilo do Botão Final */
    .stButton > button { 
        width: 100% !important; 
        max-width: 250px;
        background-color: #073763; 
        color: white; 
        font-weight: bold;
        height: 3em;
    }
    /* Estilo da Sidebar */
    section[data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# Menu Lateral Elegante
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3061/3061440.png", width=50) # Ícone de navio opcional
st.sidebar.title("MENU ZION")
pagina = st.sidebar.radio(
    "Navegação",
    ["📊 Simulações", "📋 Ativos", "⛴️ Balsas", "📍 Rotas", "📜 Histórico"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info("ZION - Gestão PCO v2.0")

# =========================================================
# BLOCO 2: CONEXÃO COM GOOGLE SHEETS
# =========================================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=300)
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
# BLOCO 3: INTERFACES DAS PÁGINAS
# =========================================================

# Título fixo no topo com o TIL corrigido
st.title("🚢 ZION - Gestão PCO")

if pagina == "📊 Simulações":
    # Registro formatado em Português: VGM DiaMes-HoraMinuto
    vgn_id = datetime.now().strftime("VGM %d%m-%H%M")
    st.subheader(f"Registro: {vgn_id}")

    df_atv = carregar_dados("Ativos")
    df_bal = carregar_dados("Balsas")
    df_rot = carregar_dados("Rotas")

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
    v_vol = c7.number_input("Volume (m³)", min_value=0.0, max_value=2000000.0)
    v_fat = c8.number_input("Faturamento (R$)", min_value=0.0)
    v_hor = c9.number_input("Horímetro", min_value=0.0)

    # --- LINHA 4 ---
    c10, c11, c12, _ = st.columns([1, 1, 1, 5])
    v_tmp = c10.number_input("Tempo Previsto (H)", min_value=0)
    v_cbm = c11.number_input("Combustível (L)", min_value=0)
    v_custo_diesel = c12.number_input("Custo Diesel (R$)", min_value=0.0)

    st.markdown("---")
    v_obs = st.text_area("Observações da Viagem", placeholder="Notas extras aqui...")

    # STATUS E SALVAMENTO
    status_viagem = "Aprovado" if v_fat >= 5000 else "Analise"
    cor = "green" if status_viagem == "Aprovado" else "red"
    st.markdown(f"### STATUS: <span style='color:{cor}'>{status_viagem}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        lista_final = [vgn_id, v_emp, str(v_bal_sel), v_com, v_ori, v_des, v_vol, v_fat, v_hor, v_tmp, v_cbm, v_custo_diesel, status_viagem, v_obs, agora]
        client = obter_cliente()
        if client:
            try:
                sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
                sh.worksheet("Historico").append_row(lista_final)
                st.success(f"✅ Viagem {vgn_id} salva com sucesso!")
            except Exception as e: st.error(f"Erro: {e}")

elif pagina == "📋 Ativos":
    st.dataframe(carregar_dados("Ativos"), use_container_width=True)

elif pagina == "⛴️ Balsas":
    st.dataframe(carregar_dados("Balsas"), use_container_width=True)

elif pagina == "📍 Rotas":
    st.dataframe(carregar_dados("Rotas"), use_container_width=True)

elif pagina == "📜 Histórico":
    st.dataframe(carregar_dados("Historico"), use_container_width=True)
