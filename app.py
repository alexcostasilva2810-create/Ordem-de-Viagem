import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
from fpdf import FPDF
import ast

# =========================================================
# 1. DESIGN E CONFIGURAÇÃO
# =========================================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}

st.markdown("""
    <style>
    .block-container { max-width: 1050px; padding-top: 1rem; margin: auto; }
    /* Mantém os campos alinhados sem quebrar o grid */
    .stNumberInput, .stTextInput, .stSelectbox, .stMultiSelect { width: 220px !important; }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.7rem; }
    /* Permite que o campo de balsas cresça sem empurrar os vizinhos de forma desordenada */
    div[data-baseweb="select"] > div:first-child { max-height: none !important; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. FUNÇÕES DE DADOS E PDF
# =========================================================
def conectar():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=2)
def carregar_sistema():
    client = conectar()
    sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
    # Carrega Listas
    ativos = sh.worksheet("Ativos").col_values(1)[1:]
    balsas = sh.worksheet("Balsas").col_values(1)[1:]
    rotas_data = sh.worksheet("Rotas").get_all_values()[1:]
    # Carrega Histórico para Busca
    hist_data = sh.worksheet("Historico").get_all_values()
    df_h = pd.DataFrame(hist_data[1:], columns=hist_data[0]).loc[:, ~pd.Series(hist_data[0]).duplicated()]
    return ativos, balsas, rotas_data, df_h

class PDF_ZION(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287)
        try: self.image('icone ZION.png', x=10, y=8, w=20)
        except: pass
        self.set_font('Arial', 'B', 14)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'ORDEM DE VIAGEM - TRANSDOURADA', align='C', ln=True)
        self.ln(5)
    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 8)
        fuso_br = timezone(timedelta(hours=-3))
        agora = datetime.now(fuso_br).strftime("%d / %m / %Y   -   %H : %M : %S")
        self.cell(0, 10, f'Gerado em: {agora}', align='C')

def gerar_pdf_final(dados):
    pdf = PDF_ZION()
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
# 3. INTERFACE (ESTRUTURA 4X3 RESTAURADA)
# =========================================================
with st.sidebar:
    pagina = st.radio("MENU", ["📊 Simulações", "📜 Histórico"])

ativos, lista_balsas, lista_rotas, df_h = carregar_sistema()

if pagina == "📊 Simulações":
    st.title("ZION - Gestão PCO")
    
    with st.expander("🔍 BUSCAR REGISTRO PARA EDIÇÃO"):
        id_sel = st.selectbox("Selecione ID:", ["---"] + df_h.iloc[:, 0].tolist())
        if st.button("CARREGAR DADOS"):
            st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
            st.rerun()

    d = st.session_state.dados_edit
    v_id = d.get('ID', datetime.now().strftime("VGM %d%m-%H%M"))
    st.subheader(f"Registro: {v_id}")

    # --- LINHA 1 ---
    l1c1, l1c2, l1c3 = st.columns(3)
    v_emp = l1c1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
    try: b_def = ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else []
    except: b_def = []
    v_bal = l1c2.multiselect("Balsas", lista_balsas, default=b_def)
    v_com = l1c3.text_input("Comandante", value=d.get('Comandante', ""))

    # --- LINHA 2 (CORRIGIDA: SELECTBOX PARA ORIGEM E DESTINO) ---
    l2c1, l2c2, l2c3 = st.columns(3)
    oris = sorted(list(set([r[0] for r in lista_rotas if r[0]])))
    dess = sorted(list(set([r[1] for r in lista_rotas if r[1]])))
    v_ori = l2c1.selectbox("Origem", oris, index=oris.index(d['Origem']) if d.get('Origem') in oris else 0)
    v_des = l2c2.selectbox("Destino", dess, index=dess.index(d['Destino']) if d.get('Destino') in dess else 0)
    v_chf = l2c3.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

    # --- LINHA 3 ---
    l3c1, l3c2, l3c3 = st.columns(3)
    v_vol = l3c1.number_input("Volume (M³)", value=float(str(d.get('Volume','0')).replace('M³','').replace('.','').replace(',','.')) if d.get('Volume') else 0.0, format="%.3f")
    v_fat = l3c2.number_input("Faturamento (R$)", value=float(str(d.get('Faturamento','0')).replace('R$','').replace('.','').replace(',','.')) if d.get('Faturamento') else 0.0, format="%.2f")
    v_hor = l3c3.number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

    # --- LINHA 4 ---
    l4c1, l4c2, l4c3 = st.columns(3)
    v_tmp = l4c1.number_input("Tempo Previsto (H)", value=int(d.get('Tempo Previsto (H)', 0)))
    v_cbm = l4c2.number_input("Combustível (L)", value=int(d.get('Combustível (L)', 0)))
    v_dsl = l4c3.number_input("Custo Diesel (R$)", value=float(str(d.get('Custo Diesel','0')).replace('R$','').replace('.','').replace(',','.')) if d.get('Custo Diesel') else 0.0, format="%.2f")

    v_obs = st.text_area("Observações", value=d.get('Observações', ""))

    status = "Aprovado" if v_fat >= 50000 else "Analise"
    st.markdown(f"### STATUS: <span style='color:{'green' if status == 'Aprovado' else 'red'}'>{status}</span>", unsafe_allow_html=True)

    if st.button("FINALIZAR E GERAR PDF"):
        dados_pdf = {
            "ID Viagem": v_id, "Empurrador": v_emp, "Balsas": ", ".join(v_bal),
            "Comandante": v_com, "Chefe Máquinas": v_chf, "Rota": f"{v_ori} x {v_des}",
            "Volume": f"{v_vol:,.3f} M³", "Faturamento": f"R$ {v_fat:,.2f}",
            "Custo Diesel": f"R$ {v_dsl:,.2f}", "Status": status, "Observações": v_obs
        }
        st.success("Salvo com sucesso!")
        st.download_button("📥 BAIXAR ORDEM DE VIAGEM", gerar_pdf_final(dados_pdf), f"{v_id}.pdf")

elif pagina == "📜 Histórico":
    st.markdown("<style>.block-container { max-width: 100% !important; }</style>", unsafe_allow_html=True)
    st.title("📜 Histórico Completo")
    st.dataframe(df_h, use_container_width=True, hide_index=True)
