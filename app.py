import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E DESIGN (BLINDAGEM DE ERROS)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# Inicializa o estado da sessão para evitar o AttributeError
if 'dados_edit' not in st.session_state or st.session_state.dados_edit is None:
    st.session_state.dados_edit = {}

# Sidebar
with st.sidebar:
    try: st.image("icone ZION.png", width=160)
    except: pass
    st.title("MENU ZION")
    pagina = st.radio("Navegação", ["📊 Simulações", "📜 Histórico"])

# CSS Condicional para Largura da Tela
if pagina == "📊 Simulações":
    st.markdown("""
        <style>
        .block-container { max-width: 1050px; padding-top: 1rem; margin: auto; }
        .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 230px !important; }
        div[data-testid="stVerticalBlock"] > div { margin-top: -0.7rem; }
        .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 200px; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("<style>.block-container { max-width: 100% !important; }</style>", unsafe_allow_html=True)

# =========================================================
# 2. GERAÇÃO DE PDF PERSONALIZADO (TRANS-DOURADA)
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        # Moldura externa
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
# 3. CONEXÃO COM BANCO DE DADOS
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
        valores = sh.worksheet(aba).col_values(col)[1:]
        return [v for v in valores if v.strip()]
    except: return []

# =========================================================
# 4. TELA DE SIMULAÇÕES
# =========================================================
if pagina == "📊 Simulações":
    st.title("ZION - Gestão PCO")
    
    # Carrega dados dos dropdowns
    ativos = carregar_lista("Ativos")
    balsas = carregar_lista("Balsas")
    origens = list(set(carregar_lista("Rotas", 1)))
    destinos = list(set(carregar_lista("Rotas", 2)))

    # Puxa dados do histórico para editar (se selecionado)
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        try:
            sh = obter_cliente().open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
            hist_data = sh.worksheet("Historico").get_all_values()
            df_h = pd.DataFrame(hist_data[1:], columns=hist_data[0])
            sel = st.selectbox("Selecione ID:", ["---"] + df_h.iloc[:, 0].tolist())
            if st.button("CARREGAR DADOS"):
                st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == sel].iloc[0].to_dict()
                st.rerun()
        except: st.info("Histórico vazio ou inacessível.")

    # Proteção contra erro de dicionário vazio
    edit = st.session_state.dados_edit
    v_id = edit.get('ID', datetime.now().strftime("VGM %d%m-%H%M"))

    st.subheader(f"Registro: {v_id}")

    col1, col2, col3 = st.columns(3)

    with col1:
        v_emp = st.selectbox("Empurrador", ativos if ativos else ["-"])
        v_ori = st.selectbox("Origem", origens if origens else ["-"])
        # Formatação Milhar: 350.000
        v_vol = st.number_input("Volume (M³)", value=float(edit.get('Volume (m³)', 0.0)), step=1000.0, format="%.3f")
        v_tmp = st.number_input("Tempo Previsto (H)", value=int(edit.get('Tempo Previsto (H)', 0)))

    with col2:
        try: b_def = ast.literal_eval(edit.get('Balsas', '[]'))
        except: b_def = []
        v_bal = st.multiselect("Balsas", balsas, default=b_def)
        v_des = st.selectbox("Destino", destinos if destinos else ["-"])
        # Formatação Moeda: R$ 520.000,00
        v_fat = st.number_input("Faturamento (R$)", value=float(edit.get('Faturamento (R$)', 0.0)), step=100.0, format="%.2f")
        v_cbm = st.number_input("Combustível (L)", value=int(edit.get('Combustível (L)', 0)))

    with col3:
        v_com = st.text_input("Comandante", value=edit.get('Comandante', ""))
        v_chf = st.text_input("Chefe de Máquinas", value=edit.get('Chefe de Máquinas', ""))
        v_hor = st.number_input("Horímetro", value=float(edit.get('Horímetro', 0.0)))
        # Formatação Moeda: R$ 85.000,00
        v_dsl = st.number_input("Custo Diesel (R$)", value=float(edit.get('Custo Diesel (R$)', 0.0)), step=100.0, format="%.2f")

    v_obs = st.text_area("Observações da Viagem", value=edit.get('Observações', ""))
    
    status = "Aprovado" if v_fat >= 50000 else "Analise"
    st.markdown(f"### STATUS: <span style='color:{'green' if status == 'Aprovado' else 'red'}'>{status}</span>", unsafe_allow_html=True)
    
    if st.button("FINALIZAR E SALVAR"):
        # Dados formatados para o PDF
        dados_final = {
            "ID da Viagem": v_id,
            "Empurrador": v_emp,
            "Balsas": ", ".join(v_bal),
            "Comandante": v_com,
            "Rota": f"{v_ori} para {v_des}",
            "Volume": f"{v_vol:,.0f} M³".replace(",", "."),
            "Faturamento": f"R$ {v_fat:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Custo Diesel": f"R$ {v_dsl:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        
        pdf_bytes = gerar_pdf(dados_final)
        st.success("Dados salvos e PDF gerado!")
        st.download_button("📥 BAIXAR ORDEM DE VIAGEM", pdf_bytes, f"Ordem_{v_id}.pdf", "application/pdf")
        st.session_state.dados_edit = {}

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
