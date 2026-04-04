import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

def conectar_google():
    try:
        s = st.secrets["gcp_service_account"]
        
        # Isso aqui limpa espaços invisíveis e garante que o \n seja real
        pk = s["private_key"].strip()
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
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro na Autenticação: {e}")
        return None

# Interface
st.title("🚢 Sistema ZION - PCO")
client = conectar_google()

if client:
    try:
        # Tenta abrir a planilha
        doc = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        st.success("✅ CONECTADO COM A NOVA CHAVE!")
        
        # Mostra a primeira aba
        df = pd.DataFrame(doc.get_worksheet(0).get_all_records())
        st.dataframe(df)
    except Exception as e:
        st.error(f"Erro ao acessar planilha: {e}")
