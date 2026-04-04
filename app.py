import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="ZION - Sistema de Gestão PCO", layout="wide")

# 2. FUNÇÃO DE CONEXÃO AO GOOGLE
def conectar_google():
    try:
        # Pega o texto do JSON que salvamos no Secrets e transforma em dicionário
        creds_json = st.secrets["gcp_service_account"]["gcp_json"]
        creds_dict = json.loads(creds_json)
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro na conexão com o Google: {e}")
        return None

# 3. INICIALIZAÇÃO DA CONEXÃO
client = conectar_google()

if client:
    try:
        # ID da sua planilha (BD O.S VG)
        spreadsheet_id = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(spreadsheet_id)
        
        # Carregando as abas
        sheet_ativos = doc.worksheet("Ativos")
        
        st.title("🚢 ZION - Sistema Online")
        st.success("Conectado com sucesso à planilha!")
        
        # Mostrar dados para testar
        dados = pd.DataFrame(sheet_ativos.get_all_records())
        st.dataframe(dados)

    except Exception as e:
        st.error(f"Erro ao abrir a planilha: {e}")
else:
    st.error("Verifique os Secrets no painel do Streamlit.")
