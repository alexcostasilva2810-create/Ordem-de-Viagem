import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA LINHA DE CÓDIGO STREAMLIT)
st.set_page_config(page_title="ZION - PCO", layout="wide")

# 2. FUNÇÃO DE CONEXÃO
@st.cache_resource
def conectar_google():
    try:
        # Pega as credenciais direto do dicionário do Secrets
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

# 3. INICIALIZAÇÃO
client = conectar_google()

if client:
    try:
        # Abre a planilha pelo ID para evitar erro de nome
        spreadsheet_id = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(spreadsheet_id)
        
        # Seleciona as abas
        sheet_ativos = doc.worksheet("Ativos")
        sheet_balsas = doc.worksheet("Balsas")
        sheet_rotas = doc.worksheet("Rotas")
        
        st.title("🚢 ZION - Sistema de Gestão PCO")
        
        # Menu Lateral
        menu = st.sidebar.selectbox("Menu", ["Simulador", "Cadastro de Ativos", "Cadastro de Rotas"])
        
        if menu == "Simulador":
            st.header("Simulador de Operação")
            # Exemplo de leitura de dados
            df_ativos = pd.DataFrame(sheet_ativos.get_all_records())
            if not df_ativos.empty:
                st.selectbox("Selecione o Empurrador", df_ativos['Nome'].tolist())
                st.success("Dados carregados com sucesso!")
            else:
                st.warning("Aba 'Ativos' está vazia na planilha.")

        elif menu == "Cadastro de Ativos":
            st.header("Cadastrar Novo Empurrador")
            nome = st.text_input("Nome do Ativo")
            potencia = st.number_input("Potência (HP)", min_value=0)
            if st.button("Salvar"):
                sheet_ativos.append_row([nome, potencia])
                st.success(f"{nome} cadastrado com sucesso!")

    except Exception as e:
        st.error(f"Erro ao acessar planilhas: {e}")
else:
    st.warning("Aguardando configuração das Secrets no Streamlit Cloud.")
