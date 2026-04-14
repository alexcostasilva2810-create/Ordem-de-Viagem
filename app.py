import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast

# =========================================================
# 1. CONFIGURAÇÃO E DESIGN (MANTENDO O AFASTAMENTO DE 2CM)
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# Inicializa estados para não perder dados na navegação
if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = "Capa"
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}

st.markdown("""
    <style>
    .block-container { max-width: 1100px; padding-top: 75px; margin: auto; }
    .capa-container {
        text-align: center; padding: 60px;
        background-color: #f8f9fa; border-radius: 20px;
        border: 2px solid #073763; margin-bottom: 40px;
    }
    .stButton > button { 
        background-color: #073763; color: white; 
        font-weight: bold; width: 100%; height: 3.5em; 
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. CLASSE DO PDF (LAYOUT O.S.)
# =========================================================
class PDF_OS(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287) # Borda da folha
        self.set_font('Arial', 'B', 14)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'ORDEM DE VIAGEM - TRANSDOURADA', align='C', ln=True)
        self.ln(5)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 8)
        fuso_br = timezone(timedelta(hours=-3))
        agora = datetime.now(fuso_br).strftime("%d/%m/%Y - %H:%M:%S")
        self.cell(0, 10, f'Gerado em: {agora} | ZION Gestão PCO', align='C')

def gerar_pdf_os(dados):
    pdf = PDF_OS()
    pdf.add_page()
    pdf.set_font("Arial", "B", 10)
    for k, v in dados.items():
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(60, 9, f" {k}", border=1, fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 9, f" {v}", border=1, ln=True)
        pdf.set_font("Arial", "B", 10)
    return pdf.output(dest="S").encode("latin-1")

# =========================================================
# 3. CONEXÃO COM BANCO DE DADOS (FORÇADA E FUNCIONAL)
# =========================================================
def carregar_tudo_zion():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        
        # Carrega as abas
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        
        hist_raw = sh.worksheet("Historico").get_all_values()
        df_h = pd.DataFrame(hist_raw[1:], columns=hist_raw[0]) if len(hist_raw) > 1 else pd.DataFrame()
        
        return ativos, balsas, rotas, df_h
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return [], [], [], pd.DataFrame()

ativos, lista_balsas, lista_rotas, df_h = carregar_tudo_zion()

# =========================================================
# 4. LÓGICA DE NAVEGAÇÃO
# =========================================================

if st.session_state.pagina_atual == "Capa":
    st.markdown("""
        <div class="capa-container">
            <h1 style='color: #073763; font-size: 50px;'>🚢 ZION - Gestão PCO</h1>
            <p style='font-size: 22px; color: #555;'>Sistema de Simulação e Controle Transdourada</p>
        </div>
    """, unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 1.5, 1])
    if col_btn.button("🚀 ACESSAR SIMULADOR"):
        st.session_state.pagina_atual = "Sistema"
        st.rerun()

else:
    with st.sidebar:
        st.markdown("### ⚙️ MENU")
        if st.button("🏠 Voltar para Capa"):
            st.session_state.pagina_atual = "Capa"
            st.rerun()
        menu = st.radio("Selecione:", ["📊 Simulações", "📜 Histórico"])

    if menu == "📊 Simulações":
        st.title("📊 Simulador de Operação")
        
        # CAMPO DE PESQUISA FUNCIONAL
        with st.expander("🔍 BUSCAR REGISTRO EXISTENTE"):
            if not df_h.empty:
                id_sel = st.selectbox("Selecione o ID para carregar:", ["---"] + df_h.iloc[:, 0].tolist())
                if st.button("CARREGAR DADOS"):
                    st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
                    st.rerun()

        d = st.session_state.dados_edit
        
        # Grid 4x3 de Inputs
        c1, c2, c3 = st.columns(3)
        v_emp = c1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
        try: b_def = ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else []
        except: b_def = []
        v_bal = c2.multiselect("Balsas", lista_balsas, default=b_def)
        v_com = c3.text_input("Comandante", value=d.get('Comandante', ""))

        c4, c5, c6 = st.columns(3)
        oris = sorted(list(set([r[0] for r in lista_rotas if r])))
        dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
        v_ori = c4.selectbox("Origem", oris, index=oris.index(d['Origem']) if d.get('Origem') in oris else 0)
        v_des = c5.selectbox("Destino", dess, index=dess.index(d['Destino']) if d.get('Destino') in dess else 0)
        v_chf = c6.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

        c7, c8, c9 = st.columns(3)
        v_vol = c7.number_input("Volume (M³)", value=float(d.get('Volume', 0.0)))
        v_fat = c8.number_input("Faturamento (R$)", value=float(d.get('Faturamento', 0.0)))
        v_hor = c9.number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

        # Lógica de Status
        status = "APROVADO" if v_fat >= 50000 else "ANÁLISE"
        st.write(f"**STATUS:** {status}")

        if st.button("✅ FINALIZAR E GERAR O.S. (PDF)"):
            dados_os = {
                "ID Viagem": datetime.now().strftime("VGM-%H%M"),
                "Empurrador": v_emp, "Balsas": ", ".join(v_bal),
                "Rota": f"{v_ori} x {v_des}", "Faturamento": f"R$ {v_fat:,.2f}",
                "Status": status
            }
            pdf_bytes = gerar_pdf_os(dados_os)
            st.success("Dados processados!")
            st.download_button("📥 BAIXAR O.S. EM PDF", data=pdf_bytes, file_name="Ordem_Servico.pdf", mime="application/pdf")

    elif menu == "📜 Histórico":
        st.title("📜 Histórico de Viagens")
        if not df_h.empty:
            st.dataframe(df_h, use_container_width=True)
        else:
            st.info("Nenhum registro encontrado.")
