import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira coisa)
st.set_page_config(page_title="ZION - PCO", layout="wide")

# 2. FUNÇÃO DE CONEXÃO REFORMULADA
@st.cache_resource
def conectar_google():
    try:
        # Pega as credenciais das Secrets
        s = st.secrets["gcp_service_account"]
        
        # O TRUQUE: Refazemos o dicionário garantindo que a chave privada
        # não tenha espaços ou quebras de linha erradas
        creds_dict = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": s["private_key"].replace("\\n", "\n"), # CORRIGE O PEM
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro Crítico de Conexão: {e}")
        return None

# 3. EXECUÇÃO
client = conectar_google()

if client:
    try:
        # ID da sua planilha (BD O.S VG)
        spreadsheet_id = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(spreadsheet_id)
        
        st.title("🚢 ZION - Sistema de Gestão PCO")
        st.success("Conectado com Sucesso!")
        
        # Menu simples para testar
        aba = st.sidebar.selectbox("Aba", ["Ativos", "Balsas", "Rotas"])
        sheet = doc.worksheet(aba)
        dados = pd.DataFrame(sheet.get_all_records())
        st.dataframe(dados)

    except Exception as e:
        st.error(f"Erro ao ler as abas: {e}. Verifique se os nomes (Ativos, Balsas, Rotas) estão certos.")
else:
    st.warning("Verifique as configurações de Secrets no painel do Streamlit.")
