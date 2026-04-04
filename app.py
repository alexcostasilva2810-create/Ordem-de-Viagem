import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="ZION - Sistema de Gestão PCO", layout="wide")

@st.cache_resource
def conectar_google():
    try:
        # Pega o dicionário dos Secrets
        if "gcp_service_account" not in st.secrets:
            st.error("Erro: 'gcp_service_account' não configurado nos Secrets.")
            return None
            
        s = st.secrets["gcp_service_account"]
        
        # --- LIMPEZA RADICAL DA CHAVE ---
        pk = s["private_key"]
        
        # 1. Se a chave estiver com \n literais, converte para quebras de linha reais
        pk = pk.replace("\\n", "\n")
        
        # 2. Remove espaços em branco extras que podem ter vindo no copiar/colar
        pk = pk.strip()
        
        # 3. Reconstrói o dicionário para garantir que está limpo
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
        st.error(f"Erro Crítico de Conexão: {e}")
        return None

# --- INÍCIO DO APP ---
st.title("🚢 ZION - Gestão PCO Online")

client = conectar_google()

if client:
    try:
        # ID da planilha (pegue da URL da sua planilha)
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        doc = client.open_by_key(ID_PLANILHA)
        
        st.success("✅ Conectado com sucesso!")
        
        # Menu de abas
        abas = [w.title for w in doc.worksheets()]
        aba_selecionada = st.selectbox("Selecione a Tabela", abas)
        
        sheet = doc.worksheet(aba_selecionada)
        dados = pd.DataFrame(sheet.get_all_records())
        
        if not dados.empty:
            st.dataframe(dados, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado nesta aba.")
            
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
else:
    st.info("Aguardando configuração correta dos Secrets.")
