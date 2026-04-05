import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ==========================================
# # 01 - CONFIGURAÇÕES GERAIS E VISUAL #
# ==========================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# CSS para compactar a tela e reduzir a largura dos campos
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    h1 {margin-top: -2rem;}
    .stSelectbox, .stTextInput, .stNumberInput, .stMultiSelect {
        max-width: 100%;
    }
    div[data-baseweb="select"] {font-size: 14px;}
    label {font-size: 14px !important; font-weight: bold;}
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
# # EXECUÇÃO #
# ==========================================
st.title("🚢 ZION - Gestão PCO Online")
client = conectar_google()

if client:
    # Carregamento prévio das abas
    df_ativos = buscar_dados(client, "Ativos")
    df_balsas = buscar_dados(client, "Balsas")
    df_trip   = buscar_dados(client, "Tripulação")
    df_rotas  = buscar_dados(client, "Rotas")

    # # 04 - INTERFACE DE NAVEGAÇÃO
    t_ativos, t_balsas, t_trip, t_rotas, t_sim = st.tabs([
        "📋 Ativos", "⛴️ Balsas", "👥 Tripulação", "📍 Rotas", "📊 Simulações"
    ])

    with t_ativos: st.dataframe(df_ativos, use_container_width=True, hide_index=True)
    with t_balsas: st.dataframe(df_balsas, use_container_width=True, hide_index=True)
    with t_trip:   st.dataframe(df_trip, use_container_width=True, hide_index=True)
    with t_rotas:  st.dataframe(df_rotas, use_container_width=True, hide_index=True)

    # ==========================================
    # # 09 - BLOCO: SIMULAÇÕES (PCO) #
    # ==========================================
    with t_sim:
        id_viagem_auto = datetime.now().strftime("VGN-%Y%m%d-%H%M")
        st.subheader(f"🚀 Planejamento: {id_viagem_auto}")
        
        with st.form("form_pco_compacto"):
            # LINHA 1: Recursos principais
            c1, c2, c3 = st.columns(3)
            with c1:
                opt_emp = df_ativos.iloc[:, 0].tolist() if not df_ativos.empty else ["-"]
                v_empurrador = st.selectbox("Empurrador", opt_emp)
            with c2:
                opt_bal = df_balsas.iloc[:, 0].tolist() if not df_balsas.empty else ["-"]
                v_balsas = st.multiselect("Balsas", opt_bal)
            with c3:
                v_comandante = st.text_input("Comandante")

            # LINHA 2: Origem, Destino e Tripulação Técnica
            c4, c5, c6 = st.columns(3)
            with c4:
                # Pega a 1ª coluna da aba Rotas para Origem
                opt_origem = df_rotas.iloc[:, 0].unique().tolist() if not df_rotas.empty else ["-"]
                v_origem = st.selectbox("Origem (Local de Saída)", opt_origem)
            with c5:
                # Pega a 2ª coluna da aba Rotas para Destino (se existir)
                col_idx_dest = 1 if len(df_rotas.columns) > 1 else 0
                opt_destino = df_rotas.iloc[:, col_idx_dest].unique().tolist() if not df_rotas.empty else ["-"]
                v_destino = st.selectbox("Destino (Local de Chegada)", opt_destino)
            with c6:
                v_chefe = st.text_input("Chefe de Máquinas")

            # LINHA 3: Dados Financeiros e Operacionais
            c7, c8, c9 = st.columns(3)
            with c7:
                v_vol = st.number_input("Volume Transportado", min_value=0.0, format="%.2f")
                v_fat = st.number_input("Faturamento (R$)", min_value=0.0, format="%.2f")
            with c8:
                v_tempo = st.number_input("Tempo Previsto (Horas)", min_value=0)
                v_comb = st.number_input("Combustível Previsto (Litros)", min_value=0)
            with c9:
                v_horimetro = st.number_input("Horímetro Inicial", min_value=0.0, format="%.1f")

            st.markdown("---")
            btn_validar = st.form_submit_button("VALIDAR PLANEJAMENTO E NOTIFICAR")

        if btn_validar:
            st.success(f"Viagem {id_viagem_auto} validada: {v_origem} ➔ {v_destino}")
            
            # Botões de Ação Final
            ca1, ca2 = st.columns(2)
            ca1.button("📥 Gerar PDF do Plano")
            ca2.button("📧 Enviar para Gestoria")

else:
    st.error("Conexão interrompida. Verifique o Bloco 02.")
