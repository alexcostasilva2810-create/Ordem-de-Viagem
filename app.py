import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E DESIGN COMPACTO
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = None

# Sidebar
with st.sidebar:
    try: st.image("icone ZION.png", width=160)
    except: pass
    st.title("MENU ZION")
    pagina = st.radio("Navegação", ["📊 Simulações", "📜 Histórico"])

# CSS Condicional: Simulação (Compacto) vs Histórico (Largo)
if pagina == "📊 Simulações":
    st.markdown("""
        <style>
        .block-container { max-width: 1050px; padding-top: 1rem; margin: auto; }
        .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 230px !important; }
        div[data-testid="stVerticalBlock"] > div { margin-top: -0.8rem; }
        .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 200px; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("<style>.block-container { max-width: 100% !important; }</style>", unsafe_allow_html=True)

# =========================================================
# 2. CLASSE PDF PERSONALIZADA
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        # Moldura/Borda do PDF
        self.rect(5, 5, 200, 287)
        try: self.image('icone ZION.png', x=10, y=8, w=20)
        except: pass
        self.set_font('Arial', 'B', 14)
        self.set_text_color(7, 55, 99)
        # Cabeçalho solicitado
        self.cell(0, 10, 'Ordem de Viagem - Transdourada', align='C', ln=True)
        self.ln(10)

def gerar_pdf_ordem(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "B", 10)
    
    for k, v in dados.items():
        pdf.set_font("Arial", "B", 10); pdf.cell(50, 8, f"{k}:", border='B')
        pdf.set_font("Arial", "", 10); pdf.cell(0, 8, f" {v}", border='B', ln=True)
    
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# 3. CONEXÃO E DADOS
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

# =========================================================
# 4. TELA DE SIMULAÇÕES
# =========================================================
if pagina == "📊 Simulações":
    st.title("ZION - Gestão PCO")
    
    ativos = carregar_lista("Ativos")
    balsas = carregar_lista("Balsas")
    origens = list(set(carregar_lista("Rotas", 1)))
    destinos = list(set(carregar_lista("Rotas", 2)))
    edit = st.session_state.get('dados_edit', {})

    v_id = edit.get('ID', datetime.now().strftime("VGM %d%m-%H%M"))
    st.subheader(f"Registro: {v_id}")

    col1, col2, col3 = st.columns(3)

    with col1:
        v_emp = st.selectbox("Empurrador", ativos if ativos else ["-"])
        v_ori = st.selectbox("Origem", origens if origens else ["-"])
        v_vol = st.number_input("Volume (M³)", value=float(edit.get('Volume (m³)', 0)), format="%.3f")
        v_tmp = st.number_input("Tempo Previsto (H)", value=int(edit.get('Tempo Previsto (H)', 0)))

    with col2:
        try: b_def = ast.literal_eval(edit.get('Balsas', '[]'))
        except: b_def = []
        v_bal = st.multiselect("Balsas", balsas, default=b_def)
        v_des = st.selectbox("Destino", destinos if destinos else ["-"])
        v_fat = st.number_input("Faturamento (R$)", value=float(edit.get('Faturamento (R$)', 0)), format="%.2f")
        v_cbm = st.number_input("Combustível (L)", value=int(edit.get('Combustível (L)', 0)))

    with col3:
        v_com = st.text_input("Comandante", value=edit.get('Comandante', ""))
        v_chf = st.text_input("Chefe de Máquinas", value=edit.get('Chefe de Máquinas', ""))
        v_hor = st.number_input("Horímetro", value=float(edit.get('Horímetro', 0)))
        v_dsl = st.number_input("Custo Diesel (R$)", value=float(edit.get('Custo Diesel (R$)', 0)), format="%.2f")

    v_obs = st.text_area("Observações da Viagem", value=edit.get('Observações', ""))
    
    status = "Aprovado" if v_fat >= 50000 else "Analise"
    st.markdown(f"### STATUS: <span style='color:{'green' if status == 'Aprovado' else 'red'}'>{status}</span>", unsafe_allow_html=True)
    
    if st.button("FINALIZAR E SALVAR"):
        # Preparar dados para o PDF
        dados_pdf = {
            "ID": v_id,
            "Empurrador": v_emp,
            "Balsas": ", ".join(v_bal),
            "Comandante": v_com,
            "Origem/Destino": f"{v_ori} -> {v_des}",
            "Volume": f"{v_vol:,.3f} M³",
            "Faturamento": f"R$ {v_fat:,.2f}",
            "Custo Diesel": f"R$ {v_dsl:,.2f}",
            "Status": status,
            "Observações": v_obs
        }
        
        pdf_bytes = gerar_pdf_ordem(dados_pdf)
        st.success("Dados processados!")
        st.download_button("📥 BAIXAR ORDEM DE VIAGEM", pdf_bytes, f"Ordem_{v_id}.pdf", "application/pdf")
        st.session_state.dados_edit = None

# =========================================================
# 5. TELA DE HISTÓRICO (LARGURA TOTAL)
# =========================================================
elif pagina == "📜 Histórico":
    st.title("📜 Histórico de Viagens")
    try:
        sh = obter_cliente().open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet("Historico").get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        st.dataframe(df, use_container_width=True, hide_index=True)
    except:
        st.error("Erro ao carregar banco de dados.")
