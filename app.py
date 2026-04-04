import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. Configuração da Página (Sempre a primeira linha de código)
st.set_page_config(page_title="ZION - Sistema PCO", layout="wide")

@st.cache_resource
def conectar_google():
    try:
        # Puxa as informações que você colou no campo 'Secrets' do Streamlit Cloud
        if "gcp_service_account" not in st.secrets:
            st.error("Erro: Você ainda não configurou as 'Secrets' no painel do Streamlit.")
            return None
            
        s = st.secrets["gcp_service_account"]
        
        # --- TRATAMENTO DE LIMPEZA DA CHAVE ---
        # Isso remove espaços e transforma o texto '\n' em quebras de linha reais.
        # É aqui que matamos o erro de 'Invalid Padding' ou 'Invalid Byte'.
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
        
        # Define o que o app pode fazer (Ler planilhas e arquivos do Drive)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
        
    except Exception as e:
        st.error(f"Erro na Autenticação (Verifique sua chave): {e}")
        return None

# --- INTERFACE DO DASHBOARD ---
st.title("🚢 ZION - Gestão PCO Online")
st.markdown("---")

client = conectar_google()

if client:
    try:
        # ID da sua planilha (Extraído da sua URL do Google Sheets)
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(ID_PLANILHA)
        
        st.success("✅ Conexão estabelecida com sucesso!")
        
        # Sidebar para escolher a aba (Trabalho, Materiais, etc)
        abas = [w.title for w in doc.worksheets()]
        aba_selecionada = st.sidebar.selectbox("Selecione a Tabela", abas)
        
        # Carregando os dados da aba escolhida
        sheet = doc.worksheet(aba_selecionada)
        dados = sheet.get_all_records()
        
        if dados:
            df = pd.DataFrame(dados)
            # Mostra a tabela na tela ocupando a largura total
            st.dataframe(df, use_container_width=True)
            
            # Pequeno resumo abaixo da tabela
            st.info(f"Exibindo {len(df)} linhas da aba '{aba_selecionada}'.")
        else:
            st.warning("Esta aba parece estar vazia.")
            
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        st.info("Dica: Verifique se o e-mail da conta de serviço tem permissão de Editor na planilha.")
else:
    st.warning("Aguardando a configuração correta das credenciais no painel do Streamlit.")
