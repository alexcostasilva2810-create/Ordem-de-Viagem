import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E CSS (FIX PARA BALSAS E LARGURA)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = {}

# CSS para travar o layout e permitir muitas balsas com scroll
st.markdown("""
    <style>
    .block-container { max-width: 1050px; padding-top: 1rem; margin: auto; }
    
    /* Trava a altura do campo de balsas para não empurrar a tela */
    div[data-baseweb="select"] > div:first-child {
        max-height: 45px;
        overflow-y: auto;
    }
    
    .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 220px !important; }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.8rem; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 200px; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. PDF PERSONALIZADO (ORDEM DE VIAGEM)
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287)
        try: self.image('icone ZION.png', x=10, y=8, w=20)
        except: pass
        self.set_font('Arial', 'B', 15)
        self.set_text_color(7, 55, 99)
        self.cell(0, 10, 'Ordem de Viagem - Transdourada', align='C', ln=True)
        self.ln(10)

def gerar_pdf_ordem(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "B", 10)
    for k, v in dados.items():
        pdf.cell(50, 8, f"{k}:", border='B')
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, f" {v}", border='B', ln=True)
        pdf.set_font("Arial", "B", 10)
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# 3. CONEXÃO COM BANCO DE DADOS
# =========================================================
def obter_cliente():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=5)
def carregar_tudo():
    try:
        sh = obter_cliente().open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        hist_data = sh.worksheet("Historico").get_all_values()
        df_h = pd.DataFrame(hist_data[1:], columns=hist_data[0]).loc[:, ~pd.Series(hist_data[0]).duplicated()]
        return ativos, balsas, rotas, df_h
    except: return [], [], [], pd.DataFrame()

# =========================================================
# 4. INTERFACE
# =========================================================
with st.sidebar:
    try: st.image("icone ZION.png", width=150)
    except: pass
    pagina = st.radio("MENU", ["📊 Simulações", "📜 Histórico"])

ativos, lista_balsas, lista_rotas, df_historico = carregar_tudo()

if pagina == "📊 Simulações":
    st.title("ZION - Gestão PCO")

    # BUSCA DE REGISTROS SALVOS (VOLTOU)
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        if not df_historico.empty:
            id_sel = st.selectbox("Escolha o ID:", ["---"] + df_historico.iloc[:, 0].tolist())
            if st.button("CARREGAR DADOS"):
                st.session_state.dados_edit = df_historico[df_historico.iloc[:, 0] == id_sel].iloc[0].to_dict()
                st.rerun()

    edit = st.session_state.dados_edit
    v_id = edit.get('ID', datetime.now().strftime("VGM %d%m-%H%M"))
    st.subheader(f"Registro: {v_id}")

    # GRID 4x3 RESTAURADO
    # Linha 1
    l1c1, l1c2, l1c3 = st.columns(3)
    v_emp = l1c1.selectbox("Empurrador", ativos)
    try: b_def = ast.literal_eval(edit.get('Balsas', '[]')) if isinstance(edit.get('Balsas'), str) else []
    except: b_def = []
    v_bal = l1c2.multiselect("Balsas", lista_balsas, default=b_def) # Com scroll fixo
    v_com = l1c3.text_input("Comandante", value=edit.get('Comandante', ""))

    # Linha 2
    l2c1, l2c2, l2c3 = st.columns(3)
    v_ori = l2c1.selectbox("Origem", sorted(list(set([r[0] for r in lista_rotas if r[0]]))))
    v_des = l2c2.selectbox("Destino", sorted(list(set([r[1] for r in lista_rotas if r[1]]))))
    v_chf = l2c3.text_input("Chefe de Máquinas", value=edit.get('Chefe de Máquinas', ""))

    # Linha 3
    l3c1, l3c2, l3c3 = st.columns(3)
    v_vol = l3c1.number_input("Volume (M³)", value=float(edit.get('Volume (m³)', 0.0)), format="%.3f")
    v_fat = l3c2.number_input("Faturamento (R$)", value=float(edit.get('Faturamento (R$)', 0.0)), format="%.2f")
    v_hor = l3c3.number_input("Horímetro", value=float(edit.get('Horímetro', 0.0)))

    # Linha 4
    l4c1, l4c2, l4c3 = st.columns(3)
    v_tmp = l4c1.number_input("Tempo Previsto (H)", value=int(edit.get('Tempo Previsto (H)', 0)))
    v_cbm = l4c2.number_input("Combustível (L)", value=int(edit.get('Combustível (L)', 0)))
    v_dsl = l4c3.number_input("Custo Diesel (R$)", value=float(edit.get('Custo Diesel (R$)', 0.0)), format="%.2f")

    v_obs = st.text_area("Observações", value=edit.get('Observações', ""))

    # STATUS
    status = "Aprovado" if v_fat >= 50000 else "Analise"
    st.markdown(f"### STATUS: <span style='color:{'green' if status == 'Aprovado' else 'red'}'>{status}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        # GERAÇÃO DO PDF (VOLTOU)
        dados_pdf = {
            "ID": v_id, "Empurrador": v_emp, "Comandante": v_com,
            "Volume": f"{v_vol:,.3f} M³", "Faturamento": f"R$ {v_fat:,.2f}",
            "Status": status, "Data": datetime.now().strftime("%d/%m/%Y")
        }
        pdf_bytes = gerar_pdf_ordem(dados_pdf)
        st.success("Dados processados com sucesso!")
        st.download_button("📥 BAIXAR ORDEM DE VIAGEM", pdf_bytes, f"Ordem_{v_id}.pdf", "application/pdf")

elif pagina == "📜 Histórico":
    st.markdown("<style>.block-container { max-width: 100% !important; }</style>", unsafe_allow_html=True)
    st.title("📜 Histórico Completo")
    st.dataframe(df_historico, use_container_width=True, hide_index=True)
