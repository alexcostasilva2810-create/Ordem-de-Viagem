import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E DESIGN
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = {}

st.markdown("""
    <style>
    .block-container { max-width: 1050px; padding-top: 1rem; margin: auto; }
    div[data-baseweb="select"] > div:first-child { max-height: 45px; overflow-y: auto; }
    .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 220px !important; }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.8rem; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. PDF PERSONALIZADO (FIX: DADOS COMPLETOS)
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        try: self.image('icone ZION.png', x=10, y=8, w=20)
        except: pass
        self.set_font('Arial', 'B', 14)
        self.set_text_color(7, 55, 99)
        self.cell(0, 10, 'ORDEM DE VIAGEM - TRANSDOURADA', align='C', ln=True)
        self.ln(10)

def gerar_pdf_final(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "B", 10)
    for k, v in dados.items():
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(50, 10, f" {k}", border=1, fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f" {v}", border=1, ln=True)
        pdf.set_font("Arial", "B", 10)
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# 3. BANCO DE DADOS
# =========================================================
def conectar():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=2)
def carregar_zion():
    client = conectar()
    sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
    df_h = pd.DataFrame(sh.worksheet("Historico").get_all_values())
    df_h.columns = df_h.iloc[0]; df_h = df_h[1:]
    return (sh.worksheet("Ativos").col_values(1)[1:], 
            sh.worksheet("Balsas").col_values(1)[1:], 
            sh.worksheet("Rotas").get_all_values()[1:], 
            df_h.loc[:, ~df_h.columns.duplicated()])

# =========================================================
# 4. TELA DE SIMULAÇÃO (RESTAURADA E CORRIGIDA)
# =========================================================
with st.sidebar:
    pagina = st.radio("NAVEGAÇÃO", ["📊 Simulações", "📜 Histórico"])

ativos, lista_balsas, lista_rotas, df_h = carregar_zion()

if pagina == "📊 Simulações":
    st.title("ZION - Gestão PCO")
    
    with st.expander("🔍 BUSCAR REGISTRO SALVO"):
        id_busca = st.selectbox("Selecione ID para Editar:", ["---"] + df_h.iloc[:, 0].tolist())
        if st.button("CARREGAR PARA EDIÇÃO"):
            st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_busca].iloc[0].to_dict()
            st.rerun()

    d = st.session_state.dados_edit
    v_id = d.get('ID', datetime.now().strftime("VGM %d%m-%H%M"))
    st.subheader(f"Registro: {v_id}")

    # --- LINHA 1 ---
    c1, c2, c3 = st.columns(3)
    v_emp = c1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
    try:
        b_raw = d.get('Balsas', '[]')
        b_def = ast.literal_eval(b_raw) if '[' in str(b_raw) else []
    except: b_def = []
    v_bal = c2.multiselect("Balsas", lista_balsas, default=b_def)
    v_com = c3.text_input("Comandante", value=d.get('Comandante', ""))

    # --- LINHA 2 ---
    c4, c5, c6 = st.columns(3)
    oris = sorted(list(set([r[0] for r in lista_rotas])))
    dess = sorted(list(set([r[1] for r in lista_rotas])))
    v_ori = c4.selectbox("Origem", oris, index=oris.index(d['Origem']) if d.get('Origem') in oris else 0)
    v_des = c5.selectbox("Destino", dess, index=dess.index(d['Destino']) if d.get('Destino') in dess else 0)
    v_chf = c6.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

    # --- LINHA 3 ---
    c7, c8, c9 = st.columns(3)
    v_vol = c7.number_input("Volume (M³)", value=float(str(d.get('Volume','0')).split()[0].replace(',','.')) if d.get('Volume') else 0.0)
    v_fat = c8.number_input("Faturamento (R$)", value=float(str(d.get('Faturamento','0')).replace('R$','').replace('.','').replace(',','.')) if d.get('Faturamento') else 0.0)
    v_hor = c9.number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

    # --- LINHA 4 ---
    c10, c11, c12 = st.columns(3)
    v_tmp = c10.number_input("Tempo Previsto (H)", value=int(d.get('Tempo Previsto (H)', 0)))
    v_cbm = c11.number_input("Combustível (L)", value=int(d.get('Combustível (L)', 0)))
    v_dsl = c12.number_input("Custo Diesel (R$)", value=float(str(d.get('Custo Diesel','0')).replace('R$','').replace('.','').replace(',','.')) if d.get('Custo Diesel') else 0.0)

    v_obs = st.text_area("Observações", value=d.get('Observações', ""))

    status = "Aprovado" if v_fat >= 50000 else "Analise"
    st.markdown(f"### STATUS: <span style='color:{'green' if status == 'Aprovado' else 'red'}'>{status}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        dados_final = {
            "ID": v_id, "Empurrador": v_emp, "Balsas": ", ".join(v_bal),
            "Comandante": v_com, "Rota": f"{v_ori} x {v_des}",
            "Faturamento": f"R$ {v_fat:,.2f}", "Status": status
        }
        pdf_bytes = gerar_pdf_final(dados_final)
        st.success("Salvo com sucesso!")
        st.download_button("📥 BAIXAR PDF ATUALIZADO", pdf_bytes, f"{v_id}.pdf")

elif pagina == "📜 Histórico":
    st.title("📜 Histórico")
    st.dataframe(df_h, use_container_width=True, hide_index=True)
