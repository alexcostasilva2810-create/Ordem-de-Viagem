import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# ==========================================
# # 01 - CONFIGURAÇÕES GERAIS #
# ==========================================
st.set_page_config(
    page_title="ZION - Gestão PCO",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# # 02 - CONEXÃO E SEGURANÇA (SECRETS) #
# ==========================================
@st.cache_resource
def conectar_google():
    try:
        s = st.secrets["gcp_service_account"]
        # Limpa a chave privada de caracteres invisíveis
        pk = s["private_key"].strip().replace("\\n", "\n")
        
        creds_dict = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": pk,
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro no Bloco # 02: {e}")
        return None

# ==========================================
# # 03 - MOTOR DE BUSCA DE DADOS #
# ==========================================
def buscar_dados(client, nome_aba):
    try:
        # ID da sua planilha Google
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        sh = client.open_by_key(ID_PLANILHA)
        worksheet = sh.worksheet(nome_aba)
        dados = worksheet.get_all_values()
        if len(dados) > 1:
            return pd.DataFrame(dados[1:], columns=dados[0])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro no Bloco # 03 (Aba {nome_aba}): {e}")
        return pd.DataFrame()

# ==========================================
# # MAIN APP - EXECUÇÃO #
# ==========================================
st.title("🚢 ZION - Gestão PCO Online")
st.markdown("---")

client = conectar_google()

if client:
    # ==========================================
    # # 04 - INTERFACE DE NAVEGAÇÃO (TABS) #
    # ==========================================
    t_ativos, t_balsas, t_trip, t_rotas, t_sim = st.tabs([
        "📋 Ativos", 
        "⛴️ Balsas", 
        "👥 Tripulação", 
        "📍 Rotas", 
        "📊 Simulações"
    ])

    # ==========================================
    # # 05 - BLOCO: ATIVOS #
    # ==========================================
    with t_ativos:
        st.subheader("Gerenciamento de Ativos")
        df_ativos = buscar_dados(client, "Ativos")
        if not df_ativos.empty:
            st.dataframe(df_ativos, use_container_width=True, hide_index=True)
        else:
            st.info("Aba 'Ativos' sem dados ou não encontrada.")

    # ==========================================
    # # 06 - BLOCO: BALSAS #
    # ==========================================
    with t_balsas:
        st.subheader("Frota de Balsas")
        df_balsas = buscar_dados(client, "Balsas")
        if not df_balsas.empty:
            st.dataframe(df_balsas, use_container_width=True, hide_index=True)
        else:
            st.info("Aba 'Balsas' sem dados ou não encontrada.")

    # ==========================================
    # # 07 - BLOCO: TRIPULAÇÃO #
    # ==========================================
    with t_trip:
        st.subheader("Controle de Tripulação")
        df_trip = buscar_dados(client, "Tripulação")
        if not df_trip.empty:
            st.dataframe(df_trip, use_container_width=True, hide_index=True)
        else:
            st.info("Aba 'Tripulação' sem dados ou não encontrada.")

    # ==========================================
    # # 08 - BLOCO: ROTAS #
    # ==========================================
    with t_rotas:
        st.subheader("Logística de Rotas")
        df_rotas = buscar_dados(client, "Rotas")
        if not df_rotas.empty:
            st.dataframe(df_rotas, use_container_width=True, hide_index=True)
        else:
            st.info("Aba 'Rotas' sem dados ou não encontrada.")

    # ==========================================
    # # 09 - BLOCO: SIMULAÇÕES #
    # ==========================================
   import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF # Precisará adicionar 'fpdf' no seu requirements.txt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --- FUNÇÃO AUXILIAR PARA GERAR PDF ---
def gerar_pdf_viagem(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "ZION - PLANEJAMENTO DE VIAGEM (PCO)", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    for chave, valor in dados.items():
        pdf.cell(200, 10, f"{chave}: {valor}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- DENTRO DA INTERFACE PRINCIPAL ---
with t_sim:
    st.header("📊 Simulador de Planejamento (PCO)")
    
    # 1. LÓGICA DE NÚMERO AUTOMÁTICO
    # Gera um ID baseado na data/hora para ser único
    id_automatico = datetime.now().strftime("VGN-%Y%m%d-%H%M")
    
    with st.form("form_simulacao"):
        st.info(f"Nº da Viagem Gerado: **{id_automatico}**")
        
        c1, c2 = st.columns(2)
        
        with c1:
            # DROPDOWN PUXANDO DOS ATIVOS (EMPURRADORES)
            lista_emp = df_ativos['Nome'].tolist() if not df_ativos.empty else ["Nenhum Ativo Cadastrado"]
            v_empurrador = st.selectbox("Empurrador", lista_emp)
            
            # DROPDOWN PUXANDO DAS BALSAS
            lista_bal = df_balsas['Nome'].tolist() if not df_balsas.empty else ["Nenhuma Balsa Cadastrada"]
            v_balsas = st.multiselect("Balsas", lista_bal)
            
            # DROPDOWN PUXANDO DAS ROTAS
            lista_rot = df_rotas['Nome'].tolist() if not df_rotas.empty else ["Nenhuma Rota Cadastrada"]
            v_rota = st.selectbox("Rota", lista_rot)
            
            v_volume = st.number_input("Volume Transportado", min_value=0.0)
            v_faturamento = st.number_input("Faturamento (R$)", min_value=0.0)

        with c2:
            v_tempo = st.number_input("Tempo Previsto de Navegação (Horas)", min_value=0)
            v_combustivel = st.number_input("Combustível da Viagem (Litros)", min_value=0)
            v_comandante = st.text_input("Comandante")
            v_chefe = st.text_input("Chefe de Máquinas")
            v_horimetro = st.number_input("Horímetro Inicial", min_value=0.0)

        submit = st.form_submit_button("Gerar Planejamento")

    if submit:
        # Dicionário com os dados consolidados
        dados_viagem = {
            "Nº Viagem": id_automatico,
            "Empurrador": v_empurrador,
            "Balsas": ", ".join(v_balsas),
            "Rota": v_rota,
            "Volume": v_volume,
            "Faturamento": f"R$ {v_faturamento:,.2f}",
            "Tempo Previsto": f"{v_tempo} h",
            "Combustivel": f"{v_combustivel} L",
            "Comandante": v_comandante,
            "Chefe de Maquinas": v_chefe,
            "Horimetro": v_horimetro
        }

        st.success("✅ Planejamento Concluído!")
        
        # --- BOTÕES DE EXPORTAÇÃO ---
        col_pdf, col_email = st.columns(2)
        
        with col_pdf:
            pdf_bytes = gerar_pdf_viagem(dados_viagem)
            st.download_button(
                label="📥 Baixar PDF da Viagem",
                data=pdf_bytes,
                file_name=f"Plano_{id_automatico}.pdf",
                mime="application/pdf"
            )
            
        with col_email:
            if st.button("📧 Enviar por E-mail aos Gestores"):
                # Aqui entra a lógica de SMTP (precisaremos das suas credenciais de email)
                st.warning("Configuração de SMTP pendente (preciso do seu e-mail de envio).")
else:
    st.warning("Aguardando conexão com o banco de dados (Bloco # 02).")
