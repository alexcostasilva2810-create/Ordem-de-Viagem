import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import ast

# 1. CONFIGURAÇÕES E CONEXÃO
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

def conectar_planilha():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    return client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")

@st.cache_data(ttl=60)
def carregar_dados_sistema():
    try:
        sh = conectar_planilha()
        ativos = sh.worksheet("Ativos").col_values(1)[1:]
        balsas = sh.worksheet("Balsas").col_values(1)[1:]
        rotas = sh.worksheet("Rotas").get_all_values()[1:]
        hist = sh.worksheet("Historico").get_all_values()
        df = pd.DataFrame(hist[1:], columns=hist[0]) if len(hist) > 1 else pd.DataFrame()
        return ativos, balsas, rotas, df
    except:
        return [], [], [], pd.DataFrame()

# 2. FUNÇÃO PARA SALVAR NA PLANILHA
def salvar_na_planilha(dados_lista):
    sh = conectar_planilha()
    ws = sh.worksheet("Historico")
    ws.append_row(dados_lista)
    st.cache_data.clear() # Limpa o cache para atualizar o histórico na tela

# 3. GERADOR DE PDF REAL
def gerar_pdf_os(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "ORDEM DE SERVICO - ZION PCO", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for k, v in dados.items():
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(60, 10, f" {k}", border=1, fill=True)
        pdf.cell(0, 10, f" {v}", border=1, ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- INTERFACE ---
if 'pagina' not in st.session_state: st.session_state.pagina = "Sistema"
ativos, lista_balsas, lista_rotas, df_h = carregar_dados_sistema()

# Menu Lateral
with st.sidebar:
    menu = st.radio("Navegação", ["📊 Simulações", "📜 Histórico"])

if menu == "📊 Simulações":
    st.title("📊 Simulador de Operação")
    
    with st.form("pco_form"):
        # Layout de Campos
        c1, c2, c3 = st.columns([1, 2, 1])
        v_emp = c1.selectbox("Empurrador", ativos)
        v_bal = c2.multiselect("Comboio (12 a 15+)", lista_balsas)
        v_com = c3.text_input("Comandante")

        c4, c5, c6 = st.columns(3)
        oris = sorted(list(set([r[0] for r in lista_rotas if r])))
        dess = sorted(list(set([r[1] for r in lista_rotas if len(r)>1])))
        v_ori = c4.selectbox("Origem", oris)
        v_des = c5.selectbox("Destino", dess)
        v_chf = c6.text_input("Chefe de Máquinas")

        c7, c8, c9 = st.columns(3)
        # VOLUME FORMATADO: O usuário digita 150000 e o sistema trata
        v_vol = c7.number_input("Volume M³", value=0, step=1000)
        v_fat = c8.number_input("Faturamento (R$)", value=0.0)
        v_hor = c9.number_input("Horímetro", value=0.0)

        v_obs = st.text_area("Observações")
        
        submit = st.form_submit_button("🚀 FINALIZAR, SALVAR E GERAR PDF")

        if submit:
            if not v_bal:
                st.error("Selecione as balsas!")
            else:
                # 1. Formata Volume e Valores
                vol_formatado = f"{v_vol:,.0f}".replace(",", ".")
                data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # 2. Prepara dados para a Planilha (deve seguir a ordem das suas colunas)
                id_viagem = str(uuid.uuid4())[:8].upper()
                linha_planilha = [
                    id_viagem, data_hoje, v_emp, str(v_bal), v_com, v_ori, v_des, 
                    vol_formatado, v_fat, v_hor, v_obs
                ]
                
                # 3. Executa Ações
                salvar_na_planilha(linha_planilha)
                
                dados_pdf = {
                    "Data": data_hoje, "Empurrador": v_emp, "Comboio": ", ".join(v_bal),
                    "Rota": f"{v_ori} x {v_des}", "Volume M³": vol_formatado, "Faturamento": f"R$ {v_fat:,.2f}"
                }
                pdf_bytes = gerar_pdf_os(dados_pdf)
                
                st.success("✅ Dados salvos na planilha e PDF gerado!")
                st.download_button("📥 BAIXAR O.S. AGORA", pdf_bytes, f"OS_{id_viagem}.pdf", "application/pdf")

elif menu == "📜 Histórico":
    st.title("📜 Histórico de Viagens")
    if not df_h.empty:
        st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado registrado ainda.")
