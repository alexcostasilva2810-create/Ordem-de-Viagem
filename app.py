import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. Configuração da Página (Sempre no topo)
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

@st.cache_resource
def conectar_google():
    """
    Conecta ao Google Sheets tratando a chave privada 
    para evitar erros de 'InvalidPadding' ou 'InvalidByte'.
    """
    try:
        # Puxa o dicionário das Secrets
        if "gcp_service_account" not in st.secrets:
            st.error("Erro: Configure as 'Secrets' no painel do Streamlit Cloud.")
            return None
            
        s = st.secrets["gcp_service_account"]
        
        # --- TRATAMENTO DA CHAVE ---
        # Remove espaços extras e garante que as quebras de linha sejam reais
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
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
        
    except Exception as e:
        st.error(f"Erro na Autenticação: {e}")
        return None

# --- INTERFACE ---
st.title("🚢 ZION - Gestão PCO Online")

client = conectar_google()

if client:
    try:
        # ID da sua planilha (Extraído dos seus prints)
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(ID_PLANILHA)
        
        st.success("✅ Conectado com sucesso!")
        
        # Navegação por abas da planilha
        abas = [w.title for w in doc.worksheets()]
        aba_selecionada = st.sidebar.selectbox("Selecione a Tabela", abas)
        
        # Carregar e exibir os dados
        sheet = doc.worksheet(aba_selecionada)
        df = pd.DataFrame(sheet.get_all_records())
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("A aba selecionada está vazia.")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
else:
    st.info("Aguardando configuração correta dos segredos.")
