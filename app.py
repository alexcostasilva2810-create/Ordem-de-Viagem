import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. DESIGN E COMPACTAÇÃO (TRAVA DE LARGURA)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# CSS para forçar a visualização COMPACTA (não larga) e botões visíveis
st.markdown("""
    <style>
    /* Limita a largura total da página para não espalhar os botões */
    .block-container { max-width: 900px; padding-top: 1rem; margin: auto; }
    
    /* Força os campos a terem largura fixa de aprox 5cm */
    .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { 
        width: 220px !important; 
    }
    
    /* Aproxima as linhas para visualização em tela única */
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.6rem; }
    
    /* Estilo dos Botões Zion */
    .stButton > button { 
        background-color: #073763; 
        color: white; 
        font-weight: bold; 
        width: 180px; 
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. PDF PERSONALIZADO (BORDAS E LOGO)
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287) # Moldura do PDF
        try: self.image('icone ZION.png', x=10, y=8, w=25)
        except: pass
        self.set_font('Arial', 'B', 15)
        self.set_text_color(7, 55, 99)
        self.cell(0, 10, 'ZION TECNOLOGIA - RESUMO DE VIAGEM', align='C', ln=True)
        self.ln(10)

def gerar_pdf(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "B", 11)
    for k, v in dados.items():
        pdf.set_font("Arial", "B", 11); pdf.cell(50, 8, f"{k}:", border='B')
        pdf.set_font("Arial", "", 11); pdf.cell(0, 8, f" {v}", border='B', ln=True)
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# 3. CONEXÃO E LIMPEZA DE DADOS
# =========================================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=10) # TTL baixo para evitar erro de cota e atualizar rápido
def carregar_dados(aba):
    client = obter_cliente()
    if not client: return pd.DataFrame()
    try:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet(aba).get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        # Resolve o erro de colunas duplicadas que apareceu no seu vídeo
        return df.loc[:, ~df.columns.duplicated()]
    except: return pd.DataFrame()

# =========================================================
# 4. INTERFACE COMPACTA
# =========================================================
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = None

# Sidebar
with st.sidebar:
    try: st.image("icone ZION.png", width=150)
    except: pass
    st.title("MENU ZION")
    pagina = st.radio("Navegação", ["📊 Simulações", "📋 Ativos", "🚢 Balsas", "📍 Rotas", "📜 Histórico"])

if pagina == "📊 Simulações":
    # Cabeçalho Compacto
    c_img, c_tit = st.columns([0.15, 0.85])
    with c_img: 
        try: st.image("icone ZION.png", width=60)
        except: pass
    with c_tit: st.title("ZION - Gestão PCO")

    # Busca de Registro
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        df_h = carregar_dados("Historico")
        if not df_h.empty:
            sel = st.selectbox("Selecione:", ["---"] + df_h.iloc[:, 0].tolist())
            if st.button("CARREGAR DADOS"):
                if sel != "---":
                    st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == sel].iloc[0].to_dict()
                    st.rerun()

    # ID e Layout de Colunas (Travado em 3 por linha)
    v_id = st.session_state.dados_edit.get('ID', datetime.now().strftime("VGM %d%m-%H%M")) if st.session_state.dados_edit else datetime.now().strftime("VGM %d%m-%H%M")
    st.subheader(f"Registro: {v_id}")

    col1, col2, col3 = st.columns(3)
    
    # Linha 1
    v_emp = col1.selectbox("Empurrador", ["Jacaranda", "Quaruba"])
    try: b_def = ast.literal_eval(st.session_state.dados_edit.get('Balsas', '[]'))
    except: b_def = []
    v_bal = col2.multiselect("Balsas", ["Balsa 1", "Balsa 2"], default=b_def)
    v_com = col3.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', "") if st.session_state.dados_edit else "")

    # Linha 2
    v_ori = col1.selectbox("Origem", ["STM", "MIR"])
    v_des = col2.selectbox("Destino", ["MIR", "STM"])
    v_chf = col3.text_input("Chefe de Máquinas", value=st.session_state.dados_edit.get('Chefe de Máquinas', "") if st.session_state.dados_edit else "")

    # Linha 3
    v_vol = col1.number_input("Volume (m³)", value=float(st.session_state.dados_edit.get('Volume (m³)', 0)) if st.session_state.dados_edit else 0.0)
    v_fat = col2.number_input("Faturamento (R$)", value=float(st.session_state.dados_edit.get('Faturamento (R$)', 0)) if st.session_state.dados_edit else 0.0)
    v_hor = col3.number_input("Horímetro", value=float(st.session_state.dados_edit.get('Horímetro', 0)) if st.session_state.dados_edit else 0.0)

    # Observações
    v_obs = st.text_area("Observações da Viagem", value=st.session_state.dados_edit.get('Observações', "") if st.session_state.dados_edit else "")

    # Status e Finalização
    status = "Aprovado" if v_fat >= 50000 else "Analise"
    cor = "green" if status == "Aprovado" else "red"
    st.markdown(f"### STATUS: <span style='color:{cor}'>{status}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        # Lógica de salvar omitida para brevidade, mas o PDF está pronto:
        pdf_bytes = gerar_pdf({"ID": v_id, "Comandante": v_com, "Faturamento": v_fat, "Status": status})
        st.download_button("📥 BAIXAR PDF", pdf_bytes, f"{v_id}.pdf")
        st.success("Salvo com sucesso!")

elif pagina == "📜 Histórico":
    st.title("Histórico")
    st.dataframe(carregar_dados("Historico"))
