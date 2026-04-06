import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E DESIGN DINÂMICO
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = {}

with st.sidebar:
    try: st.image("icone ZION.png", width=160)
    except: pass
    st.title("MENU ZION")
    pagina = st.radio("Navegação", ["📊 Simulações", "📜 Histórico"])

# CSS Condicional: Compacto na simulação, Largo no histórico
if pagina == "📊 Simulações":
    st.markdown("""
        <style>
        .block-container { max-width: 1050px; padding-top: 1rem; margin: auto; }
        .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 230px !important; }
        div[data-testid="stVerticalBlock"] > div { margin-top: -0.7rem; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("<style>.block-container { max-width: 100% !important; }</style>", unsafe_allow_html=True)

# =========================================================
# 2. CONEXÃO E LIMPEZA DE DADOS (CORREÇÃO DO ERRO)
# =========================================================
def obter_cliente():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=5)
def carregar_historico_limpo():
    client = obter_cliente()
    try:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet("Historico").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        # CORREÇÃO CRÍTICA: Remove colunas duplicadas que travam o Streamlit
        df = df.loc[:, ~df.columns.duplicated()]
        return df
    except Exception as e:
        return pd.DataFrame()

def carregar_lista(aba, col=1):
    try:
        sh = obter_cliente().open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        return [v for v in sh.worksheet(aba).col_values(col)[1:] if v.strip()]
    except: return []

# =========================================================
# 3. GERAÇÃO DE PDF PERSONALIZADO
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287)
        try: self.image('icone ZION.png', x=10, y=8, w=20)
        except: pass
        self.set_font('Arial', 'B', 16)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'Ordem de Viagem - Transdourada', align='C', ln=True)
        self.ln(5)

def gerar_pdf(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "B", 11)
    for k, v in dados.items():
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(50, 10, f"{k}:", border=1, fill=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 10, f" {v}", border=1, ln=True)
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# 4. TELAS
# =========================================================
if pagina == "📊 Simulações":
    st.title("ZION - Gestão PCO")
    
    ativos = carregar_lista("Ativos")
    balsas = carregar_lista("Balsas")
    origens = list(set(carregar_lista("Rotas", 1)))
    destinos = list(set(carregar_lista("Rotas", 2)))

    edit = st.session_state.dados_edit
    v_id = edit.get('ID', datetime.now().strftime("VGM %d%m-%H%M"))

    col1, col2, col3 = st.columns(3)
    with col1:
        v_emp = st.selectbox("Empurrador", ativos if ativos else ["-"])
        v_ori = st.selectbox("Origem", origens if origens else ["-"])
        v_vol = st.number_input("Volume (M³)", value=float(edit.get('Volume (m³)', 0.0)), format="%.3f")
        v_tmp = st.number_input("Tempo Previsto (H)", value=int(edit.get('Tempo Previsto (H)', 0)))

    with col2:
        v_bal = st.multiselect("Balsas", balsas, default=[])
        v_des = st.selectbox("Destino", destinos if destinos else ["-"])
        v_fat = st.number_input("Faturamento (R$)", value=float(edit.get('Faturamento (R$)', 0.0)), format="%.2f")
        v_cbm = st.number_input("Combustível (L)", value=int(edit.get('Combustível (L)', 0)))

    with col3:
        v_com = st.text_input("Comandante", value=edit.get('Comandante', ""))
        v_chf = st.text_input("Chefe de Máquinas", value=edit.get('Chefe de Máquinas', ""))
        v_hor = st.number_input("Horímetro", value=float(edit.get('Horímetro', 0.0)))
        v_dsl = st.number_input("Custo Diesel (R$)", value=float(edit.get('Custo Diesel (R$)', 0.0)), format="%.2f")

    if st.button("FINALIZAR E SALVAR"):
        dados_final = {
            "ID": v_id, "Empurrador": v_emp, "Comandante": v_com,
            "Volume": f"{v_vol:,.0f} M³".replace(",", "."),
            "Faturamento": f"R$ {v_fat:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Custo Diesel": f"R$ {v_dsl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        }
        pdf_bytes = gerar_pdf(dados_final)
        st.success("Salvo!")
        st.download_button("📥 BAIXAR PDF", pdf_bytes, f"Ordem_{v_id}.pdf", "application/pdf")

elif pagina == "📜 Histórico":
    st.title("📜 Histórico de Viagens")
    df_h = carregar_historico_limpo()
    if not df_h.empty:
        st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.error("Erro: Verifique se há colunas duplicadas ou vazias na planilha.")
