import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Configuração inicial
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

@st.cache_resource
def conectar_google():
    try:
        # Puxa os dados salvos no Secrets
        s = st.secrets["gcp_service_account"]
        
        # --- TRATAMENTO DE CHOQUE NA CHAVE ---
        # Remove espaços, remove aspas extras e limpa quebras de linha
        raw_key = s["private_key"].replace('"', '').strip()
        
        # Garante que as quebras de linha sejam interpretadas corretamente
        if "-----BEGIN PRIVATE KEY-----" in raw_key:
            # Se a chave veio com \n escrito como texto, vira quebra real
            formatted_key = raw_key.replace("\\n", "\n")
        else:
            # Se estiver sem os cabeçalhos, nós adicionamos
            formatted_key = "-----BEGIN PRIVATE KEY-----\n" + raw_key + "\n-----END PRIVATE KEY-----"

        creds_dict = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": formatted_key,
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
        st.error(f"Erro na autenticação: {e}")
        return None

# Interface
st.title("🚢 ZION - Sistema PCO Online")

client = conectar_google()

if client:
    try:
        # Acesso à planilha
        spreadsheet_id = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(spreadsheet_id)
        
        st.success("✅ Conectado com sucesso!")
        
        # Seletor de abas
        abas = [w.title for w in doc.worksheets()]
        aba_foco = st.sidebar.selectbox("Selecione a Tabela", abas)
        
        # Carrega dados
        sheet = doc.worksheet(aba_foco)
        df = pd.DataFrame(sheet.get_all_records())
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha: {e}")
else:
    st.warning("Verifique suas configurações de Secrets no Streamlit Cloud.")
