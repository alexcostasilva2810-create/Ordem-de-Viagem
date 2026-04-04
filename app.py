import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Primeira linha sempre
st.set_page_config(page_title="ZION - PCO", layout="wide")

@st.cache_resource
def conectar_google():
    try:
        # Puxa o dicionário do TOML
        creds_dict = st.secrets["gcp_service_account"]
        
        # Define os escopos
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Cria a credencial diretamente (o formato do segredo agora está perfeito)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro na Conexão: {e}")
        return None

# Interface
st.title("🚢 Sistema ZION - PCO")

client = conectar_google()

if client:
    try:
        spreadsheet_id = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(spreadsheet_id)
        st.success("✅ Conectado à Planilha!")
        
        # Mostra os dados da primeira aba como teste
        sheet = doc.get_worksheet(0)
        df = pd.DataFrame(sheet.get_all_records())
        st.dataframe(df)
        
    except Exception as e:
        st.error(f"Erro ao abrir planilha: {e}")
