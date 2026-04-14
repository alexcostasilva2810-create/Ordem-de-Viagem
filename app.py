import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast
import uuid

# Configurações de layout e estado da sessão
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = "Capa"
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}
if 'session_id' not in st.session_state: st.session_state.session_id = str(uuid.uuid4())

# Estilos customizados
st.markdown("""
    <style>
    .block-container { max-width: 1100px; padding-top: 70px; margin: auto; }
    .capa-container {
        text-align: center; padding: 50px;
        background-color: #f8f9fa; border-radius: 20px;
        border: 2px solid #073763; margin-bottom: 40px;
    }
    .stButton > button { 
        background-color: #073763; color: white; 
        font-weight: bold; width: 100%; height: 3.5em; 
    }
    div[data-baseweb="select"] > div:first-child { max-height: 200px; overflow-y: auto; }
    </style>
""", unsafe_allow_html=True)

# Classe para geração do PDF da Ordem de Serviço
class PDF_ZION(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'ORDEM DE VIAGEM - TRANSDOURADA', align='C', ln=True)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        fuso_br = timezone(timedelta(hours=-3))
        agora = datetime.now(fuso_br).strftime("%d/%m/%Y - %H:%M:%S")
        self.cell(0, 10, f'Gerado em: {agora} - ZION Gestão PCO', align='C')

def gerar_pdf_os(dados):
    pdf = PDF_ZION()
    pdf.add_page()
    pdf.set_font("Arial", "B", 10)
    for k, v in dados.items():
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(60, 10, f" {k}", border=1, fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f" {str(v)}", border=1, ln=True)
        pdf.set_font("Arial", "B", 10)
    return pdf.output(dest="S").encode("latin-1")

# Função para carregar dados das planilhas
def carregar_dados_sistema():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        
        ativos = [x for x in sh.worksheet("Ativos").col_values(1)[1:] if x]
        balsas = [x for x in sh.worksheet("Balsas").col_values(1)[1:] if x]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        
        hist_raw = sh.worksheet("Historico").get_all_values()
        if len(hist_raw) > 1:
            df = pd.DataFrame(hist_raw[1:], columns=hist_raw[0])
            df = df.loc[:, ~df.columns.duplicated()].copy()
        else:
            df = pd.DataFrame()
            
        return ativos, balsas, rotas, df
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return [], [], [], pd.DataFrame()

# Navegação e Telas
if st.session_state.pagina_atual == "Capa":
    st.markdown('<div class="capa-container"><h1>🚢 ZION - GESTÃO PCO</h1><p>Transdourada Navegação</p></div>', unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 1.5, 1])
    if col_btn.button("🚀 ENTRAR NO SISTEMA", key="btn_entrar"):
        st.session_state.pagina_atual = "Sistema"
        st.rerun()

else:
    ativos, lista_balsas, lista_rotas, df_h = carregar_dados_sistema()
    uid = st.session_state.session_id

    with st.sidebar:
        if st.button("🏠 Voltar para Capa", key="btn_capa"):
            st.session_state.pagina_atual = "Capa"
            st.rerun()
        menu = st.radio("Menu:", ["📊 Simulações", "📜 Histórico"], key="menu_nav")

    if menu == "📊 Simulações":
        st.title("📊 Simulação de Viagem")
        
        # Pesquisa de registros existentes
        with st.expander("🔍 BUSCAR REGISTRO"):
            id_sel = st.selectbox("ID:", ["---"] + (df_h.iloc[:,0].tolist() if not df_h.empty else []), key=f"sel_id_{uid}")
            if st.button("CARREGAR", key=f"btn_load_{uid}"):
                st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()

        d = st.session_state.dados_edit
        
        # Formulário da Simulação
        l1, l2, l3 = st.columns(3)
        v_emp = l1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0, key=f"emp_{uid}")
        
        try:
            b_val = d.get('Balsas', '[]')
            b_def = ast.literal_eval(b_val) if '[' in str(b_val) else []
        except: b_def = []
        
        v_bal = l2.multiselect("Comboio de Balsas", lista_balsas, default=[b for b in b_def if b in lista_balsas], key=f"bal_{uid}")
        v_com = l3.text_input("Comandante", value=d.get('Comandante', ""), key=f"com_{uid}")

        l4, l5, l6 = st.columns(3)
        oris = sorted(list(set([r[0] for r in lista_rotas if r])))
        dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
        v_ori = l4.selectbox("Origem", oris, key=f"ori_{uid}")
        v_des = l5.selectbox("Destino", dess, key=f"des_{uid}")
        v_chf = l6.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""), key=f"chf_{uid}")

        l7, l8, l9 = st.columns(3)
        v_vol = l7.number_input("Volume (M³)", value=0.0, key=f"vol_{uid}")
        v_fat = l8.number_input("Faturamento (R$)", value=0.0, key=f"fat_{uid}")
        v_hor = l9.number_input("Horímetro", value=0.0, key=f"hor_{uid}")

        status = "APROVADO" if v_fat >= 50000 else "ANÁLISE"
        st.write(f"**STATUS OPERACIONAL:** {status}")

        if st.button("✅ FINALIZAR E GERAR O.S. (PDF)", key=f"btn_pdf_{uid}"):
            dados_pdf = {
                "ID": d.get('ID', datetime.now().strftime("VGM-%H%M")),
                "Empurrador": v_emp, "Balsas": ", ".join(v_bal),
                "Rota": f"{v_ori} x {v_des}", "Faturamento": f"R$ {v_fat:,.2f}", "Status": status
            }
            pdf_bytes = gerar_pdf_os(dados_pdf)
            st.download_button("📥 BAIXAR O.S. EM PDF", pdf_bytes, "Ordem_Servico.pdf", "application/pdf", key=f"btn_dw_{uid}")

    elif menu == "📜 Histórico":
        st.title("📜 Histórico de Viagens")
        if not df_h.empty:
            st.dataframe(df_h, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado encontrado.")
