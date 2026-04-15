import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast
import uuid

# --- 1. CONFIGURAÇÕES E ESTILO (LAYOUT LIMPO) ---
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

st.markdown("""
    <style>
    .block-container { max-width: 1150px; padding-top: 40px; margin: auto; }
    .stMultiSelect div[data-baseweb="select"] > div:first-child { max-height: 180px; overflow-y: auto; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; height: 3em; border-radius: 8px; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONEXÃO COM A PLANILHA ---
def conectar():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")

@st.cache_data(ttl=60)
def carregar_dados_pco():
    try:
        sh = conectar()
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        hist = sh.worksheet("Historico").get_all_values()
        df = pd.DataFrame(hist[1:], columns=hist[0]) if len(hist) > 1 else pd.DataFrame()
        return ativos, balsas, rotas, df
    except:
        return [], [], [], pd.DataFrame()

# --- 3. GERADOR DE PDF ---
def criar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 15, "ORDEM DE SERVIÇO - TRANSDOURADA", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    for k, v in dados.items():
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(50, 10, f" {k}", border=1, fill=True)
        pdf.cell(0, 10, f" {v}", border=1, ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- 4. LÓGICA DO SISTEMA ---
if 'pagina' not in st.session_state: st.session_state.pagina = "Sistema"
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}

ativos, lista_balsas, lista_rotas, df_h = carregar_dados_pco()

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Placeholder_logo.svg/1024px-Placeholder_logo.svg.png", width=150) # Substitua pela sua logo
    menu = st.radio("Selecione:", ["📊 Simulações", "📜 Histórico"])

if menu == "📊 Simulações":
    st.title("📊 Simulador de Operação")
    
    # BUSCA
    with st.expander("🔍 Pesquisar Registro"):
        id_sel = st.selectbox("ID Viagem:", ["---"] + (df_h.iloc[:,0].tolist() if not df_h.empty else []))
        if st.button("Carregar"):
            st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
            st.rerun()

    d = st.session_state.dados_edit
    
    # --- LAYOUT DE CAMPOS SOLTOS (SEM FORM) ---
    c1, c2, c3 = st.columns([1, 2, 1])
    v_emp = c1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
    
    # Tratamento para carregar as 15 balsas do histórico se houver
    try: b_def = ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else []
    except: b_def = []
    v_bal = c2.multiselect("Comboio (12 a 15 Balsas)", lista_balsas, default=[b for b in b_def if b in lista_balsas])
    v_com = c3.text_input("Comandante", value=d.get('Comandante', ""))

    c4, c5, c6 = st.columns(3)
    oris = sorted(list(set([r[0] for r in lista_rotas if r])))
    dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
    v_ori = c4.selectbox("Origem", oris, index=oris.index(d['Origem']) if d.get('Origem') in oris else 0)
    v_des = c5.selectbox("Destino", dess, index=dess.index(d['Destino']) if d.get('Destino') in dess else 0)
    v_chf = c6.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

    c7, c8, c9 = st.columns(3)
    v_vol = c7.number_input("Volume M³", value=float(d.get('Volume', 0.0)), step=100.0)
    v_fat = c8.number_input("Faturamento (R$)", value=float(d.get('Faturamento', 0.0)))
    v_hor = c9.number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

    v_obs = st.text_area("Observações", value=d.get('Observações', ""))

    st.write("---")
    if st.button("🚀 FINALIZAR, SALVAR E GERAR O.S."):
        if not v_bal:
            st.warning("Selecione as balsas do comboio!")
        else:
            # Formatação solicitada
            vol_formatado = f"{v_vol:,.0f}".replace(",", ".")
            data_viagem = datetime.now().strftime("%d/%m/%Y %H:%M")
            id_gera = str(uuid.uuid4())[:8].upper()

            # SALVAR NA PLANILHA
            try:
                sh = conectar()
                ws = sh.worksheet("Historico")
                nova_linha = [id_gera, data_viagem, v_emp, str(v_bal), v_com, v_ori, v_des, vol_formatado, v_fat, v_hor, v_obs]
                ws.append_row(nova_linha)
                st.cache_data.clear() # Limpa o cache para o histórico atualizar
                
                # GERAR PDF
                dados_pdf = {
                    "ID Viagem": id_gera, "Data": data_viagem, "Empurrador": v_emp,
                    "Balsas": ", ".join(v_bal), "Rota": f"{v_ori} x {v_des}",
                    "Volume M³": vol_formatado, "Faturamento": f"R$ {v_fat:,.2f}"
                }
                pdf_bytes = criar_pdf(dados_pdf)
                
                st.success(f"✅ Viagem {id_gera} salva com sucesso!")
                st.download_button("📥 BAIXAR PDF DA O.S.", pdf_bytes, f"OS_{id_gera}.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

elif menu == "📜 Histórico":
    st.title("📜 Histórico de Viagens")
    if not df_h.empty:
        st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado registrado.")
