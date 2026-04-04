import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Correto)
st.set_page_config(page_title="ZION - Sistema de Gestão PCO", layout="wide")

# 2. FUNÇÃO DE CONEXÃO AO GOOGLE
def conectar_google():
    try:
        # Pega as credenciais salvas nos Secrets
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro na conexão com o Google: {e}")
        return None

# 3. INICIALIZAÇÃO DA CONEXÃO
client = conectar_google()

if client:
    try:
        # Abertura da Planilha pelo ID (Infalível)
        spreadsheet_id = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(spreadsheet_id)
        
        # Carregando as abas
        sheet_ativos = doc.worksheet("Ativos")
        sheet_balsas = doc.worksheet("Balsas")
        sheet_rotas = doc.worksheet("Rotas")
        sheet_simulacoes = doc.worksheet("Simulacoes")
        
        # 4. INTERFACE DO SISTEMA
        st.title("🚢 ZION - Simulador de Operação PCO")
        
        menu = st.sidebar.selectbox("Navegação", ["Simulador", "Cadastrar Ativos", "Cadastrar Rotas"])

        if menu == "Simulador":
            st.subheader("Configurar Nova Simulação")
            ativos = sheet_ativos.get_all_records()
            df_ativos = pd.DataFrame(ativos)
            
            if not df_ativos.empty:
                empurrador = st.selectbox("Selecione o Empurrador", df_ativos['Nome'].tolist())
                st.write(f"Empurrador selecionado: {empurrador}")
            else:
                st.warning("Nenhum ativo encontrado.")

        elif menu == "Cadastrar Ativos":
            st.subheader("Cadastro de Ativos")
            nome = st.text_input("Nome do Empurrador")
            potencia = st.number_input("Potência (HP)")
            if st.button("Salvar no Sheets"):
                sheet_ativos.append_row([nome, potencia])
                st.success("Salvo com sucesso!")

    except Exception as e:
        st.error(f"Erro ao acessar as abas da planilha: {e}")
        st.write("Verifique se os nomes das abas na planilha estão exatamente: Ativos, Balsas, Rotas, Simulacoes")
else:
    st.error("Não foi possível conectar. Verifique seus Secrets.")
