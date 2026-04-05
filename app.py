import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# ==========================================
# # 01 - CONFIGURAÇÕES GERAIS E ESTILO #
# ==========================================
st.set_page_config(page_title="ZION - PCO", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-left: 1rem; padding-right: 1rem;}
    
    /* Fixa largura de 5cm (190px) */
    div[data-testid="stSelectbox"], 
    div[data-testid="stTextInput"], 
    div[data-testid="stNumberInput"], 
    div[data-testid="stMultiSelect"] {
        width: 190px !important;
    }
    
    /* APROXIMAÇÃO HORIZONTAL: Força as colunas a ficarem juntas */
    [data-testid="column"] {
        width: 200px !important; 
        flex: none !important;
        margin-right: -10px !important; /* Puxa um campo para perto do outro */
    }
    
    /* Compacta verticalmente */
    div.row-widget.stHorizontal { gap: 0.1rem; }
    label { font-size: 12px !important; font-weight: bold; margin-bottom: -0.8rem !important; }
    
    /* Botões */
    .stButton > button { width: 190px !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# # 02 - CONEXÃO E SALVAMENTO #
# ==========================================
@st.cache_resource
def conectar_google():
    try:
        s = st.secrets["gcp_service_account"]
        pk = s["private_key"].strip().replace("\\n", "\n")
        creds_dict = dict(s)
        creds_dict["private_key"] = pk
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

def salvar_historico(client, dados):
    try:
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        sh = client.open_by_key(ID_PLANILHA)
        wks = sh.worksheet("Historico")
        wks.append_row(dados)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# ==========================================
# # 03 - FUNÇÃO GERAR PDF #
# ==========================================
def gerar_pdf_bytes(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "ZION - ORDEM DE VIAGEM", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for chave, valor in dados.items():
        pdf.cell(200, 8, f"{chave}: {valor}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# # 04 - EXECUÇÃO #
# ==========================================
st.title("🚢 ZION - Gestão PCO")
client = conectar_google()

if client:
    def buscar_dados(aba):
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        sh = client.open_by_key(ID_PLANILHA)
        data = sh.worksheet(aba).get_all_values()
        return pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame()

    df_ativos = buscar_dados("Ativos")
    df_balsas = buscar_dados("Balsas")
    df_rotas  = buscar_dados("Rotas")

    t_sim, t_ativos, t_balsas, t_rotas = st.tabs(["📊 Simulações", "Ativos", "Balsas", "Rotas"])

    with t_sim:
        id_vgn = datetime.now().strftime("VGN-%Y%m%d-%H%M")
        st.subheader(f"Nº: {id_vgn}")
        
        with st.form("form_pco"):
            c1, c2, c3 = st.columns(3)
            v_emp = c1.selectbox("Empurrador", df_ativos.iloc[:,0].tolist() if not df_ativos.empty else ["-"])
            v_bal = c2.multiselect("Balsas", df_balsas.iloc[:,0].tolist() if not df_balsas.empty else ["-"])
            v_com = c3.text_input("Comandante")

            c4, c5, c6 = st.columns(3)
            v_ori = c4.selectbox("Origem", df_rotas.iloc[:,0].unique().tolist() if not df_rotas.empty else ["-"])
            v_des = c5.selectbox("Destino", df_rotas.iloc[:,1].unique().tolist() if not df_rotas.empty else ["-"])
            v_chf = c6.text_input("Chefe de Máquinas")

            c7, c8, c9 = st.columns(3)
            v_vol = c7.number_input("Volume", min_value=0.0)
            v_fat = c8.number_input("Faturamento (R$)", min_value=0.0)
            v_hor = c9.number_input("Horímetro", min_value=0.0)

            c10, c11 = st.columns(2)
            v_tmp = c10.number_input("Tempo (H)", min_value=0)
            v_cbm = c11.number_input("Combustível (L)", min_value=0)

            btn = st.form_submit_button("VALIDAR E SALVAR")

        if btn:
            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            lista_sheets = [id_vgn, v_emp, ", ".join(v_bal), v_com, v_ori, v_des, v_chf, v_vol, v_fat, v_hor, v_tmp, v_cbm, agora]
            
            if salvar_historico(client, lista_sheets):
                st.success("✅ Registrado no Google Sheets!")
                
                # PDF
                dados_pdf = {"Viagem": id_vgn, "Empurrador": v_emp, "Comandante": v_com, "Rota": f"{v_ori} x {v_des}", "Data": agora}
                pdf_bytes = gerar_pdf_bytes(dados_pdf)
                
                col_a, col_b = st.columns(2)
                col_a.download_button("📥 Baixar PDF", data=pdf_bytes, file_name=f"{id_vgn}.pdf", mime="application/pdf")
                col_b.button("📧 Enviar E-mail")

    with t_ativos: st.dataframe(df_ativos, use_container_width=True)
    with t_balsas: st.dataframe(df_balsas, use_container_width=True)
    with t_rotas:  st.dataframe(df_rotas, use_container_width=True)
