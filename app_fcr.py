import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# CONFIGURAÇÃO DE PÁGINA E CSS PREMIUM
# ==========================================
st.set_page_config(page_title="Dashboard de FCR", layout="wide", initial_sidebar_state="expanded")

# CSS customizado para os Cards de Métricas (Efeito Hover, Sombras, Bordas)
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="metric-container"] label {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
    }
    /* Estilização dos separadores */
    hr {
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 0;
        border-top: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 Dashboard Operacional: Cálculo de FCR")
st.markdown("Acompanhamento de First Contact Resolution e Reincidências da Operação")
st.markdown("---")

# --- LISTA FIXA DAS EQUIPES DE FCR ---
EQUIPES_FCR = [
    'Atendimento IA',
    'Atendimento Financeiro',
    'Atendimento Inicial',
    'CC - Online',
    'Atendimento Inicial - Pré-Qualificação Da Demanda'
]

# ==========================================
# BARRA LATERAL (Filtros)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2936/2936630.png", width=60) # Ícone de dashboard
    st.header("Parâmetros do Relatório")
    
    arquivo_carregado = st.file_uploader("📂 Importar Base de Dados (.csv)")
    
    if arquivo_carregado is not None:
        try:
            try:
                df = pd.read_csv(arquivo_carregado, sep=';', encoding='utf-8')
            except UnicodeDecodeError:
                arquivo_carregado.seek(0)
                df = pd.read_csv(arquivo_carregado, sep=';', encoding='latin1')
            
            # Limpeza
            df['Tipo de Solicitação'] = df['Tipo de Solicitação'].astype(str).str.strip()
            df['Solicitante'] = df['Solicitante'].astype(str).str.strip()
            
            coluna_atendente = 'Aberto Por' if 'Aberto Por' in df.columns else 'Atendente / Equipe'
            if coluna_atendente in df.columns:
                df[coluna_atendente] = df[coluna_atendente].astype(str).str.strip()
            
            # Filtro de Datas
            if 'Data da Abertura' in df.columns:
                df['Data da Abertura'] = df['Data da Abertura'].astype(str).str.strip()
                df['Data da Abertura'] = pd.to_datetime(df['Data da Abertura'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                
                datas_validas = df['Data da Abertura'].dropna()
                if not datas_validas.empty:
                    min_date = datas_validas.dt.date.min()
                    max_date = datas_validas.dt.date.max()
                    
                    st.markdown("### 📅 Período de Análise")
                    col_inicio, col_fim = st.columns(2)
                    data_inicio = col_inicio.date_input("Início", min_date)
                    data_fim = col_fim.date_input("Fim", max_date)
                    
                    mask = (df['Data da Abertura'].dt.date >= data_inicio) & (df['Data da Abertura'].dt.date <= data_fim)
                    df = df.loc[mask]
                
            st.markdown("### 🏢 Equipes FCR")
            equipes_disponiveis = df['Tipo de Solicitação'].unique().tolist()
            equipes_padrao_presentes = [e for e in EQUIPES_FCR if e in equipes_disponiveis]
            
            equipes_selecionadas = st.multiselect(
                "Selecionar equipes base:", 
                options=equipes_padrao_presentes, 
                default=equipes_padrao_presentes
            )

            if coluna_atendente in df.columns:
                st.markdown("### 👥 Gestão de Operadores")
                todos_atendentes = sorted(df[coluna_atendente].unique().tolist())
                atendentes_selecionados = st.multiselect(
                    "Filtrar equipe de atendimento:",
                    options=todos_atendentes,
                    default=todos_atendentes
                )
                if atendentes_selecionados:
                    df = df[df[coluna_atendente].isin(atendentes_selecionados)]
            
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

# ==========================================
# ÁREA PRINCIPAL (Resultados em Abas)
# ==========================================
if arquivo_carregado is not None and 'equipes_selecionadas' in locals():
    
    if df.empty:
        st.warning("⚠️ Não há registros para os filtros selecionados.")
    else:
        aba_time, aba_individual = st.tabs(["📊 VISÃO GERAL DO TIME", "👤 PERFORMANCE INDIVIDUAL"])
        
        df_fcr_time = df[df['Tipo de Solicitação'].isin(equipes_selecionadas)]
        
        # --- ABA 1: VISÃO GERAL ---
        with aba_time:
            total_geral_time = len(df)
            
            if not df_fcr_time.empty:
                fcr_unicos_time = df_fcr_time['Solicitante'].nunique()
                reincidencias_time = len(df_fcr_time) - fcr_unicos_time
                
                taxa_fcr_time = (fcr_unicos_time / total_geral_time) * 100 if total_geral_time > 0 else 0
                perc_reinc_time = (reincidencias_time / total_geral_time) * 100 if total_geral_time > 0 else 0
                
                # Cards de Métricas
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Geral (Demandas)", f"{total_geral_time:,}")
                col2.metric("Reincidências", f"{reincidencias_time:,}", f"{perc_reinc_time:.1f}% do fluxo", delta_color="inverse")
                col3.metric("Taxa Global FCR", f"{taxa_fcr_time:.2f}%", "Índice de Resolução", delta_color="normal")
                col4.metric("Solicitantes Únicos", f"{fcr_unicos_time:,}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Gráfico Premium com Plotly
                resumo_grafico = df_fcr_time.groupby('Tipo de Solicitação').agg(
                    Total=('Solicitante', 'count'),
                    Unicos=('Solicitante', 'nunique')
                ).reset_index()
                resumo_grafico['Reincidências'] = resumo_grafico['Total'] - resumo_grafico['Unicos']
                resumo_grafico.rename(columns={'Unicos': 'Solucionados (FCR)'}, inplace=True)
                
                # Preparar dados para o Plotly Express
                df_melted = resumo_grafico.melt(id_vars=['Tipo de Solicitação'], value_vars=['Solucionados (FCR)', 'Reincidências'], 
                                                var_name='Status', value_name='Quantidade')
                
                fig = px.bar(
                    df_melted, 
                    y='Tipo de Solicitação', 
                    x='Quantidade', 
                    color='Status',
                    orientation='h',
                    barmode='stack',
                    color_discrete_map={'Solucionados (FCR)': '#10b981', 'Reincidências': '#64748b'},
                    title="<b>Volume de Atendimentos: FCR vs Reincidências por Equipe</b>"
                )
                
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="Número de Solicitações",
                    yaxis_title="",
                    legend_title="",
                    font=dict(size=14, color="#334155"),
                    hovermode="y unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("Nenhum chamado das equipes de FCR atende aos filtros atuais.")
        
        # --- ABA 2: RESULTADO INDIVIDUAL ---
        with aba_individual:
            st.markdown("### 🏆 Ranking de Performance por Operador")
            
            dados_operadores = []
            for operador in df[coluna_atendente].unique():
                df_operador_total = df[df[coluna_atendente] == operador]
                total_op = len(df_operador_total)
                
                df_operador_fcr = df_fcr_time[df_fcr_time[coluna_atendente] == operador]
                unicos_op = df_operador_fcr['Solicitante'].nunique()
                reincidencias_op = len(df_operador_fcr) - unicos_op
                
                taxa_op = (unicos_op / total_op) * 100 if total_op > 0 else 0
                
                dados_operadores.append({
                    'Operador': operador,
                    'Volume Total': total_op,
                    'Únicos (FCR)': unicos_op,
                    'Reincidências': reincidencias_op,
                    'Taxa FCR (%)': taxa_op # Guardamos como número real para a barra de progresso
                })
            
            df_resultado_individual = pd.DataFrame(dados_operadores).sort_values(by='Taxa FCR (%)', ascending=False)
            
            # Nova Tabela com DataGrid nativo e Barras de Progresso!
            st.dataframe(
                df_resultado_individual,
                column_config={
                    "Operador": st.column_config.TextColumn("👤 Nome do Atendente", width="medium"),
                    "Volume Total": st.column_config.NumberColumn("📥 Volume Total", format="%d"),
                    "Únicos (FCR)": st.column_config.NumberColumn("✅ Únicos (FCR)", format="%d"),
                    "Reincidências": st.column_config.NumberColumn("🔁 Reincidências", format="%d"),
                    "Taxa FCR (%)": st.column_config.ProgressColumn(
                        "🚀 Taxa FCR (%)",
                        help="Porcentagem de chamados resolvidos no primeiro contato.",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                },
                hide_index=True,
                use_container_width=True
            )
        
        # --- EXPORTAÇÃO ---
        st.markdown("---")
        col_vazia, col_btn = st.columns([3, 1])
        with col_btn:
            base_fcr_limpa = df_fcr_time.drop_duplicates(subset=['Solicitante', 'Tipo de Solicitação'])
            csv_limpo = base_fcr_limpa.to_csv(index=False, sep=';', encoding='utf-8-sig')
            
            st.download_button(
                label="📥 Exportar Base Limpa (CSV)",
                data=csv_limpo,
                file_name="Base_FCR_Time_Filtrado.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )

elif arquivo_carregado is None:
    st.info("👈 Faça o upload do arquivo CSV no menu lateral para iniciar a análise dos dados.")