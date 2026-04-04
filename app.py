import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# CONFIGURAÇÃO DA PÁGINA
st.set_page_title("ZION - Sistema de Gestão PCO", layout="wide")

# 1. FUNÇÃO DE CONEXÃO (ROBUSTA)
def conectar_google():
    try:
        # Tenta ler as credenciais dos Secrets
        if "gcp_service_account" not in st.secrets:
            st.error("Erro: Secret 'gcp_service_account' não encontrada.")
            return None
            
        credentials_info = st.secrets["gcp_service_account"]
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro ao autenticar no Google: {e}")
        return None

# 2. INICIALIZAÇÃO DA CONEXÃO
client = conectar_google()

if client:
    try:
        # USA O ID DA SUA PLANILHA (Extraído da sua imagem)
        spreadsheet_id = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(spreadsheet_id)
        
        # Acessando as abas
        sheet_ativos = doc.worksheet("Ativos")
        sheet_balsas = doc.worksheet("Balsas")
        sheet_rotas = doc.worksheet("Rotas")
        sheet_simulacoes = doc.worksheet("Simulacoes")
        
    except Exception as e:
        st.error(f"Erro ao abrir planilhas: {e}. Verifique se o e-mail do robô é EDITOR da planilha.")
        st.stop()
else:
    st.stop()

# 3. INTERFACE DO SISTEMA
st.title("🚢 ZION - Simulador de Operação")

menu = st.sidebar.selectbox("Navegação", ["Simulador", "Cadastrar Ativos", "Cadastrar Rotas"])

if menu == "Simulador":
    st.subheader("Nova Simulação")
    # Busca dados das abas para os selects
    ativos_data = pd.DataFrame(sheet_ativos.get_all_records())
    
    if not ativos_data.empty:
        empurrador = st.selectbox("Selecione o Empurrador", ativos_data['Nome'].tolist())
        st.success(f"Empurrador {empurrador} selecionado!")
    else:
        st.warning("Nenhum empurrador cadastrado na planilha.")

elif menu == "Cadastrar Ativos":
    st.subheader("Cadastro de Empurradores")
    nome = st.text_input("Nome do Ativo")
    potencia = st.number_input("Potência (HP)", min_value=0)
    
    if st.button("Salvar no Google Sheets"):
        sheet_ativos.append_row([nome, potencia])
        st.success("Cadastrado com sucesso!")
