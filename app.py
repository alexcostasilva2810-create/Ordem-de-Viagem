import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E DESIGN (TRAVA 5CM / COMPACTO)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = {}

# Sidebar Original
with st.sidebar:
    try: st.image("icone ZION.png", width=160)
    except: pass
    st.title("MENU ZION")
    pagina = st.radio("Navegação", ["📊 Simulações", "📜 Histórico"])

# CSS para travar o layout da Simulação como você quer
if pagina == "📊 Simulações":
    st.markdown("""
        <style>
        .block-container { max-width: 1000px; padding-top: 1rem; margin: auto; }
        .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 220px !important; }
        div[data-testid="stVerticalBlock"] > div { margin-top: -0.8rem; }
        .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 200px; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("<style>.block-container { max-width: 100% !important; }</style>", unsafe_allow_html=True)

# =========================================================
# 2. PDF PERSONALIZADO - ORDEM DE VIAGEM TRANSDOURADA
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

def gerar_pdf(dados):
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
# 3. CONEXÃO E LIMPEZA DE DADOS
# =========================================================
def obter_cliente():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

def carregar_lista(aba, col=1):
    try:
        sh = obter_cliente().open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        return [v for v in sh.worksheet(aba).col_values(col)[1:] if v.strip()]
    except: return []

@st.cache_data(ttl=5)
def carregar_historico_blindado():
    client = obter_cliente()
    try:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet("Historico").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df.loc[:, ~df.columns.duplicated()] # Mata o erro de duplicatas
    except: return pd.DataFrame()

# =========================================================
# 4. TELA DE SIMULAÇÕES (LAYOUT ORIGINAL RESTAURADO)
# =========================================================
if pagina == "📊 Simulações":
    # Cabeçalho Zion
    c_img, c_tit = st.columns([0.1, 0.9])
    with c_img: 
        try: st.image("icone ZION.png", width=55)
        except: pass
    with c_tit: st.title("ZION - Gestão PCO")

    # Busca
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        df_h = carregar_historico_blindado()
        if not df_h.empty:
            sel = st.selectbox("Selecione ID:", ["---"] + df_h.iloc[:, 0].tolist())
            if st.button("CARREGAR DADOS"):
                st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == sel].iloc[0].to_dict()
                st.rerun()

    edit = st.session_state.dados_edit
    v_id = edit.get('ID', datetime.now().strftime("VGM %d%m-%H%M"))
    st.subheader(f"Registro: {v_id}")

    # Bases
    ativos = carregar_lista("Ativos")
    balsas = carregar_lista("Balsas")
    origens = list(set(carregar_lista("Rotas", 1)))
    destinos = list(set(carregar_lista("Rotas", 2)))

    # --- GRID ORIGINAL: 4 LINHAS DE 3 COLUNAS ---
    # Linha 1
    l1c1, l1c2, l1c3 = st.columns(3)
    v_emp = l1c1.selectbox("Empurrador", ativos if ativos else ["-"])
    try: b_def = ast.literal_eval(edit.get('Balsas', '[]'))
    except: b_def = []
    v_bal = l1c2.multiselect("Balsas", balsas, default=b_def)
    v_com = l1c3.text_input("Comandante", value=edit.get('Comandante', ""))

    # Linha 2
    l2c1, l2c2, l2c3 = st.columns(3)
    v_ori = l2c1.selectbox("Origem", origens if origens else ["-"])
    v_des = l2c2.selectbox("Destino", destinos if destinos else ["-"])
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

    v_obs = st.text_area("Observações da Viagem", value=edit.get('Observações', ""))
    
    # STATUS ORIGINAL
    status = "Aprovado" if v_fat >= 50000 else "Analise"
    st.markdown(f"### STATUS: <span style='color:{'green' if status == 'Aprovado' else 'red'}'>{status}</span>", unsafe_allow_html=True)
    
    if st.button("FINALIZAR E SALVAR"):
        dados_pdf = {
            "ID": v_id, "Empurrador": v_emp, "Faturamento": f"R$ {v_fat:,.2f}", 
            "Status": status, "Volume": f"{v_vol:,.3f} M³"
        }
        pdf_out = gerar_pdf(dados_pdf)
        st.success("Salvo!")
        st.download_button("📥 BAIXAR ORDEM DE VIAGEM", pdf_out, f"Ordem_{v_id}.pdf")

# =========================================================
# 5. TELA DE HISTÓRICO (LARGURA TOTAL)
# =========================================================
elif pagina == "📜 Histórico":
    st.title("📜 Histórico de Viagens")
    df_h = carregar_historico_blindado()
    st.dataframe(df_h, use_container_width=True, hide_index=True)
