import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import io

# ==========================================
# # 01 - CONFIGURAÇÃO E ESTILO #
# ==========================================
st.set_page_config(page_title="ZION - PCO", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-left: 2rem; }
    /* Estabilidade dos campos: 190px (~5cm) */
    .stSelectbox, .stTextInput, .stNumberInput, .stMultiSelect { max-width: 190px !important; }
    .element-container { margin-bottom: -0.3rem !important; }
    label { font-size: 13px !important; font-weight: bold; }
    /* Botões Padrão */
    .stButton > button { width: 190px !important; background-color: #073763; color: white; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# # 02 - FUNÇÕES DE SUPORTE #
# ==========================================
def obter_cliente():
    try:
        s = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except: return None

def enviar_email(destinatario, vgn_id, pdf_bytes):
    try:
        # Puxa credenciais dos Secrets
        remetente = st.secrets["email_config"]["usuario"]
        senha = st.secrets["email_config"]["senha"]
        
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = f"ZION PCO - Nova Viagem {vgn_id}"
        
        corpo = f"Segue em anexo o planejamento da viagem {vgn_id} gerado pelo sistema ZION."
        msg.attach(MIMEText(corpo, 'plain'))

        anexo = MIMEApplication(pdf_bytes, _subtype="pdf")
        anexo.add_header('Content-Disposition', 'attachment', filename=f"{vgn_id}.pdf")
        msg.attach(anexo)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro no envio: {e}")
        return False

@st.cache_data(ttl=300)
def carregar_dados(aba):
    client = obter_cliente()
    if client:
        sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        data = sh.worksheet(aba).get_all_values()
        return pd.DataFrame(data[1:], columns=data[0])
    return pd.DataFrame()

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
# # 03 - INTERFACE #
# ==========================================
st.title("🚢 ZION - Gestão PCO")

# E-mail de teste fixado
email_destino = "analista.pco@grupogdias.com.br"

df_atv = carregar_dados("Ativos")
df_bal = carregar_dados("Balsas")
df_rot = carregar_dados("Rotas")

t_sim, t_atv, t_bal, t_rot = st.tabs(["📊 Simulações", "Ativos", "Balsas", "Rotas"])

with t_sim:
    vgn_id = datetime.now().strftime("VGN-%Y%m%d-%H%M")
    st.subheader(f"Nº Registro: {vgn_id}")
    
    # Grid de inputs com colunas fantasmas para evitar que o layout "monte"
    c1, c2, c3, _ = st.columns([1, 1, 1, 5])
    v_emp = c1.selectbox("Empurrador", df_atv.iloc[:,0] if not df_atv.empty else ["-"])
    v_bal = c2.multiselect("Balsas", df_bal.iloc[:,0] if not df_bal.empty else [])
    v_com = c3.text_input("Comandante")

    c4, c5, c6, _ = st.columns([1, 1, 1, 5])
    v_ori = c4.selectbox("Origem", df_rot.iloc[:,0].unique() if not df_rot.empty else ["-"])
    v_des = c5.selectbox("Destino", df_rot.iloc[:,1].unique() if not df_rot.empty else ["-"])
    v_chf = c6.text_input("Chefe de Máquinas")

    c7, c8, c9, _ = st.columns([1, 1, 1, 5])
    v_vol = c7.number_input("Volume", min_value=0.0)
    v_fat = c8.number_input("Faturamento", min_value=0.0)
    v_hor = c9.number_input("Horímetro", min_value=0.0)

    c10, c11, _ = st.columns([1, 1, 6])
    v_tmp = c10.number_input("Tempo (H)", min_value=0)
    v_cbm = c11.number_input("Combustível (L)", min_value=0)

    st.write("---")
    
    if st.button("VALIDAR E SALVAR"):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        lista_dados = [vgn_id, v_emp, ", ".join(v_bal), v_com, v_ori, v_des, v_chf, v_vol, v_fat, v_hor, v_tmp, v_cbm, agora]
        
        # Tentativa de salvar no Sheets
        client = obter_cliente()
        try:
            sh = client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
            sh.worksheet("Historico").append_row(lista_dados)
            st.success("✅ Salvo com sucesso na planilha!")
        except Exception as e:
            st.warning("⚠️ Erro ao salvar no Sheets, mas você pode gerar o PDF abaixo.")

        # Gerar o PDF independente do salvamento
        dados_p = {"Viagem": vgn_id, "Empurrador": v_emp, "Comandante": v_com, "Rota": f"{v_ori} x {v_des}", "Data": agora}
        pdf_bytes = gerar_pdf(dados_p)
        
        st.write("### 📄 Ações")
        b1, b2, _ = st.columns([1, 1, 6])
        b1.download_button("📥 Baixar PDF", data=pdf_bytes, file_name=f"{vgn_id}.pdf")
        
        if b2.button("📧 Enviar E-mail"):
            if enviar_email(email_destino, vgn_id, pdf_bytes):
                st.success(f"E-mail enviado para {email_destino}")

# Outras abas
with t_atv: st.dataframe(df_atv, use_container_width=True)
with t_bal: st.dataframe(df_bal, use_container_width=True)
with t_rot: st.dataframe(df_rot, use_container_width=True)
