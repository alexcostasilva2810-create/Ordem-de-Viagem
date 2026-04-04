import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Interface
st.title("🚢 Sistema ZION - PCO")

@st.cache_resource
def conectar_google():
    try:
        # Puxa o dicionário completo do Secrets
        info = st.secrets["gcp_service_account"]
        
        # O segredo: transforma o texto '\n' em quebras de linha reais
        info_dict = dict(info)
        info_dict["private_key"] = info_dict["private_key"].replace("\\n", "\n")
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro na Autenticação: {e}")
        return None

client = conectar_google()

if client:
    try:
        # ID da sua planilha (pelo que vi nos prints anteriores)
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(ID_PLANILHA)
        st.success("✅ CONECTADO COM SUCESSO!")
        
        # Mostra os dados
        sheet = doc.get_worksheet(0)
        df = pd.DataFrame(sheet.get_all_records())
        st.dataframe(df)
    except Exception as e:
        st.error(f"Erro ao ler dados: {e}")
