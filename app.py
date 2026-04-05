import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ==========================================
# # 01 - CONFIGURAÇÕES GERAIS E ESTILO #
# ==========================================
st.set_page_config(page_title="ZION - PCO", layout="wide")

# CSS para fixar largura de 5cm (190px) e compactar linhas
st.markdown("""
    <style>
    /* Compacta o container principal */
    .block-container {padding-top: 1rem; padding-left: 2rem;}
    
    /* Força a largura de aproximadamente 5cm em todos os campos de entrada */
    div[data-testid="stSelectbox"], 
    div[data-testid="stTextInput"], 
    div[data-testid="stNumberInput"], 
    div[data-testid="stMultiSelect"],
    .stButton > button {
        width: 190px !important;
    }

    /* Aproxima as linhas verticalmente */
    div.row-widget.stHorizontal { gap: 1rem; }
    div[data-testid="stForm"] { border: none; padding: 0; }
    
    /* Ajuste de labels */
    label { font-size: 13px !important; font-weight: bold; }
    
    /* Remove espaços extras entre colunas e widgets */
    [data-testid="column"] { width: auto !important; flex: none !important; }
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
    df_ativos = buscar_dados(client, "Ativos")
    df_balsas = buscar_dados(client, "Balsas")
    df_trip   = buscar_dados(client, "Tripulação")
    df_rotas  = buscar_dados(client, "Rotas")

    t_ativos, t_balsas, t_trip, t_rotas, t_sim = st.tabs([
        "📋 Ativos", "⛴️ Balsas", "👥 Tripulação", "📍 Rotas", "📊 Simulações"
    ])

    with t_ativos: st.dataframe(df_ativos, use_container_width=True, hide_index=True)
    with t_balsas: st.dataframe(df_balsas, use_container_width=True, hide_index=True)
    with t_trip:   st.dataframe(df_trip, use_container_width=True, hide_index=True)
    with t_rotas:  st.dataframe(df_rotas, use_container_width=True, hide_index=True)

    # ==========================================
    # # 09 - BLOCO: SIMULAÇÕES (COMPACTO 5CM) #
    # ==========================================
    with t_sim:
        id_viagem_auto = datetime.now().strftime("VGN-%Y%m%d-%H%M")
        st.subheader(f"🚀 Planejamento: {id_viagem_auto}")
        
        with st.form("form_pco_final"):
            # Linha 1
            c1, c2, c3 = st.columns(3)
            with c1:
                opt_emp = df_ativos.iloc[:, 0].tolist() if not df_ativos.empty else ["-"]
                v_empurrador = st.selectbox("Empurrador", opt_emp)
            with c2:
                opt_bal = df_balsas.iloc[:, 0].tolist() if not df_balsas.empty else ["-"]
                v_balsas = st.multiselect("Balsas", opt_bal)
            with c3:
                v_comandante = st.text_input("Comandante")

            # Linha 2
            c4, c5, c6 = st.columns(3)
            with c4:
                opt_origem = df_rotas.iloc[:, 0].unique().tolist() if not df_rotas.empty else ["-"]
                v_origem = st.selectbox("Origem", opt_origem)
            with c5:
                col_dest = 1 if len(df_rotas.columns) > 1 else 0
                opt_destino = df_rotas.iloc[:, col_dest].unique().tolist() if not df_rotas.empty else ["-"]
                v_destino = st.selectbox("Destino", opt_destino)
            with c6:
                v_chefe = st.text_input("Chefe de Máquinas")

            # Linha 3
            c7, c8, c9 = st.columns(3)
            with c7:
                v_vol = st.number_input("Volume", min_value=0.0)
            with c8:
                v_fat = st.number_input("Faturamento (R$)", min_value=0.0)
            with c9:
                v_horimetro = st.number_input("Horímetro", min_value=0.0)

            # Linha 4
            c10, c11 = st.columns(2)
            with c10:
                v_tempo = st.number_input("Tempo (Horas)", min_value=0)
            with c11:
                v_comb = st.number_input("Combustível (L)", min_value=0)

            st.markdown("---")
            btn_validar = st.form_submit_button("VALIDAR PLANEJAMENTO")

        if btn_validar:
            st.success(f"Viagem {id_viagem_auto} registrada!")
            ca1, ca2 = st.columns(2)
            ca1.button("📥 Gerar PDF")
            ca2.button("📧 Enviar E-mail")
else:
    st.error("Erro na conexão.")
