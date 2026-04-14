import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast
import time

# 1. CONFIGURAÇÃO E RESPIRO DE 2CM
st.set_page_config(page_title="ZION - SISTEMA PCO", layout="wide")

st.markdown("""
    <style>
    .block-container { max-width: 1100px; padding-top: 75px; margin: auto; }
    .stMultiSelect div[data-baseweb="select"] > div:first-child { max-height: 200px; overflow-y: auto; }
    .stButton > button { background-color: #073763; color: white; height: 3em; width: 100%; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. FUNÇÃO DE CARREGAMENTO ÚNICO (EVITA ERRO 429 QUOTA)
@st.cache_data(ttl=600)
def carregar_dados_estaticos():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        hist_raw = sh.worksheet("Historico").get_all_values()
        
        df_h = pd.DataFrame(hist_raw[1:], columns=hist_raw[0])
        df_h = df_h.loc[:, ~df_h.columns.duplicated()].copy()
        
        return ativos, balsas, rotas, df_h
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return [], [], [], pd.DataFrame()

# 3. GERADOR DE PDF
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "ORDEM DE SERVIÇO - TRANSDOURADA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    for k, v in dados.items():
        pdf.cell(50, 8, f"{k}:", border=1)
        pdf.cell(0, 8, f" {v}", border=1, ln=True)
    return pdf.output(dest="S").encode("latin-1")

# 4. LÓGICA DE TELAS
if 'tela' not in st.session_state: st.session_state.tela = "Capa"
if 'dados_edicao' not in st.session_state: st.session_state.dados_edicao = {}

ativos, lista_balsas, lista_rotas, df_historico = carregar_dados_estaticos()

if st.session_state.tela == "Capa":
    st.markdown("<h1 style='text-align:center;'>🚢 ZION - GESTÃO PCO</h1>", unsafe_allow_html=True)
    if st.button("🚀 ENTRAR NO SISTEMA"):
        st.session_state.tela = "Sistema"
        st.rerun()

else:
    with st.sidebar:
        if st.button("🏠 Voltar para Capa"):
            st.session_state.tela = "Capa"
            st.rerun()
        opcao = st.radio("Menu", ["📊 Simulação", "📜 Histórico"])

    if opcao == "📊 Simulação":
        st.title("📊 Nova Simulação")
        
        # BUSCA SEM BUG
        with st.expander("🔍 Recuperar Viagem Anterior"):
            id_busca = st.selectbox("Selecione ID:", ["---"] + (df_historico.iloc[:,0].tolist() if not df_historico.empty else []))
            if st.button("Carregar Dados"):
                st.session_state.dados_edicao = df_historico[df_historico.iloc[:, 0] == id_busca].iloc[0].to_dict()
                st.rerun()

        # FORMULÁRIO QUE AGUENTA 15 BALSAS
        with st.form("form_viagem"):
            d = st.session_state.dados_edicao
            c1, c2 = st.columns([1, 2])
            emp = c1.selectbox("Empurrador", ativos)
            
            # Tratamento para as 15 balsas
            try:
                b_salvas = ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else []
            except: b_salvas = []
            
            bal = c2.multiselect("Selecione o Comboio (Até 15+)", lista_balsas, default=[b for b in b_salvas if b in lista_balsas])
            
            st.write("---")
            c3, c4, c5 = st.columns(3)
            com = c3.text_input("Comandante", value=d.get('Comandante', ""))
            chf = c4.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))
            fat = c5.number_input("Faturamento (R$)", value=0.0)
            
            submit = st.form_submit_button("✅ SALVAR E GERAR O.S.")
            
            if submit:
                if not bal:
                    st.error("Selecione o comboio!")
                else:
                    status = "APROVADO" if fat >= 50000 else "ANÁLISE"
                    dados_os = {"ID": "NOVO", "Empurrador": emp, "Comboio": ", ".join(bal), "Faturamento": f"R$ {fat:,.2f}", "Status": status}
                    pdf_bytes = gerar_pdf(dados_os)
                    st.success(f"Comboio de {len(bal)} balsas pronto!")
                    st.download_button("📥 BAIXAR O.S. EM PDF", pdf_bytes, "Ordem_Servico.pdf", "application/pdf")

    elif opcao == "📜 Histórico":
        st.title("📜 Histórico")
        st.dataframe(df_historico, use_container_width=True, hide_index=True)
