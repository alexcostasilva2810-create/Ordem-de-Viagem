import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser sempre a primeira linha)
st.set_page_config(page_title="ZION - Sistema de Gestão PCO", layout="wide")

@st.cache_resource
def conectar_google():
    """
    Função para conectar ao Google Sheets usando as Secrets do Streamlit.
    Inclui limpeza automática da chave privada para evitar erros de Padding/PEM.
    """
    try:
        # Carrega o dicionário das Secrets
        if "gcp_service_account" not in st.secrets:
            st.error("Erro: A chave 'gcp_service_account' não foi encontrada nos Secrets.")
            return None
            
        s = st.secrets["gcp_service_account"]
        
        # --- LIMPEZA DA CHAVE PRIVADA ---
        # Remove espaços em branco e garante que os \n sejam quebras de linha reais
        pk = s["private_key"].strip()
        pk = pk.replace("\\n", "\n")
        
        # Garante o cabeçalho e rodapé corretos da chave PEM
        if not pk.startswith("-----BEGIN PRIVATE KEY-----"):
            pk = "-----BEGIN PRIVATE KEY-----\n" + pk
        if not pk.endswith("-----END PRIVATE KEY-----"):
            pk = pk + "\n-----END PRIVATE KEY-----"

        # Monta o dicionário de credenciais exatamente como o Google exige
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
        
        # Escopos necessários para ler e escrever em planilhas e drive
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
        
    except Exception as e:
        st.error(f"Erro Crítico na Conexão: {e}")
        return None

# --- INTERFACE DO USUÁRIO ---
st.title("🚢 ZION - Gestão PCO Online")

client = conectar_google()

if client:
    try:
        # ID DA SUA PLANILHA (Retirado dos seus prints anteriores)
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(ID_PLANILHA)
        
        st.success("✅ Sistema conectado à Planilha Google!")
        
        # Sidebar para navegação
        menu = st.sidebar.selectbox("Navegação", ["Visualizar Dados", "Simulador", "Cadastro"])
        
        # Listar todas as abas disponíveis na planilha para facilitar
        abas_disponiveis = [w.title for w in doc.worksheets()]
        aba_selecionada = st.sidebar.selectbox("Selecione a Aba", abas_disponiveis)
        
        if menu == "Visualizar Dados":
            st.subheader(f"Dados da Aba: {aba_selecionada}")
            sheet = doc.worksheet(aba_selecionada)
            dados = pd.DataFrame(sheet.get_all_records())
            
            if not dados.empty:
                st.dataframe(dados, use_container_width=True)
            else:
                st.info("Esta aba está vazia.")
                
        elif menu == "Cadastro":
            st.subheader("Cadastro de Ativos")
            with st.form("form_cadastro"):
                nome_ativo = st.text_input("Nome do Empurrador/Balsa")
                status = st.selectbox("Status", ["Operacional", "Manutenção", "Parado"])
                enviar = st.form_submit_button("Salvar na Planilha")
                
                if enviar:
                    sheet = doc.worksheet("Ativos") # Certifique-se que existe essa aba
                    sheet.append_row([nome_ativo, status])
                    st.success("Dados salvos!")

    except Exception as e:
        st.error(f"Conectado ao Google, mas houve um erro ao ler os dados: {e}")
else:
    st.info("Aguardando configuração das Secrets no painel do Streamlit Cloud.")
