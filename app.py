import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO PDF ---
class PDF(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287) # Borda
        try: self.image('fundo_offshore.jpg', 10, 50, 190) # Fundo
        except: pass
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'ZION TECNOLOGIA - RESUMO DE VIAGEM', 0, 1, 'C')
        self.ln(10)

def gerar_pdf(dados):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 12)
    for chave, valor in dados.items():
        if chave == "Observações":
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "OBSERVAÇÕES:", ln=True)
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 8, str(valor), border=1)
        else:
            pdf.cell(0, 10, f"{chave}: {valor}", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- CONEXÃO ---
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
            return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame()
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- INTERFACE ---
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = None

st.title("🚢 ZION - Gestão PCO")

# Busca
df_hist = carregar_dados("Historico")
with st.expander("🔍 BUSCAR REGISTRO"):
    lista = ["---"] + (df_hist.iloc[:, 0].tolist() if not df_hist.empty else [])
    sel = st.selectbox("Selecione:", lista)
    if st.button("CARREGAR"):
        if sel != "---":
            st.session_state.dados_edit = df_hist[df_hist.iloc[:, 0] == sel].iloc[0].to_dict()
            st.rerun()

# Formulário com TODOS os campos
id_reg = st.session_state.dados_edit.get('ID') if st.session_state.dados_edit else datetime.now().strftime("VGM %d%m-%H%M")
c1, c2, c3 = st.columns(3)
emp = c1.selectbox("Empurrador", ["Jacaranda", "Quaruba", "Outro"]) # Ajuste conforme sua lista
com = c2.text_input("Comandante", value=st.session_state.dados_edit.get('Comandante', '') if st.session_state.dados_edit else "")
chf = c3.text_input("Chefe de Máquinas", value=st.session_state.dados_edit.get('Chefe de Máquinas', '') if st.session_state.dados_edit else "")

c4, c5, c6 = st.columns(3)
vol = c4.number_input("Volume (m³)", value=int(float(st.session_state.dados_edit.get('Volume (m³)', 0))) if st.session_state.dados_edit else 0)
fat = c5.number_input("Faturamento (R$)", value=float(st.session_state.dados_edit.get('Faturamento (R$)', 0)) if st.session_state.dados_edit else 0.0)
hor = c6.number_input("Horímetro", value=float(st.session_state.dados_edit.get('Horímetro', 0)) if st.session_state.dados_edit else 0.0)

c7, c8, c9 = st.columns(3)
tmp = c7.number_input("Tempo Previsto (H)", value=int(st.session_state.dados_edit.get('Tempo Previsto (H)', 0)) if st.session_state.dados_edit else 0)
cbm = c8.number_input("Combustível (L)", value=int(st.session_state.dados_edit.get('Combustível (L)', 0)) if st.session_state.dados_edit else 0)
dse = c9.number_input("Custo Diesel (R$)", value=float(st.session_state.dados_edit.get('Custo Diesel (R$)', 0)) if st.session_state.dados_edit else 0.0)

obs = st.text_area("Observações da Viagem", value=st.session_state.dados_edit.get('Observações', '') if st.session_state.dados_edit else "")

# Salvar
if st.button("FINALIZAR E SALVAR"):
    # ... (lógica de salvar na planilha permanece igual)
    dados_pdf = {"ID": id_reg, "Empurrador": emp, "Comandante": com, "Volume": vol, "Faturamento": fat, "Observações": obs}
    pdf_bytes = gerar_pdf(dados_pdf)
    st.success("Salvo!")
    st.download_button("📥 BAIXAR PDF", pdf_bytes, f"{id_reg}.pdf")
