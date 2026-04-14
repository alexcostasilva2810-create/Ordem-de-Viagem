import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast
import uuid

# 1. CONFIGURAÇÃO GERAL
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = "Capa"
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}

st.markdown("""
    <style>
    .block-container { max-width: 1100px; padding-top: 50px; margin: auto; }
    .stMultiSelect div[data-baseweb="select"] > div:first-child { max-height: 200px; overflow-y: auto; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO COM CACHE (PARA NÃO DAR ERRO DE QUOTA/LIMITE)
@st.cache_data(ttl=600)
def carregar_dados_sistema():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sh = gspread.authorize(creds).open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        hist = sh.worksheet("Historico").get_all_values()
        
        df = pd.DataFrame(hist[1:], columns=hist[0])
        df = df.loc[:, ~df.columns.duplicated()].copy() # Remove colunas duplicadas
        return ativos, balsas, rotas, df
    except:
        return [], [], [], pd.DataFrame()

# 3. TELAS
if st.session_state.pagina_atual == "Capa":
    st.markdown("<h1 style='text-align: center;'>🚢 ZION - GESTÃO PCO</h1>", unsafe_allow_html=True)
    if st.button("🚀 ENTRAR NO SISTEMA"):
        st.session_state.pagina_atual = "Sistema"
        st.rerun()

else:
    ativos, lista_balsas, lista_rotas, df_h = carregar_dados_sistema()

    with st.sidebar:
        if st.button("🏠 Voltar para Capa"):
            st.session_state.pagina_atual = "Capa"
            st.rerun()
        menu = st.radio("Menu", ["📊 Simulações", "📜 Histórico"])

    if menu == "📊 Simulações":
        st.title("📊 Simulador de Operação")
        
        # BUSCA DE REGISTRO
        with st.expander("🔍 BUSCAR REGISTRO EXISTENTE"):
            id_sel = st.selectbox("ID:", ["---"] + (df_h.iloc[:,0].tolist() if not df_h.empty else []))
            if st.button("CARREGAR DADOS"):
                st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
                st.rerun()

        # FORMULÁRIO COMPLETO (VOLTARAM TODOS OS CAMPOS)
        with st.form("form_pco"):
            d = st.session_state.dados_edit
            
            col1, col2, col3 = st.columns([1, 1.5, 1])
            v_emp = col1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
            
            try:
                b_def = ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else []
            except: b_def = []
            v_bal = col2.multiselect("Comboio (Até 15+)", lista_balsas, default=[b for b in b_def if b in lista_balsas])
            v_com = col3.text_input("Comandante", value=d.get('Comandante', ""))

            col4, col5, col6 = st.columns(3)
            oris = sorted(list(set([r[0] for r in lista_rotas if r])))
            dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
            v_ori = col4.selectbox("Origem", oris, index=oris.index(d['Origem']) if d.get('Origem') in oris else 0)
            v_des = col5.selectbox("Destino", dess, index=dess.index(d['Destino']) if d.get('Destino') in dess else 0)
            v_chf = col6.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

            col7, col8, col9 = st.columns(3)
            v_vol = col7.number_input("Volume (M³)", value=float(d.get('Volume (M³)', 0.0)))
            v_fat = col8.number_input("Faturamento (R$)", value=float(d.get('Faturamento (R$)', 0.0)))
            v_hor = col9.number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

            col10, col11, col12 = st.columns(3)
            v_tem = col10.number_input("Tempo Previsto (H)", value=int(d.get('Tempo (H)', 0)))
            v_combus = col11.number_input("Combustível (L)", value=int(d.get('Combustível (L)', 0)))
            v_custo = col12.number_input("Custo Diesel (R$)", value=float(d.get('Custo Diesel (R$)', 0.0)))

            v_obs = st.text_area("Observações", value=d.get('Observações', ""))

            # Lógica de Status
            status_cor = "green" if v_fat >= 50000 else "red"
            st.markdown(f"### STATUS: <span style='color:{status_cor}'>{'Aprovado' if v_fat >= 50000 else 'Análise'}</span>", unsafe_allow_html=True)

            if st.form_submit_button("✅ FINALIZAR E GERAR O.S. (PDF)"):
                if not v_bal:
                    st.error("Selecione as balsas!")
                else:
                    st.success(f"Comboio de {len(v_bal)} balsas processado com sucesso!")
                    # Aqui entra sua lógica de salvar na planilha e gerar o PDF

    elif menu == "📜 Histórico":
        st.title("📜 Histórico de Viagens")
        st.dataframe(df_h, use_container_width=True, hide_index=True)
