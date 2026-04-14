import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast
import uuid  # Para garantir que cada ID seja único e nunca dê erro

# =========================================================
# 1. CONFIGURAÇÃO E DESIGN (2CM DE ESPAÇO)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = "Capa"
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}
# Chave única para resetar os campos se necessário
if 'session_id' not in st.session_state: st.session_state.session_id = str(uuid.uuid4())

st.markdown("""
    <style>
    .block-container { max-width: 1150px; padding-top: 75px; margin: auto; }
    .capa-container {
        text-align: center; padding: 50px;
        background-color: #f8f9fa; border-radius: 20px;
        border: 2px solid #073763; margin-bottom: 40px;
    }
    /* Suporte visual para muitas balsas */
    div[data-baseweb="select"] > div:first-child { 
        max-height: 200px !important; 
        overflow-y: auto !important; 
    }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. PDF E CONEXÃO (LÓGICA ESTÁVEL)
# =========================================================
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

def carregar_dados_seguros():
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

# =========================================================
# 3. INTERFACE PRINCIPAL
# =========================================================

if st.session_state.pagina_atual == "Capa":
    st.markdown('<div class="capa-container"><h1>🚢 ZION - GESTÃO PCO</h1><p>Transdourada Navegação</p></div>', unsafe_allow_html=True)
    if st.button("🚀 ENTRAR NO SISTEMA"):
        st.session_state.pagina_atual = "Sistema"
        st.rerun()

else:
    ativos, lista_balsas, lista_rotas, df_h = carregar_dados_seguros()

    with st.sidebar:
        if st.button("🏠 Voltar para Capa"):
            st.session_state.pagina_atual = "Capa"
            st.rerun()
        menu = st.radio("Selecione:", ["📊 Simulações", "📜 Histórico"])

    if menu == "📊 Simulações":
        st.title("📊 Simulação de Viagem")
        
        # BUSCA COM KEY ÚNICA
        with st.expander("🔍 BUSCAR REGISTRO"):
            id_sel = st.selectbox("Escolha ID:", ["---"] + (df_h.iloc[:,0].tolist() if not df_h.empty else []), key="busca_id_v2")
            if st.button("CARREGAR"):
                st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
                st.session_state.session_id = str(uuid.uuid4()) # Reseta IDs para evitar erro
                st.rerun()

        d = st.session_state.dados_edit
        uid = st.session_state.session_id

        # --- GRID 4X3 ---
        l1, l2, l3 = st.columns(3)
        v_emp = l1.selectbox("Empurrador", ativos, index=0, key=f"emp_{uid}")
        
        # COMBOIO DE 15 BALSAS (Processamento Seguro)
        try:
            b_val = d.get('Balsas', '[]')
            b_def = ast.literal_eval(b_val) if '[' in str(b_val) else []
        except: b_def = []
        
        v_bal = l2.multiselect("Comboio de Balsas (Até 15+)", lista_balsas, default=[b for b in b_def if b in lista_balsas], key=f"bal_{uid}")
        v_com = l3.text_input("Comandante", value=d.get('Comandante', ""), key=f"com_{uid}")

        l4, l5, l6 = st.columns(3)
        oris = sorted(list(set([r[0] for r in lista_rotas if r])))
        dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
        v_ori = l4.selectbox("Origem", oris, key=f"ori_{uid}")
        v_des = l5.selectbox("Destino", dess, key=f"des_{uid}")
        v_chf = l6.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""), key=f"chf_{uid}")

        l7, l8, l9 = st.columns(3)
        v_vol = l7.number_input("Volume (M³)", value=0.0, key=f"vol_{uid}")
        v_fat = l8.number_input("Faturamento (R$)", value=0.0, key=f"fat_{uid}")
        v_hor = l9.number_input("Horímetro", value=0.0, key=f"hor_{uid}")

        if st.button("✅ FINALIZAR E GERAR O.S."):
            pdf_data = {"ID": "NOVO", "Empurrador": v_emp, "Comboio": ", ".join(v_bal), "Rota": f"{v_ori} x {v_des}", "Faturamento": f"R$ {v_fat:,.2f}"}
            pdf_bytes = PDF_ZION().output(dest="S").encode("latin-1") # Simplificado para teste
            st.success(f"Comboio de {len(v_bal)} balsas processado!")
            st.download_button("📥 BAIXAR O.S.", pdf_bytes, "OS.pdf", "application/pdf")

    elif menu == "📜 Histórico":
        st.title("📜 Histórico")
        st.dataframe(df_h, use_container_width=True, hide_index=True)
