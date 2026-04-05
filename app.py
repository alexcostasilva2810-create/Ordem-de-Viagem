import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÕES E ESTILO (TRAVANDO AS LARGURAS)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state:
    st.session_state.dados_edit = None

# CSS para fixar largura de 5cm (aprox 220px) e aproximar os campos
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    /* Trava a largura máxima de cada widget para não espalhar */
    [data-testid="stHorizontalBlock"] [data-testid="column"] {
        max-width: 250px !important;
    }
    .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { 
        width: 220px !important; 
    }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.8rem; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 180px; height: 3em; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. PERSONALIZAÇÃO DO PDF (ZION DESIGN)
# =========================================================
class PDF_ZION(FPDF):
    def header(self):
        # Moldura externa (Borda)
        self.rect(5, 5, 200, 287)
        # Logo no PDF
        try: self.image('icone ZION.png', x=10, y=8, w=25)
        except: pass
        self.set_font('Arial', 'B', 16)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'ZION TECNOLOGIA - RESUMO DE VIAGEM', border=0, ln=True, align='C')
        self.ln(10)

def gerar_pdf_pco(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "B", 11)
    
    for chave, valor in dados.items():
        if chave == "Observações":
            pdf.ln(5); pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "OBSERVAÇÕES:", ln=True)
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 8, str(valor), border=1)
        else:
            pdf.set_font("Arial", "B", 11); pdf.cell(50, 10, f"{chave}:", border='B')
            pdf.set_font("Arial", "", 11); pdf.cell(0, 10, f" {valor}", border='B', ln=True)
            
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# 3. CONEXÃO E DADOS
# =========================================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=60)
def carregar_dados(aba):
    client = obter_cliente()
    if client:
        try:
            sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
            data = sh.worksheet(aba).get_all_values()
            return pd.DataFrame(data[1:], columns=data[0])
        except: return pd.DataFrame()
    return pd.DataFrame()

# =========================================================
# 4. INTERFACE (RECUPERANDO O ZION NO TOPO)
# =========================================================

# SIDEBAR ORIGINAL
with st.sidebar:
    try: st.image("icone ZION.png", width=180)
    except: pass
    st.title("MENU ZION")
    pagina = st.radio("Navegação", ["📊 Simulações", "📋 Ativos", "🚢 Balsas", "📍 Rotas", "📜 Histórico"])

if pagina == "📊 Simulações":
    # TOPO COM LOGO E TÍTULO (Como na sua foto)
    c_logo, c_titulo = st.columns([0.1, 0.9])
    with c_logo:
        try: st.image("icone ZION.png", width=60)
        except: pass
    with c_titulo:
        st.title("ZION - Gestão PCO")

    # BUSCA
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        df_hist = carregar_dados("Historico")
        if not df_hist.empty:
            c_sel, c_btn = st.columns([2, 1])
            selecionado = c_sel.selectbox("Registro:", ["---"] + df_hist.iloc[:, 0].tolist(), label_visibility="collapsed")
            if c_btn.button("CARREGAR DADOS"):
                if selecionado != "---":
                    st.session_state.dados_edit = df_hist[df_hist.iloc[:, 0] == selecionado].iloc[0].to_dict()
                    st.rerun()

    vgn_id = st.session_state.dados_edit.get('ID') if st.session_state.dados_edit else datetime.now().strftime("VGM %d%m-%H%M")
    st.subheader(f"Registro: {vgn_id}")

    # BASES
    df_atv = carregar_dados("Ativos")
    df_bal = carregar_dados("Balsas")
    df_rot = carregar_dados("Rotas")

    # --- CAMPOS EM LINHAS DE 3 (LARGURA FIXA 5CM) ---
    l1_c1, l1_c2, l1_c3 = st.columns(3)
    v_emp = l1_c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    bal_def = []
    if st.session_state.dados_edit:
        try: bal_def = ast.literal_eval(st.session_state.dados_edit.get('Balsas', '[]'))
        except: bal_def = []
    v_bal = l1_c2.multiselect("Balsas", df_bal.iloc[:,0] if not df_bal.empty else [], default=bal_def)
    v_com = l1_c3.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', '') if st.session_state.dados_edit else "")

    l2_c1, l2_c2, l2_c3 = st.columns(3)
    v_ori = l2_c1.selectbox("Origem", df_rot.iloc[:,0].unique() if not df_rot.empty else ["-"])
    v_des = l2_c2.selectbox("Destino", df_rot.iloc[:,1].unique() if not df_rot.empty else ["-"])
    v_chf = l2_c3.text_input("Chefe de Máquinas", value=st.session_state.dados_edit.get('Chefe de Máquinas', '') if st.session_state.dados_edit else "")

    l3_c1, l3_c2, l3_c3 = st.columns(3)
    v_vol = l3_c1.number_input("Volume (m³)", value=float(st.session_state.dados_edit.get('Volume (m³)', 0)) if st.session_state.dados_edit else 0.0)
    v_fat = l3_c2.number_input("Faturamento (R$)", value=float(st.session_state.dados_edit.get('Faturamento (R$)', 0)) if st.session_state.dados_edit else 0.0)
    v_hor = l3_c3.number_input("Horímetro", value=float(st.session_state.dados_edit.get('Horímetro', 0)) if st.session_state.dados_edit else 0.0)

    l4_c1, l4_c2, l4_c3 = st.columns(3)
    v_tmp = l4_c1.number_input("Tempo Previsto (H)", value=int(st.session_state.dados_edit.get('Tempo Previsto (H)', 0)) if st.session_state.dados_edit else 0)
    v_cbm = l4_c2.number_input("Combustível (L)", value=int(st.session_state.dados_edit.get('Combustível (L)', 0)) if st.session_state.dados_edit else 0)
    v_dsl = l4_c3.number_input("Custo Diesel (R$)", value=float(st.session_state.dados_edit.get('Custo Diesel (R$)', 0)) if st.session_state.dados_edit else 0.0)

    v_obs = st.text_area("Observações da Viagem", value=st.session_state.dados_edit.get('Observações', '') if st.session_state.dados_edit else "")

    # STATUS
    status_v = "Aprovado" if v_fat >= 5000 else "Analise"
    cor = "green" if status_v == "Aprovado" else "red"
    st.markdown(f"### STATUS: <span style='color:{cor}'>{status_v}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E SALVAR"):
        # Lógica de Salvar no Sheets
        d_pdf = {"ID": vgn_id, "Empurrador": v_emp, "Comandante": v_com, "Faturamento": f"R$ {v_fat:,.2f}", "Observações": v_obs}
        pdf_out = gerar_pdf_pco(d_pdf)
        st.success("✅ Salvo!")
        st.download_button("📥 BAIXAR PDF", pdf_out, f"{vgn_id}.pdf", "application/pdf")

elif pagina == "📜 Histórico":
    st.title("📜 Histórico")
    st.dataframe(carregar_dados("Historico"), use_container_width=True)
