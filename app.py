import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ==========================================
# # 01 - CONFIGURAÇÕES GERAIS #
# ==========================================
st.set_page_config(page_title="ZION - Gestão PCO", layout="wide")

# ==========================================
# # 02 - CONEXÃO E SEGURANÇA #
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
        st.error(f"Erro no Bloco # 02: {e}")
        return None

# ==========================================
# # 03 - MOTOR DE BUSCA DE DADOS #
# ==========================================
def buscar_dados(client, nome_aba):
    try:
        ID_PLANILHA = "1nhySCAEgddykCBXIDX84ASTJyFknHtBOi2m04EewHEw"
        sh = client.open_by_key(ID_PLANILHA)
        worksheet = sh.worksheet(nome_aba)
        dados = worksheet.get_all_values()
        if len(dados) > 1:
            # Assume que a primeira linha são os nomes das colunas
            return pd.DataFrame(dados[1:], columns=dados[0])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# ==========================================
# # MAIN APP - EXECUÇÃO #
# ==========================================
st.title("🚢 ZION - Gestão PCO Online")
st.markdown("---")

client = conectar_google()

if client:
    # Pré-carregamento dos dados para alimentar os dropdowns do Bloco 09
    df_ativos = buscar_dados(client, "Ativos")
    df_balsas = buscar_dados(client, "Balsas")
    df_trip   = buscar_dados(client, "Tripulação")
    df_rotas  = buscar_dados(client, "Rotas")

    # ==========================================
    # # 04 - INTERFACE DE NAVEGAÇÃO (TABS) #
    # ==========================================
    t_ativos, t_balsas, t_trip, t_rotas, t_sim = st.tabs([
        "📋 Ativos", "⛴️ Balsas", "👥 Tripulação", "📍 Rotas", "📊 Simulações"
    ])

    # # 05 - BLOCO: ATIVOS
    with t_ativos:
        st.subheader("Cadastro de Ativos")
        st.dataframe(df_ativos, use_container_width=True, hide_index=True)

    # # 06 - BLOCO: BALSAS
    with t_balsas:
        st.subheader("Cadastro de Balsas")
        st.dataframe(df_balsas, use_container_width=True, hide_index=True)

    # # 07 - BLOCO: TRIPULAÇÃO
    with t_trip:
        st.subheader("Cadastro de Tripulação")
        st.dataframe(df_trip, use_container_width=True, hide_index=True)

    # # 08 - BLOCO: ROTAS
    with t_rotas:
        st.subheader("Cadastro de Rotas")
        st.dataframe(df_rotas, use_container_width=True, hide_index=True)

    # ==========================================
    # # 09 - BLOCO: SIMULAÇÕES (PCO) #
    # ==========================================
    with t_sim:
        st.subheader("🚀 Planejamento de Viagem")
        
        # Nº da viagem automático baseado em Data e Hora
        id_viagem_auto = datetime.now().strftime("VGN-%Y%m%d-%H%M")
        
        with st.form("form_planejamento_pco"):
            st.markdown(f"**Nº da Viagem:** `{id_viagem_auto}`")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Dropdown Empurrador (Busca da aba Ativos)
                # IMPORTANTE: A coluna na planilha deve se chamar 'Nome'
                opcoes_emp = df_ativos['Nome'].unique() if not df_ativos.empty else ["Cadastre Ativos primeiro"]
                v_empurrador = st.selectbox("Empurrador", opcoes_emp)
                
                # Dropdown Balsas (Busca da aba Balsas)
                opcoes_bal = df_balsas['Nome'].unique() if not df_balsas.empty else ["Cadastre Balsas primeiro"]
                v_balsas = st.multiselect("Balsas", opcoes_bal)
                
                # Dropdown Rota (Busca da aba Rotas)
                opcoes_rot = df_rotas['Nome'].unique() if not df_rotas.empty else ["Cadastre Rotas primeiro"]
                v_rota = st.selectbox("Rota", opcoes_rot)
                
                v_volume = st.number_input("Volume Transportado", min_value=0.0, step=1.0)
                v_faturamento = st.number_input("Faturamento (R$)", min_value=0.0, step=100.0)

            with col2:
                v_tempo = st.number_input("Tempo previsto de navegação (Horas)", min_value=0)
                v_combustivel = st.number_input("Combustível da viagem (litros)", min_value=0)
                
                # Campos de preenchimento manual conforme solicitado
                v_comandante = st.text_input("Comandante")
                v_chefe_maquinas = st.text_input("Chefe de Máquinas")
                v_horimetro = st.number_input("Horímetros (Inicial)", min_value=0.0, step=0.1)

            # Botão de submissão do formulário
            enviado = st.form_submit_button("VALIDAR PLANEJAMENTO")

        if enviado:
            st.success(f"Planejamento da Viagem {id_viagem_auto} gerado com sucesso!")
            
            # Área de Ações Pós-Planejamento
            st.markdown("---")
            c_acao1, c_acao2 = st.columns(2)
            
            with c_acao1:
                # Placeholder para o PDF (necessário biblioteca fpdf no requirements.txt)
                st.button("📥 Gerar PDF do Planejamento")
            
            with c_acao2:
                # Placeholder para o E-mail
                st.button("📧 Enviar para Gestores")
                st.caption("Destinatário: gestao@zion.com.br (Exemplo)")

else:
    st.warning("Sistema Offline: Erro na conexão com o Google Sheets (Bloco # 02).")
