import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import time

# ==========================================
# # 01 - CONFIGURAÇÃO E ESTILO #
# ==========================================
st.set_page_config(page_title="ZION - PCO", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-left: 1.5rem; }
    div[data-testid="stSelectbox"], div[data-testid="stTextInput"], 
    div[data-testid="stNumberInput"], div[data-testid="stMultiSelect"] {
        width: 190px !important;
    }
    [data-testid="column"] {
        width: 210px !important; 
        flex: none !important;
        margin-right: 15px !important;
    }
    .element-container { margin-bottom: -0.5rem !important; }
    label { font-size: 12px !important; font-weight: bold; }
    .stButton > button { width: 190px !important; background-color: #003366; color: white; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# # 02 - CONEXÃO E SALVAMENTO COM RETRY #
# ==========================================
@st.cache_resource
def conectar():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except: return None

def salvar_no_sheets(client, lista_dados):
    """Tenta salvar e se falhar tenta mais uma vez após 2 segundos"""
    ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
    for tentativa in range(2):
        try:
            sh = client.open_by_key(ID_PLANILHA)
            wks = sh.worksheet("Historico")
            wks.append_row(lista_dados)
            return True
        except Exception as e:
            if tentativa == 0:
                time.sleep(2) # Espera o Google "respirar"
                continue
            st.error(f"Erro persistente do Google Sheets: {e}")
            return False

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "ZION - ORDEM DE VIAGEM", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for k, v in dados.items():
        pdf.cell(200, 8, f"{k}: {v}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# # 03 - APP #
# ==========================================
st.title("🚢 ZION - Gestão PCO")
client = conectar()

if client:
    ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
    try:
        sh = client.open_by_key(ID_PLANILHA)
        # Carregamento de dados para os menus
        df_atv = pd.DataFrame(sh.worksheet("Ativos").get_all_values()[1:], columns=sh.worksheet("Ativos").get_all_values()[0])
        df_bal = pd.DataFrame(sh.worksheet("Balsas").get_all_values()[1:], columns=sh.worksheet("Balsas").get_all_values()[0])
        df_rot = pd.DataFrame(sh.worksheet("Rotas").get_all_values()[1:], columns=sh.worksheet("Rotas").get_all_values()[0])
    except Exception as e:
        st.error(f"Erro ao ler planilhas base: {e}")
        st.stop()

    tabs = st.tabs(["📊 Simulações", "Ativos", "Balsas", "Rotas"])

    with tabs[0]:
        vgn_id = datetime.now().strftime("VGN-%Y%m%d-%H%M")
        st.subheader(f"Nº: {vgn_id}")
        
        # Grid de Entradas
        c1, c2, c3 = st.columns(3)
        v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
        v_bal_sel = c2.multiselect("Balsas", df_bal.iloc[:,0] if not df_bal.empty else [])
        v_com = c3.text_input("Comandante")

        c4, c5, c6 = st.columns(3)
        v_ori = c4.selectbox("Origem", df_rot.iloc[:,0].unique() if not df_rot.empty else ["-"])
        v_des = c5.selectbox("Destino", df_rot.iloc[:,1].unique() if not df_rot.empty else ["-"])
        v_chf = c6.text_input("Chefe de Máquinas")

        c7, c8, c9 = st.columns(3)
        v_vol = c7.number_input("Volume", min_value=0.0)
        v_fat = c8.number_input("Faturamento (R$)", min_value=0.0)
        v_hor = c9.number_input("Horímetro", min_value=0.0)

        c10, c11 = st.columns(2)
        v_tmp = c10.number_input("Tempo (H)", min_value=0)
        v_cbm = c11.number_input("Combustível (L)", min_value=0)

        st.markdown("---")
        
        if st.button("VALIDAR E SALVAR"):
            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            lista_final = [vgn_id, v_emp, ", ".join(v_bal_sel), v_com, v_ori, v_des, v_chf, v_vol, v_fat, v_hor, v_tmp, v_cbm, agora]
            
            # Tenta salvar no Sheets
            sucesso = salvar_no_sheets(client, lista_final)
            
            if sucesso:
                st.success(f"✅ Viagem {vgn_id} registrada com sucesso no Histórico!")
            else:
                st.warning("⚠️ Dados não salvos no Sheets (Erro de API), mas você pode gerar o PDF abaixo.")

            # Gera dados para PDF
            dados_pdf = {"N Viagem": vgn_id, "Empurrador": v_emp, "Comandante": v_com, "Data": agora}
            pdf_bytes = gerar_pdf(dados_pdf)
            
            # BOTÕES FINAIS (Sempre aparecem após clicar em validar)
            st.write("### Ações Disponíveis:")
            col_fim1, col_fim2 = st.columns(2)
            col_fim1.download_button("📥 Baixar PDF", data=pdf_bytes, file_name=f"{vgn_id}.pdf", mime="application/pdf")
            
            if col_fim2.button("📧 Enviar E-mail"):
                st.info("E-mail enviado para a central de monitoramento (Simulação).")

    # Demais abas apenas para conferência
    with tabs[1]: st.dataframe(df_atv, use_container_width=True)
    with tabs[2]: st.dataframe(df_bal, use_container_width=True)
    with tabs[3]: st.dataframe(df_rot, use_container_width=True)
