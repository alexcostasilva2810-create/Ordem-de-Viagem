import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. ESSENCIAL: Configuração da página primeiro
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

@st.cache_resource
def conectar_google():
    try:
        # Puxa o dicionário completo do segredo
        info = st.secrets["gcp_service_account"]
        
        # Cria as credenciais (O Streamlit já entende o \n dentro de aspas simples)
        creds = Credentials.from_service_account_info(info, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro Crítico: {e}")
        return None

# EXECUÇÃO PRINCIPAL
st.title("🚢 Sistema Operacional - ZION")

client = conectar_google()

if client:
    try:
        # ID da sua planilha
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(ID_PLANILHA)
        
        st.success("✅ Conexão estabelecida com sucesso!")
        
        # Menu para navegar entre as abas
        aba_selecionada = st.selectbox("Selecione a Aba", ["Ativos", "Balsas", "Equipe", "Rotas"])
        
        sheet = doc.worksheet(aba_selecionada)
        dados = pd.DataFrame(sheet.get_all_records())
        st.dataframe(dados)
        
    except Exception as e:
        st.error(f"Conectado ao Google, mas erro na Planilha: {e}")
else:
    st.info("Configure os Secrets no menu do Streamlit para ativar o sistema.")
