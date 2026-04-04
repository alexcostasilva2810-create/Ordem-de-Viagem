import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- CONFIGURAÇÃO DE PÁGINA E ESTILO ---
st.set_page_config(page_title="Gestão de Frota e Simulação PCO", layout="wide")

# --- FUNÇÃO DE CONEXÃO (UTILIZANDO SECRETS DO STREAMLIT) ---
def conectar_google():
    try:
        info_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(info_dict, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(creds)
        # Substitua pelo nome EXATO da sua planilha
        return client.open("BD O.S VG")
    except:
        return client.open_by_key("1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw")
        return None

# --- INTERFACE PRINCIPAL ---
st.title("🚢 Sistema Operacional de Navegação - PCO")

# Criação das abas (Sessões)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Simulador de Viagem", 
    "⚙️ Ativos (Empurradores)", 
    "🛶 Balsas", 
    "👨‍✈️ Equipe", 
    "📍 Rotas"
])

# Conectar à planilha uma vez para carregar os dados
doc = conectar_google()

# ---------------------------------------------------------
# SESSÃO 2: CADASTRO DE ATIVOS (EMPURRADORES)
# ---------------------------------------------------------
with tab2:
    st.subheader("Cadastro de Empurradores")
    with st.form("form_ativos"):
        nome_ativo = st.text_input("Nome do Empurrador (Ex: AROEIRA, JATOBA)")
        submit_ativo = st.form_submit_button("Cadastrar Ativo")
        if submit_ativo and doc:
            doc.worksheet("Ativos").append_row([nome_ativo])
            st.success(f"{nome_ativo} cadastrado!")

# ---------------------------------------------------------
# SESSÃO 3: CADASTRO DE BALSAS
# ---------------------------------------------------------
with tab3:
    st.subheader("Cadastro de Balsas")
    with st.form("form_balsas"):
        nome_balsa = st.text_input("Nome/ID da Balsa")
        cap_balsa = st.number_input("Capacidade (m³)", min_value=0.0)
        tipo_balsa = st.selectbox("Tipo de Carga", ["Grão", "Derivado"])
        submit_balsa = st.form_submit_button("Cadastrar Balsa")
        if submit_balsa and doc:
            doc.worksheet("Balsas").append_row([nome_balsa, cap_balsa, tipo_balsa])
            st.success(f"Balsa {nome_balsa} cadastrada!")

# ---------------------------------------------------------
# SESSÃO 4: EQUIPE (CMT / CH MAQ)
# ---------------------------------------------------------
with tab4:
    st.subheader("Cadastro de Tripulação")
    with st.form("form_equipe"):
        nome_func = st.text_input("Nome Completo")
        funcao = st.selectbox("Função", ["Comandante", "Chefe de Máquina"])
        submit_equipe = st.form_submit_button("Cadastrar Tripulante")
        if submit_equipe and doc:
            doc.worksheet("Tripulacao").append_row([nome_func, funcao])
            st.success("Tripulante cadastrado!")

# ---------------------------------------------------------
# SESSÃO 5: ROTAS
# ---------------------------------------------------------
with tab5:
    st.subheader("Cadastro de Rotas e Tempos")
    with st.form("form_rotas"):
        origem_destino = st.text_input("Rota (Ex: STM x MIR)")
        tempo_ref = st.number_input("Tempo Previsto (Horas)", min_value=0)
        submit_rota = st.form_submit_button("Cadastrar Rota")
        if submit_rota and doc:
            doc.worksheet("Rotas").append_row([origem_destino, tempo_ref])
            st.success("Rota salva!")

# ---------------------------------------------------------
# SESSÃO 1: SIMULADOR (PUXANDO DADOS DAS OUTRAS ABAS)
# ---------------------------------------------------------
with tab1:
    st.subheader("Nova Simulação de Viagem")
    
    if doc:
        # Puxando dados para os selects
        lista_ativos = doc.worksheet("Ativos").col_values(1)[1:]
        lista_balsas = doc.worksheet("Balsas").col_values(1)[1:]
        lista_cmts = [r[0] for r in doc.worksheet("Tripulacao").get_all_values() if r[1] == "Comandante"]
        lista_chefes = [r[0] for r in doc.worksheet("Tripulacao").get_all_values() if r[1] == "Chefe de Máquina"]
        lista_rotas = doc.worksheet("Rotas").get_all_values()[1:]
        dict_rotas = {r[0]: r[1] for r in lista_rotas}

        with st.form("form_simulador"):
            col1, col2 = st.columns(2)
            with col1:
                n_viagem = st.text_input("Nº da Viagem")
                emp_sel = st.selectbox("Empurrador", lista_ativos)
                balsa_sel = st.multiselect("Balsas no Comboio", lista_balsas)
                rota_sel = st.selectbox("Rota", list(dict_rotas.keys()))
                volume = st.number_input("Volume Total Planejado (m³)")
            
            with col2:
                faturamento = st.number_input("Faturamento Estimado (R$)")
                # Preenche automaticamente o tempo da rota selecionada
                tempo_estimado = dict_rotas.get(rota_sel, 0)
                st.info(f"Tempo estimado para esta rota: {tempo_estimado} horas")
                
                combustivel = st.number_input("Combustível Estimado (Litros)")
                cmt_sel = st.selectbox("Comandante", lista_cmts)
                chefe_sel = st.selectbox("Chefe de Máquinas", lista_chefes)
                horimetro = st.text_input("Horímetros Iniciais")

            if st.form_submit_button("Gerar Simulação e Salvar"):
                # Lógica de Viabilidade (Exemplo de cruzamento)
                if faturamento > (combustivel * 6.0): # Exemplo: Faturamento vs Gasto Diesel
                    st.success("✅ Viagem Viável!")
                    status = "VIÁVEL"
                else:
                    st.warning("⚠️ Fora dos Parâmetros!")
                    status = "NÃO VIÁVEL"
                
                # Salvar na aba Simulacoes
                doc.worksheet("Simulacoes").append_row([
                    n_viagem, emp_sel, str(balsa_sel), rota_sel, volume, 
                    faturamento, tempo_estimado, combustivel, cmt_sel, 
                    chefe_sel, horimetro, status, str(datetime.date.today())
                ])
    else:
        st.warning("Conecte a Planilha Google para habilitar o simulador.")
