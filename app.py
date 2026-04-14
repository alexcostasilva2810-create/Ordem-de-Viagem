import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast
import uuid

# 1. CONFIGURAÇÃO E DESIGN
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = "Capa"
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}
if 'session_id' not in st.session_state: st.session_state.session_id = str(uuid.uuid4())

# 2. CACHE PARA EVITAR ERRO DE QUOTA (BLOQUEIO DO GOOGLE)
@st.cache_data(ttl=600)  # Atualiza os dados a cada 10 minutos
def carregar_dados_cache():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sh = gspread.authorize(creds).open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        
        # Carrega histórico e remove colunas duplicadas ou vazias
        hist_raw = sh.worksheet("Historico").get_all_values()
        if len(hist_raw) > 1:
            df = pd.DataFrame(hist_raw[1:], columns=hist_raw[0])
            df = df.loc[:, ~df.columns.duplicated()].copy()
        else:
            df = pd.DataFrame()
            
        return ativos, balsas, rotas, df
    except Exception as e:
        return [], [], [], pd.DataFrame()

# 3. INTERFACE
if st.session_state.pagina_atual == "Capa":
    st.markdown("<h1 style='text-align: center;'>🚢 ZION - GESTÃO PCO</h1>", unsafe_allow_html=True)
    if st.button("🚀 ENTRAR NO SISTEMA", use_container_width=True):
        st.session_state.pagina_atual = "Sistema"
        st.rerun()

else:
    ativos, lista_balsas, lista_rotas, df_h = carregar_dados_cache()
    uid = st.session_state.session_id

    with st.sidebar:
        st.title("MENU")
        if st.button("🏠 Voltar para Capa"):
            st.session_state.pagina_atual = "Capa"
            st.rerun()
        menu = st.radio("Selecione:", ["📊 Simulações", "📜 Histórico"])

    if menu == "📊 Simulações":
        st.title("📊 Simulador de Viagem")
        
        # FORMULÁRIO COM PROTEÇÃO DE ESTADO
        with st.form("meu_form_blindado"):
            st.subheader("Configuração de Comboio (12-15 Balsas)")
            
            col1, col2 = st.columns([1, 2])
            emp = col1.selectbox("Empurrador", ativos)
            # O multiselect dentro do form não dispara o erro de quota a cada clique
            balsas_sel = col2.multiselect("Balsas do Comboio", lista_balsas)
            
            st.write("---")
            c1, c2, c3 = st.columns(3)
            comandante = c1.text_input("Comandante")
            chefe = c2.text_input("Chefe de Máquinas")
            horimetro = c3.number_input("Horímetro", step=0.1)
            
            f1, f2, f3 = st.columns(3)
            ori = f1.selectbox("Origem", sorted(list(set([r[0] for r in lista_rotas if r]))))
            des = f2.selectbox("Destino", sorted(list(set([r[1] for r in lista_rotas if len(r)>1]))))
            faturamento = f3.number_input("Faturamento (R$)", format="%.2f")
            
            btn_confirmar = st.form_submit_button("✅ SALVAR E GERAR O.S.")
            
            if btn_confirmar:
                if not balsas_sel:
                    st.warning("Selecione as balsas antes de finalizar.")
                else:
                    st.success(f"Comboio com {len(balsas_sel)} balsas registrado com sucesso!")

    elif menu == "📜 Histórico":
        st.title("📜 Histórico de Viagens")
        if not df_h.empty:
            st.dataframe(df_h, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhum dado encontrado no histórico.")
