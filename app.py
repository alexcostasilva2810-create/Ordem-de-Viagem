import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# ==========================================
# # 01 - CONFIGURAÇÕES GERAIS #
# ==========================================
st.set_page_config(
    page_title="ZION - Gestão PCO",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# # 02 - CONEXÃO E SEGURANÇA (SECRETS) #
# ==========================================
@st.cache_resource
def conectar_google():
    try:
        s = st.secrets["gcp_service_account"]
        # Limpa a chave privada de caracteres invisíveis
        pk = s["private_key"].strip().replace("\\n", "\n")
        
        creds_dict = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": pk,
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro no Bloco # 02: {e}")
        return None

# ==========================================
# # 03 - MOTOR DE BUSCA DE DADOS #
# ==========================================
def buscar_dados(client, nome_aba):
    try:
        # ID da sua planilha Google
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        sh = client.open_by_key(ID_PLANILHA)
        worksheet = sh.worksheet(nome_aba)
        dados = worksheet.get_all_values()
        if len(dados) > 1:
            return pd.DataFrame(dados[1:], columns=dados[0])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro no Bloco # 03 (Aba {nome_aba}): {e}")
        return pd.DataFrame()

# ==========================================
# # MAIN APP - EXECUÇÃO #
# ==========================================
st.title("🚢 ZION - Gestão PCO Online")
st.markdown("---")

client = conectar_google()

if client:
    # ==========================================
    # # 04 - INTERFACE DE NAVEGAÇÃO (TABS) #
    # ==========================================
    t_ativos, t_balsas, t_trip, t_rotas, t_sim = st.tabs([
        "📋 Ativos", 
        "⛴️ Balsas", 
        "👥 Tripulação", 
        "📍 Rotas", 
        "📊 Simulações"
    ])

    # ==========================================
    # # 05 - BLOCO: ATIVOS #
    # ==========================================
    with t_ativos:
        st.subheader("Gerenciamento de Ativos")
        df_ativos = buscar_dados(client, "Ativos")
        if not df_ativos.empty:
            st.dataframe(df_ativos, use_container_width=True, hide_index=True)
        else:
            st.info("Aba 'Ativos' sem dados ou não encontrada.")

    # ==========================================
    # # 06 - BLOCO: BALSAS #
    # ==========================================
    with t_balsas:
        st.subheader("Frota de Balsas")
        df_balsas = buscar_dados(client, "Balsas")
        if not df_balsas.empty:
            st.dataframe(df_balsas, use_container_width=True, hide_index=True)
        else:
            st.info("Aba 'Balsas' sem dados ou não encontrada.")

    # ==========================================
    # # 07 - BLOCO: TRIPULAÇÃO #
    # ==========================================
    with t_trip:
        st.subheader("Controle de Tripulação")
        df_trip = buscar_dados(client, "Tripulação")
        if not df_trip.empty:
            st.dataframe(df_trip, use_container_width=True, hide_index=True)
        else:
            st.info("Aba 'Tripulação' sem dados ou não encontrada.")

    # ==========================================
    # # 08 - BLOCO: ROTAS #
    # ==========================================
    with t_rotas:
        st.subheader("Logística de Rotas")
        df_rotas = buscar_dados(client, "Rotas")
        if not df_rotas.empty:
            st.dataframe(df_rotas, use_container_width=True, hide_index=True)
        else:
            st.info("Aba 'Rotas' sem dados ou não encontrada.")

    # ==========================================
    # # 09 - BLOCO: SIMULAÇÕES #
    # ==========================================
    with t_sim:
        st.subheader("Simulador de Operações")
        df_sim = buscar_dados(client, "Simulacoes")
        if not df_sim.empty:
            st.dataframe(df_sim, use_container_width=True, hide_index=True)
        else:
            st.info("Aba 'Simulacoes' sem dados ou não encontrada.")

else:
    st.warning("Aguardando conexão com o banco de dados (Bloco # 02).")
