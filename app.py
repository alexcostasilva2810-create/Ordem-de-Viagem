import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="ZION - PCO", layout="wide")

@st.cache_resource
def conectar_google():
    try:
        s = st.secrets["gcp_service_account"]
        
        # Limpeza pesada para evitar o erro de PEM/Padding
        pk = s["private_key"]
        if "\\n" in pk:
            pk = pk.replace("\\n", "\n")
            
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
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro: {e}")
        return None

st.title("🚢 Sistema ZION")
client = conectar_google()

if client:
    try:
        doc = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        st.success("✅ FUNCIONOU! Sistema online.")
        # Resto do seu código aqui...
    except Exception as e:
        st.error(f"Erro ao abrir planilha: {e}")
