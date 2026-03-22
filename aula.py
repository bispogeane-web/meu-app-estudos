import streamlit as st
import google.generativeai as genai
import json

st.set_page_config(page_title="Português Total", page_icon="📚", layout="wide")

# Configuração
GOOGLE_API_KEY = "AIzaSyAa4B9AEiPVWcBxGtFPS2xhx1oUJJVMmdE"
genai.configure(api_key=GOOGLE_API_KEY)
modelo = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})

# 1. Estrutura do Syllabus Padrão
areas_ordenadas = [
    "Morfologia - Língua Portuguesa", 
    "Sintaxe", 
    "Produção de Textos", 
    "Ortografia", 
    "Fonologia", 
    "Pragmática", 
    "Estilística"
]

opcoes_topicos = {
    "Morfologia - Língua Portuguesa": ["Substantivos e suas flexões", "Adjetivos (Grau e Flexão)", "Uso dos Pronomes", "Conjugação Verbal", "Uso das Conjunções", "Estrutura e Formação de Palavras", "Advérbios", "Uso de Preposições", "🏆 SIMULADO FINAL - Morfologia"],
    "Sintaxe": ["Termos Essenciais da Oração (Sujeito e Predicado)", "Crase (Regras e Pegadinhas)", "Concordância Verbal", "Concordância Nominal", "Regência Verbal e Nominal", "Pontuação (Uso da Vírgula)", "Colocação Pronominal", "Orações Subordinadas", "🏆 SIMULADO FINAL - Sintaxe"],
    "Produção de Textos": ["Tipologia Textual", "Gêneros Textuais", "Coesão e Coerência", "Intertextualidade", "Redação Oficial (Manual da Presidência)", "🏆 SIMULADO FINAL - Produção"],
    "Ortografia": ["Novo Acordo Ortográfico", "Uso do Porquê", "Uso do Hífen", "Acentuação Gráfica", "Palavras Homônimas e Parônimas", "Mal ou Mau? Onde ou Aonde?", "🏆 SIMULADO FINAL - Ortografia"],
    "Fonologia": ["Encontros Vocálicos e Consonantais", "Dígrafos", "Divisão Silábica", "Ortoépia e Prosódia", "🏆 SIMULADO FINAL - Fonologia"],
    "Pragmática": ["Atos de Fala", "Funções da Linguagem", "Variação e Preconceito Linguístico", "Pressupostos e Subentendidos", "🏆 SIMULADO FINAL - Pragmática"],
    "Estilística": ["Figuras de Linguagem", "Vícios de Linguagem", "Sinônimos e Antônimos", "Polissemia", "🏆 SIMULADO FINAL - Estilística"]
}

# 2. Inicializando Variáveis de Sessão e Travas
if 'sessao_iniciada' not in st.session_state:
    st.session_state.area_desbloqueada_idx = 0
    st.session_state.topico_desbloqueado_idx = {i: 0 for i in range(len(areas_ordenadas))}
    
    st.session_state.aula_dados = None
    st.session_state.indice_questao_atual = 0
    st.session_state.errou_atual = False
    st.session_state.acertou_atual = False
    st.session_state.sessao_iniciada = True

def resetar_estudo():
    st.session_state.aula_dados = None
    st.session_state.indice_questao_atual = 0
    st.session_state.errou_atual = False
    st.session_state.acertou_atual = False

# 3. Sidebar com Filtros de Bloqueio Embutidos
st.sidebar.title("🛤️ Trilha de Aprendizagem")
st.sidebar.caption("Avance na plataforma acertando as baterias e os simulados.")

areas_liberadas = areas_ordenadas[:int(st.session_state.area_desbloqueada_idx) + 1]
area_escolhida = st.sidebar.selectbox("Escolha a Grande Área:", areas_liberadas)
area_idx = areas_ordenadas.index(area_escolhida)

topicos_da_area = opcoes_topicos[area_escolhida]
if area_idx < st.session_state.area_desbloqueada_idx:
    topicos_liberados = topicos_da_area
else:
    idx_max_topico = st.session_state.topico_desbloqueado_idx[area_idx]
    topicos_liberados = topicos_da_area[:int(idx_max_topico) + 1]

tema_escolhido = st.sidebar.selectbox("Escolha o Tópico específico:", topicos_liberados)
tema_idx = topicos_da_area.index(tema_escolhido)
is_simulado = "🏆 SIMULADO FINAL" in tema_escolhido

# 4. Tela Principal
st.title("📚 Português Total")
st.caption("Resolva a bateria inteira de exercícios para comprovar aprendizado e liberar o próximo bloco.")

if st.sidebar.button("Gerar Bateria" if not is_simulado else "INICIAR SIMULADO", on_click=resetar_estudo, type="primary"):
    with st.spinner("Preparando as questões das piores bancas para você..."):
        
        if is_simulado:
            prompt = f"""
            Aja como um professor especialista em concursos e crie um SIMULADO RIGOROSO sobre a área: "{area_escolhida}".
            Regras:
            1. NÃO gere aula teórica. Apenas uma fala inicial desafiadora.
            2. Gere EXATAMENTE 7 questões inéditas (nível FGV/FCC) misturando os tópicos dessa área.
            3. Responda em JSON EXATO com as chaves: "aula" (mensagem da professora), "questoes" (array com objetos contendo: "enunciado_questao", "opcoes" (com A a E), "resposta_correta" (só a letra) e "comentario_gabarito": "Explicacao...").
            """
        else:
            prompt = f"""
            Aja como um professor especialista em concursos e explique o tema: "{tema_escolhido}" ({area_escolhida}).
            Regras:
            1. Aula ágil, direta ao ponto e de alto nível.
            2. Forneça o MACETE INFALÍVEL.
            3. IMPORTANTE: Gere UMA BATERIA DE EXATAMENTE 5 QUESTÕES inéditas (múltipla escolha) sobre o tema.
            4. Responda em JSON EXATO com as chaves: "aula" (texto motivacional + teoria + macete em markdown), "questoes" (array com objetos contendo: "enunciado_questao", "opcoes" (com A a E), "resposta_correta" (só a letra) e "comentario_gabarito": "Explicacao rigorosa...").
            """
        
        try:
            resposta = modelo.generate_content(prompt)
            st.session_state.aula_dados = json.loads(resposta.text, strict=False)
        except Exception as e:
            st.error(f"Erro ao gerar material. Tente novamente! ({e})")

# 5. Lógica Iterativa de Bateria de Questões
if st.session_state.aula_dados:
    dados = st.session_state.aula_dados
    questoes = dados["questoes"]
    qtd_questoes = len(questoes)
    idx = st.session_state.indice_questao_atual
    
    if idx < qtd_questoes:
        q_atual = questoes[idx]
        
        with st.expander(f"📖 Aula / Recado do Professor", expanded=(idx == 0)):
            st.markdown(dados["aula"])
            
        st.divider()
        st.subheader(f"📝 Questão {idx + 1} de {qtd_questoes}")
        st.markdown(q_atual["enunciado_questao"])
        
        if not st.session_state.acertou_atual:
            lista_opcoes = [f"{letra}) {texto}" for letra, texto in q_atual["opcoes"].items()]
            resposta_usuario = st.radio("Sua resposta:", lista_opcoes, index=None, key=f"rad_{idx}")
            
            if st.button("Submeter Resposta"):
                if resposta_usuario:
                    if resposta_usuario[0] == q_atual["resposta_correta"]:
                        st.session_state.acertou_atual = True
                        st.session_state.errou_atual = False
                    else:
                        st.session_state.errou_atual = True
                    st.rerun()
                else:
                    st.warning("Marque uma alternativa!")
            
            if st.session_state.errou_atual:
                st.error('❌ Errou! Esse é um erro clássico.')
                st.warning(f"**Comentário do Professor:**\n{q_atual['comentario_gabarito']}")
                st.info("Você precisa acertar a questão para avançar. Revise o comentário e tente de novo!")
                
        else:
            st.success(f"🎉 Exato! A letra correta é a **{q_atual['resposta_correta']}**.")
            st.info(f"💡 **Fixação da Regra:**\n{q_atual['comentario_gabarito']}")
            
            if st.button("Avançar para Próxima Questão" if idx < qtd_questoes - 1 else "✅ FINALIZAR BATERIA", type="primary"):
                st.session_state.indice_questao_atual += 1
                st.session_state.acertou_atual = False
                st.session_state.errou_atual = False
                
                # Fim da bateria - Lógica de Desbloqueios
                if st.session_state.indice_questao_atual >= qtd_questoes:
                    if area_idx == st.session_state.area_desbloqueada_idx:
                        if is_simulado:
                            if area_idx < len(areas_ordenadas) - 1:
                                st.session_state.area_desbloqueada_idx += 1
                        else:
                            if tema_idx == st.session_state.topico_desbloqueado_idx[area_idx]:
                                st.session_state.topico_desbloqueado_idx[area_idx] += 1
                st.rerun()
                    
    else: # Acertou todas as questões
        st.balloons()
        if is_simulado:
            st.success("🎓 ABSURDO! Você destruiu no Simulado e destravou uma NOVA GRANDE ÁREA! Continue assim!")
        else:
            st.success("🎯 Trabalho excelente! Você superou a bateria inteira de questões e liberou o próximo tópico.")
            
        if st.button("🚀 Ver Menu Atualizado", type="primary"):
            resetar_estudo()
            st.rerun()
            
else:
    st.info("👈 Escoha seu assunto no menu ao lado e comece a etapa de fixação!")
        