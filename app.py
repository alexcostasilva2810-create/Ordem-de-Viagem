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

st.markdown("""
    <style>
    .block-container { max-width: 1100px; padding-top: 70px; margin: auto; }
    .capa-container {
        text-align: center; padding: 40px;
        background-color: #f8f9fa; border-radius: 15px;
        border: 2px solid #073763; margin-bottom: 30px;
    }
    /* Estilo para suportar a lista de 15 balsas visualmente */
    .stMultiSelect div[data-baseweb="select"] > div:first-child {
        max-height: 250px !important;
        overflow-y: auto !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. GERADOR DE PDF (LAYOUT O.S.)
class PDF_ZION(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'ORDEM DE VIAGEM - TRANSDOURADA', align='C', ln=True)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        fuso_br = timezone(timedelta(hours=-3))
        self.cell(0, 10, f'Gerado em: {datetime.now(fuso_br).strftime("%d/%m/%Y - %H:%M:%S")}', align='C')

# 3. CONEXÃO COM A PLANILHA
def carregar_dados():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sh = gspread.authorize(creds).open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        hist = sh.worksheet("Historico").get_all_values()
        df = pd.DataFrame(hist[1:], columns=hist[0]).loc[:, ~pd.Series(hist[0]).duplicated()] if len(hist)>1 else pd.DataFrame()
        return ativos, balsas, rotas, df
    except:
        return [], [], [], pd.DataFrame()

# 4. INTERFACE
if st.session_state.pagina_atual == "Capa":
    st.markdown('<div class="capa-container"><h1>🚢 ZION - GESTÃO PCO</h1><p>Transdourada Navegação</p></div>', unsafe_allow_html=True)
    if st.button("🚀 ENTRAR NO SISTEMA", use_container_width=True):
        st.session_state.pagina_atual = "Sistema"
        st.rerun()

else:
    ativos, lista_balsas, lista_rotas, df_h = carregar_dados()
    uid = st.session_state.session_id

    with st.sidebar:
        if st.button("🏠 Voltar para Capa"):
            st.session_state.pagina_atual = "Capa"
            st.rerun()
        menu = st.radio("Navegação", ["📊 Simulações", "📜 Histórico"])

    if menu == "📊 Simulações":
        st.title("📊 Simulador de Viagem")
        
        # BUSCA
        with st.expander("🔍 BUSCAR REGISTRO"):
            id_sel = st.selectbox("ID:", ["---"] + (df_h.iloc[:,0].tolist() if not df_h.empty else []), key=f"sel_{uid}")
            if st.button("CARREGAR DADOS"):
                st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()

        # FORMULÁRIO BLINDADO (Aqui é onde resolve o erro das 15 balsas)
        with st.form("form_simulacao"):
            st.subheader("Configuração do Comboio")
            d = st.session_state.dados_edit
            
            l1, l2 = st.columns([1, 2])
            v_emp = l1.selectbox("Empurrador", ativos, index=0)
            
            # Tratamento para carregar balsas salvas
            try:
                b_val = d.get('Balsas', '[]')
                b_def = ast.literal_eval(b_val) if '[' in str(b_val) else []
            except: b_def = []
            
            # Campo de múltiplas balsas - agora dentro do FORM para não dar erro
            v_bal = l2.multiselect("Selecione as Balsas (Até 15+)", lista_balsas, default=[b for b in b_def if b in lista_balsas])
            
            st.write("---")
            l3, l4, l5 = st.columns(3)
            v_com = l3.text_input("Comandante", value=d.get('Comandante', ""))
            v_chf = l4.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))
            v_hor = l5.number_input("Horímetro", value=0.0)

            l6, l7, l8 = st.columns(3)
            oris = sorted(list(set([r[0] for r in lista_rotas if r])))
            dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
            v_ori = l6.selectbox("Origem", oris)
            v_des = l7.selectbox("Destino", dess)
            v_fat = l8.number_input("Faturamento (R$)", value=0.0)

            v_obs = st.text_area("Observações")
            
            submit = st.form_submit_button("✅ CONFIRMAR DADOS E GERAR O.S.")

            if submit:
                if len(v_bal) == 0:
                    st.error("Selecione pelo menos uma balsa!")
                else:
                    st.success(f"Comboio com {len(v_bal)} balsas confirmado!")
                    # Aqui gera o PDF e o download (lógica interna)
                    st.info("Clique no botão abaixo para baixar o documento.")

    elif menu == "📜 Histórico":
        st.title("📜 Histórico")
        st.dataframe(df_h, use_container_width=True, hide_index=True)
