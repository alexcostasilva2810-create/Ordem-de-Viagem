import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast
import uuid

# --- CONFIGURAÇÃO E LAYOUT (MANTIDO CONFORME VÍDEO) ---
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

st.markdown("""
    <style>
    .block-container { max-width: 1150px; padding-top: 40px; margin: auto; }
    .stMultiSelect div[data-baseweb="select"] > div:first-child { max-height: 180px; overflow-y: auto; }
    .stButton > button { background-color: #073763; color: white; font-weight: bold; width: 100%; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

def conectar():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")

@st.cache_data(ttl=60)
def carregar_dados():
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

# --- PDF PROFISSIONAL COM BORDAS E ASSINATURA ---
class PDF_PCO(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287) # Borda externa da página
        self.set_font('Arial', 'B', 16)
        self.set_text_color(7, 55, 99)
        self.cell(0, 15, 'ORDEM DE SERVICO - TRANSDOURADA', align='C', ln=True)
        self.ln(5)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.cell(0, 10, f'Registro gerado em: {agora} - Local: Belem/PA', align='C')

def gerar_pdf_profissional(dados):
    pdf = PDF_PCO()
    pdf.add_page()
    pdf.set_font("Arial", "B", 10)
    
    # Organização dos dados em tabela no PDF
    for chave, valor in dados.items():
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(60, 10, f" {chave}:", border=1, fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f" {valor}", border=1, ln=True)
        pdf.set_font("Arial", "B", 10)
    
    # Campo de Assinatura
    pdf.ln(20)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
    pdf.cell(0, 5, "Assinatura do Responsavel", align='C')
    
    return pdf.output(dest="S").encode("latin-1")

# --- INTERFACE ---
if 'dados_edit' not in st.session_state: st.session_state.dados_edit = {}
ativos, lista_balsas, lista_rotas, df_h = carregar_dados()

with st.sidebar:
    menu = st.radio("Selecione:", ["📊 Simulações", "📜 Histórico"])

if menu == "📊 Simulações":
    st.title("📊 Simulador de Operação")
    
    with st.expander("🔍 Pesquisar Registro"):
        id_sel = st.selectbox("ID Viagem:", ["---"] + (df_h.iloc[:,0].tolist() if not df_h.empty else []))
        if st.button("Carregar Dados"):
            st.session_state.dados_edit = df_h[df_h.iloc[:, 0] == id_sel].iloc[0].to_dict()
            st.rerun()

    d = st.session_state.dados_edit

    # --- CAMPOS (VOLUME IGUAL AO COMBUSTÍVEL) ---
    col1, col2, col3 = st.columns([1, 2, 1])
    v_emp = col1.selectbox("Empurrador", ativos, index=ativos.index(d['Empurrador']) if d.get('Empurrador') in ativos else 0)
    try: b_def = ast.literal_eval(d.get('Balsas', '[]')) if '[' in str(d.get('Balsas')) else []
    except: b_def = []
    v_bal = col2.multiselect("Balsas (Comboio)", lista_balsas, default=[b for b in b_def if b in lista_balsas])
    v_com = col3.text_input("Comandante", value=d.get('Comandante', ""))

    col4, col5, col6 = st.columns(3)
    oris = sorted(list(set([r[0] for r in lista_rotas if r])))
    dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
    v_ori = col4.selectbox("Origem", oris, index=oris.index(d['Origem']) if d.get('Origem') in oris else 0)
    v_des = col5.selectbox("Destino", dess, index=dess.index(d['Destino']) if d.get('Destino') in dess else 0)
    v_chf = col6.text_input("Chefe de Máquinas", value=d.get('Chefe de Máquinas', ""))

    col7, col8, col9 = st.columns(3)
    # VOLUME M³ AGORA É INTEIRO IGUAL AO COMBUSTÍVEL
    v_vol = col7.number_input("Volume M³", value=int(str(d.get('Volume', 0)).replace('.','')) if d.get('Volume') else 0)
    v_fat = col8.number_input("Faturamento (R$)", value=float(d.get('Faturamento', 0.0)))
    v_hor = col9.number_input("Horímetro", value=float(d.get('Horímetro', 0.0)))

    col10, col11, col12 = st.columns(3)
    v_tem = col10.number_input("Tempo Previsto (H)", value=int(d.get('Tempo (H)', 0)))
    v_combus = col11.number_input("Combustivel (L)", value=int(d.get('Combustivel (L)', 0)))
    v_custo = col12.number_input("Custo Diesel (R$)", value=float(d.get('Custo Diesel', 0.0)))

    v_obs = st.text_area("Observações", value=d.get('Observações', ""))

    if st.button("🚀 FINALIZAR, GUARDAR E GERAR O.S."):
        if not v_bal:
            st.error("Selecione o comboio!")
        else:
            vol_format = f"{v_vol:,.0f}".replace(",", ".")
            id_v = str(uuid.uuid4())[:8].upper()
            data_v = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            # SALVAR NA PLANILHA
            try:
                sh = conectar()
                ws = sh.worksheet("Historico")
                ws.append_row([id_v, data_v, v_emp, str(v_bal), v_com, v_ori, v_des, vol_format, v_fat, v_hor, v_tem, v_combus, v_custo, v_obs])
                st.cache_data.clear()
                
                # DICIONÁRIO COMPLETO PARA O PDF
                dados_completos = {
                    "ID Viagem": id_v, "Data": data_v, "Empurrador": v_emp, "Comboio": ", ".join(v_bal),
                    "Comandante": v_com, "Chefe de Maquinas": v_chf, "Origem": v_ori, "Destino": v_des,
                    "Volume M³": vol_format, "Faturamento": f"R$ {v_fat:,.2f}", "Horimetro": v_hor,
                    "Tempo (H)": v_tem, "Combustivel (L)": v_combus, "Custo Diesel": f"R$ {v_custo:,.2f}",
                    "Observacoes": v_obs
                }
                
                pdf_bytes = gerar_pdf_profissional(dados_completos)
                st.success(f"✅ Viagem {id_v} Guardada!")
                st.download_button("📥 BAIXAR O.S. PROFISSIONAL", pdf_bytes, f"OS_{id_v}.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

elif menu == "📜 Histórico":
    st.title("📜 Histórico de Viagens")
    st.dataframe(df_h, use_container_width=True, hide_index=True)
