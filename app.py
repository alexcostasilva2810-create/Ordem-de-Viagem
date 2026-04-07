import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast

# =========================================================
# 1. DESIGN CORRIGIDO (FIXO 4X3)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}

st.markdown("""
    <style>
    .block-container { max-width: 1050px; padding-top: 1rem; margin: auto; }
    /* Correção do layout: mantemos largura fixa e alinhamento */
    .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 220px !important; }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.7rem; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. PDF (DATA/HORA BRASIL)
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'ORDEM DE VIAGEM - TRANSDOURADA', align='C', ln=True)
    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 8)
        fuso_br = timezone(timedelta(hours=-3))
        self.cell(0, 10, f'Gerado em: {datetime.now(fuso_br).strftime("%d/%m/%Y - %H:%M:%S")}', align='C')

def gerar_pdf(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "", 10)
    for k, v in dados.items():
        pdf.cell(60, 9, f" {k}", border=1)
        pdf.cell(0, 9, f" {v}", border=1, ln=True)
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# 3. LÓGICA E INTERFACE (RESTABELECIDA)
# =========================================================
with st.sidebar:
    pagina = st.radio("NAVEGAÇÃO", ["📊 Simulações", "📜 Histórico"])

# Função carregamento (simplificada para evitar erros)
def carregar_tudo():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"])
    sh = gspread.authorize(creds).open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
    df = pd.DataFrame(sh.worksheet("Historico").get_all_values())
    df.columns = df.iloc[0]; df = df[1:]
    return sh.worksheet("Ativos").col_values(1)[1:], sh.worksheet("Balsas").col_values(1)[1:], df

ativos, balsas, df_h = carregar_tudo()

if pagina == "📊 Simulações":
    st.title("ZION - Gestão PCO")
    
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        id_sel = st.selectbox("Selecione ID:", ["---"] + df_h.iloc[:, 0].tolist())
        if st.button("CARREGAR DADOS"):
            st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
            st.rerun()

    d = st.session_state.dados_edit
    
    # Grid 4x3 (Layout Original)
    cols1 = st.columns(3)
    v_emp = cols1[0].selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
    v_bal = cols1[1].multiselect("Balsas", balsas, default=ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else [])
    v_com = cols1[2].text_input("Comandante", value=d.get('Comandante', ""))

    cols2 = st.columns(3)
    v_ori = cols2[0].text_input("Origem", value=d.get('Origem', ""))
    v_des = cols2[1].text_input("Destino", value=d.get('Destino', ""))
    v_chf = cols2[2].text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

    cols3 = st.columns(3)
    v_vol = cols3[0].number_input("Volume (M³)", value=float(str(d.get('Volume',0)).replace('.','').replace(',','.')) if d.get('Volume') else 0.0)
    v_fat = cols3[1].number_input("Faturamento (R$)", value=float(str(d.get('Faturamento',0)).replace('.','').replace(',','.')) if d.get('Faturamento') else 0.0)
    v_hor = cols3[2].number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

    cols4 = st.columns(3)
    v_tmp = cols4[0].number_input("Tempo (H)", value=int(d.get('Tempo Previsto (H)', 0)))
    v_cbm = cols4[1].number_input("Combustível (L)", value=int(d.get('Combustível (L)', 0)))
    v_dsl = cols4[2].number_input("Custo Diesel (R$)", value=float(str(d.get('Custo Diesel',0)).replace('.','').replace(',','.')) if d.get('Custo Diesel') else 0.0)

    if st.button("FINALIZAR E GERAR PDF"):
        dados = {"ID": d.get('ID', 'VGM-001'), "Empurrador": v_emp, "Faturamento": f"R$ {v_fat:,.2f}"}
        st.download_button("📥 BAIXAR PDF", gerar_pdf(dados), "ordem.pdf")

elif pagina == "📜 Histórico":
    st.dataframe(df_h, use_container_width=True)
