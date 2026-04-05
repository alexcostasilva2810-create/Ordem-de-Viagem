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
        st.error(f"Erro na Conexão (Bloco 02): {e}")
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
            return pd.DataFrame(dados[1:], columns=dados[0])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# ==========================================
# # EXECUÇÃO PRINCIPAL #
# ==========================================
st.title("🚢 ZION - Gestão PCO Online")
client = conectar_google()

if client:
    # Carregando as bases de dados
    df_ativos = buscar_dados(client, "Ativos")
    df_balsas = buscar_dados(client, "Balsas")
    df_trip   = buscar_dados(client, "Tripulação")
    df_rotas  = buscar_dados(client, "Rotas")

    # # 04 - INTERFACE DE NAVEGAÇÃO (TABS)
    t_ativos, t_balsas, t_trip, t_rotas, t_sim = st.tabs([
        "📋 Ativos", "⛴️ Balsas", "👥 Tripulação", "📍 Rotas", "📊 Simulações"
    ])

    # # 05 a # 08 - VISUALIZAÇÃO DAS TABELAS
    with t_ativos: st.dataframe(df_ativos, use_container_width=True, hide_index=True)
    with t_balsas: st.dataframe(df_balsas, use_container_width=True, hide_index=True)
    with t_trip:   st.dataframe(df_trip, use_container_width=True, hide_index=True)
    with t_rotas:  st.dataframe(df_rotas, use_container_width=True, hide_index=True)

    # ==========================================
    # # 09 - BLOCO: SIMULAÇÕES (PCO) #
    # ==========================================
    with t_sim:
        st.subheader("🚀 Planejamento de Viagem")
        
        # Gerador Automático de Nº de Viagem
        id_viagem_auto = datetime.now().strftime("VGN-%Y%m%d-%H%M")
        
        with st.form("form_planejamento_viagem"):
            st.markdown(f"**Nº da Viagem:** `{id_viagem_auto}`")
            col1, col2 = st.columns(2)
            
            with col1:
                # Pega a 1ª coluna de cada DF para os dropdowns (evita erro de nome de coluna)
                lista_emp = df_ativos.iloc[:, 0].tolist() if not df_ativos.empty else ["Sem dados"]
                v_empurrador = st.selectbox("Empurrador", lista_emp)
                
                lista_bal = df_balsas.iloc[:, 0].tolist() if not df_balsas.empty else ["Sem dados"]
                v_balsas = st.multiselect("Balsas", lista_bal)
                
                lista_rot = df_rotas.iloc[:, 0].tolist() if not df_rotas.empty else ["Sem dados"]
                v_rota = st.selectbox("Rota", lista_rot)
                
                v_volume = st.number_input("Volume Transportado", min_value=0.0)
                v_faturamento = st.number_input("Faturamento (R$)", min_value=0.0)

            with col2:
                v_tempo = st.number_input("Tempo previsto de navegação (Horas)", min_value=0)
                v_combustivel = st.number_input("Combustível da viagem (litros)", min_value=0)
                v_comandante = st.text_input("Comandante")
                v_chefe = st.text_input("Chefe de Máquinas")
                v_horimetro = st.number_input("Horímetros (Inicial)", min_value=0.0)

            # O BOTÃO QUE FALTAVA (SUBMIT)
            btn_validar = st.form_submit_button("VALIDAR PLANEJAMENTO")

        if btn_validar:
            st.success(f"Viagem {id_viagem_auto} validada com sucesso!")
            
            # Rodapé de Ações
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.button("📥 Gerar PDF do Planejamento")
            with c2:
                st.button("📧 Enviar por E-mail")
                st.caption("Destinatário padrão: pco.gestao@zion.com")

else:
    st.error("Erro crítico: Verifique as credenciais no Bloco # 02.")
