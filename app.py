import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ==========================================
# # 01 - CONFIGURAÇÕES GERAIS E ESTILO COMPACTO #
# ==========================================
st.set_page_config(page_title="ZION - PCO", layout="wide")

# CSS para eliminar espaços vazios e compactar os campos
st.markdown("""
    <style>
    .block-container {padding-top: 0.5rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem;}
    div.stBlock { margin-bottom: -1.5rem; }
    label { font-size: 13px !important; font-weight: bold; margin-bottom: -0.8rem !important; }
    .stSelectbox, .stTextInput, .stNumberInput, .stMultiSelect { margin-bottom: -1rem !important; }
    button[data-baseweb="tab"] { height: 35px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    h1 { font-size: 22px !important; margin-bottom: 0rem; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# # 02 - CONEXÃO E SEGURANÇA #
# ==========================================
@st.cache_resource
def conectar_google():
    try:
        s = st.secrets["gcp_service_account"]
        pk = s["private_key"].strip().replace("\\n", "\n")
        creds_dict = dict(s)
        creds_dict["private_key"] = pk
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

# ==========================================
# # 03 - MOTOR DE BUSCA DE DADOS #
# ==========================================
def buscar_dados(client, nome_aba):
    try:
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        sh = client.open_by_key(ID_PLANILHA)
        worksheet = sh.worksheet(nome_aba)
        dados = worksheet.get_all_values()
        if len(dados) > 1:
            return pd.DataFrame(dados[1:], columns=dados[0])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# ==========================================
# # EXECUÇÃO DO APP #
# ==========================================
st.title("🚢 ZION - Gestão PCO Online")
client = conectar_google()

if client:
    # Carregamento de dados para os dropdowns
    df_ativos = buscar_dados(client, "Ativos")
    df_balsas = buscar_dados(client, "Balsas")
    df_trip   = buscar_dados(client, "Tripulação")
    df_rotas  = buscar_dados(client, "Rotas")

    # Interface em Abas
    t_ativos, t_balsas, t_trip, t_rotas, t_sim = st.tabs([
        "📋 Ativos", "⛴️ Balsas", "👥 Tripulação", "📍 Rotas", "📊 Simulações"
    ])

    with t_ativos: st.dataframe(df_ativos, use_container_width=True, hide_index=True)
    with t_balsas: st.dataframe(df_balsas, use_container_width=True, hide_index=True)
    with t_trip:   st.dataframe(df_trip, use_container_width=True, hide_index=True)
    with t_rotas:  st.dataframe(df_rotas, use_container_width=True, hide_index=True)

    # ==========================================
    # # 09 - BLOCO: SIMULAÇÕES (VISÃO ULTRA COMPACTA) #
    # ==========================================
    with t_sim:
        id_viagem_auto = datetime.now().strftime("VGN-%Y%m%d-%H%M")
        st.write(f"**Planejamento de Viagem:** `{id_viagem_auto}`")
        
        with st.form("form_pco_pro"):
            # LINHA 1: Recursos
            c1, c2, c3 = st.columns(3)
            with c1:
                opt_emp = df_ativos.iloc[:, 0].tolist() if not df_ativos.empty else ["-"]
                v_empurrador = st.selectbox("Empurrador", opt_emp)
            with c2:
                opt_bal = df_balsas.iloc[:, 0].tolist() if not df_balsas.empty else ["-"]
                v_balsas = st.multiselect("Balsas", opt_bal)
            with c3:
                v_comandante = st.text_input("Comandante")

            # LINHA 2: Origem e Destino (Puxando de Rotas)
            c4, c5, c6 = st.columns(3)
            with c4:
                # Pega a 1ª coluna de Rotas para Origem
                opt_origem = df_rotas.iloc[:, 0].unique().tolist() if not df_rotas.empty else ["-"]
                v_origem = st.selectbox("Origem", opt_origem)
            with c5:
                # Pega a 2ª coluna de Rotas para Destino (ou a 1ª se só tiver uma)
                col_dest = 1 if len(df_rotas.columns) > 1 else 0
                opt_destino = df_rotas.iloc[:, col_dest].unique().tolist() if not df_rotas.empty else ["-"]
                v_destino = st.selectbox("Destino", opt_destino)
            with c6:
                v_chefe = st.text_input("Chefe de Máquinas")

            # LINHA 3: Operacional e Financeiro
            c7, c8, c9 = st.columns(3)
            with c7:
                v_vol = st.number_input("Volume", min_value=0.0)
                v_fat = st.number_input("Faturamento (R$)", min_value=0.0)
            with c8:
                v_tempo = st.number_input("Tempo (Horas)", min_value=0)
                v_comb = st.number_input("Combustível (L)", min_value=0)
            with c9:
                v_horimetro = st.number_input("Horímetro", min_value=0.0)

            st.write("---")
            btn_validar = st.form_submit_button("VALIDAR PLANEJAMENTO E NOTIFICAR")

        if btn_validar:
            st.success(f"Viagem {id_viagem_auto} registrada!")
            ca1, ca2 = st.columns(2)
            ca1.button("📥 Gerar PDF")
            ca2.button("📧 Enviar E-mail")
else:
    st.error("Sem conexão com o Google.")
