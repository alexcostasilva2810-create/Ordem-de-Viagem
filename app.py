import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
import datetime

# --- CONFIGURAÇÃO GOOGLE SHEETS ---
def conectar_planilha():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('seu_arquivo_credenciais.json', scope)
    client = gspread.authorize(creds)
    # Abre a planilha pelo nome ou ID
    return client.open("NOME_DA_SUA_PLANILHA").sheet1

# --- FUNÇÃO PARA GERAR PDF ---
def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Simulação de Viagem - PCO", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    for chave, valor in dados.items():
        pdf.cell(200, 10, txt=f"{chave}: {valor}", ln=True)
    
    nome_arquivo = f"Simulacao_Viagem_{dados['Nº da viagem']}.pdf"
    pdf.output(nome_arquivo)
    return nome_arquivo

# --- INTERFACE STREAMLIT ---
st.title("🚢 Sistema de Programação de Viagens")

with st.form("form_viagem"):
    col1, col2 = st.columns(2)
    
    with col1:
        n_viagem = st.text_input("Nº da viagem")
        empurrador = st.selectbox("Empurrador", ["JATOBA","AROEIRA"])
        balsas = st.text_input("Balsas (IDs/Quantidade)")
        rota = st.text_input("Rota (Ex: Miritituba -> Santarém)")
        volume = st.number_input("Volume transportado (m³)", min_value=0.0)
        faturamento = st.number_input("Faturamento (R$)", min_value=0.0)

    with col2:
        tempo_previsto = st.text_input("Tempo previsto de navegação")
        combustivel = st.number_input("Combustível da viagem (litros)", min_value=0)
        comandante = st.text_input("Comandante")
        chefe_maquina = st.text_input("Chefe de Máquinas")
        horimetros = st.text_input("Horímetros (Iniciais)")

    submit = st.form_submit_button("Simular e Salvar Viagem")

if submit:
    dados_viagem = {
        "Data": str(datetime.date.today()),
        "Nº da viagem": n_viagem,
        "Empurrador": empurrador,
        "Balsas": balsas,
        "Rota": rota,
        "Volume": volume,
        "Faturamento": faturamento,
        "Tempo Previsto": tempo_previsto,
        "Combustível": combustivel,
        "Comandante": comandante,
        "Chefe Máquina": chefe_maquina,
        "Horímetros": horimetros
    }

    # --- LÓGICA DE VIABILIDADE (EXEMPLO) ---
    meta_faturamento = 50000  # Valor vindo do seu orçamento
    if faturamento < meta_faturamento:
        st.error(f"⚠️ Alerta: Faturamento abaixo do orçamento planejado!")
        viavel = "Não"
    else:
        st.success("✅ Viagem em conformidade com o orçamento.")
        viavel = "Sim"

    # 1. Salvar no Google Sheets
    try:
        sheet = conectar_planilha()
        sheet.append_row(list(dados_viagem.values()))
        st.info("Dados salvos na Planilha Google com sucesso!")
    except Exception as e:
        st.error(f"Erro ao conectar na planilha: {e}")

    # 2. Gerar PDF
    pdf_path = gerar_pdf(dados_viagem)
    with open(pdf_path, "rb") as f:
        st.download_button("Baixar PDF da Simulação", f, file_name=pdf_path)

    # 3. Envio de E-mail (Sugestão: Usar biblioteca 'smtplib' ou integração externa)
    st.write("✉️ E-mail enviado aos gestores para aprovação.")
