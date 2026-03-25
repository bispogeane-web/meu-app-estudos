import streamlit as st
import google.generativeai as genai
import json
from supabase import create_client, Client

st.set_page_config(page_title="Português Total", page_icon="📚", layout="wide")

# Configuração
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
modelo = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})

# Conexão Supabase
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

if 'user' not in st.session_state:
    st.session_state.user = None

# Estrutura do Syllabus
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

def carregar_progresso():
    if not st.session_state.user: return
    try:
        resp = supabase.table('user_progress').select("*").eq('id', st.session_state.user.id).execute()
        if resp.data:
            dados = resp.data[0]
            st.session_state.area_desbloqueada_idx = dados["area_desbloqueada_idx"]
            st.session_state.topico_desbloqueado_idx = {int(k): v for k, v in dados["topico_desbloqueado_idx"].items()}
        else:
            st.session_state.area_desbloqueada_idx = 0
            st.session_state.topico_desbloqueado_idx = {i: 0 for i in range(len(areas_ordenadas))}
            supabase.table('user_progress').insert({
                "id": st.session_state.user.id,
                "area_desbloqueada_idx": 0,
                "topico_desbloqueado_idx": st.session_state.topico_desbloqueado_idx
            }).execute()
    except Exception as e:
        st.session_state.area_desbloqueada_idx = 0
        st.session_state.topico_desbloqueado_idx = {i: 0 for i in range(len(areas_ordenadas))}

def salvar_progresso():
    if st.session_state.user:
        try:
            supabase.table('user_progress').update({
                "area_desbloqueada_idx": st.session_state.area_desbloqueada_idx,
                "topico_desbloqueado_idx": st.session_state.topico_desbloqueado_idx
            }).eq('id', st.session_state.user.id).execute()
        except: pass

def log_out():
    st.session_state.clear()
    
# --- TELA DE LOGIN ---
if not st.session_state.user:
    st.title("🔐 Acesso - Português Total")
    st.write("Faça login para salvar e continuar o seu progresso.")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba1, aba2 = st.tabs(["Entrar", "Criar Nova Conta"])
        with aba1:
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar", type="primary"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                    st.session_state.user = res.user
                    carregar_progresso()
                    st.rerun()
                except Exception as e:
                    st.error("Email ou senha incorretos ou não cadastrados.")
        with aba2:
            email_novo = st.text_input("E-mail ")
            senha_nova = st.text_input("Senha ", type="password", help="Use pelo menos 6 caracteres")
            if st.button("Finalizar Cadastro", type="primary"):
                try:
                    res = supabase.auth.sign_up({"email": email_novo, "password": senha_nova})
                    st.success("Conta criada com sucesso! Faça login na aba 'Entrar'.")
                except Exception as e:
                    st.error(f"Ocorreu um erro. A senha deve ter no mínimo 6 letras/números.")
    st.stop()


# --- APP PRINCIPAL ---
if 'sessao_iniciada' not in st.session_state:
    st.session_state.aula_dados = None
    st.session_state.indice_questao_atual = 0
    st.session_state.errou_atual = False
    st.session_state.acertou_atual = False
    st.session_state.tentativas_atuais = 0
    st.session_state.ultima_resposta_errada = None
    st.session_state.sessao_iniciada = True
    carregar_progresso()

def resetar_estudo():
    st.session_state.aula_dados = None
    st.session_state.indice_questao_atual = 0
    st.session_state.errou_atual = False
    st.session_state.acertou_atual = False
    st.session_state.tentativas_atuais = 0
    st.session_state.ultima_resposta_errada = None

st.sidebar.title("🛤️ Trilha de Aprendizagem")
st.sidebar.caption(f"Usuário: {st.session_state.user.email}")
st.sidebar.button("Sair (Logout)", on_click=log_out)
st.sidebar.divider()

is_battery_active = st.session_state.get('aula_dados') is not None

area_escolhida = st.sidebar.selectbox("Escolha a Grande Área:", areas_ordenadas, disabled=is_battery_active)
area_idx = areas_ordenadas.index(area_escolhida)

topicos_da_area = opcoes_topicos[area_escolhida]
tema_escolhido = st.sidebar.selectbox("Escolha o Tópico específico:", topicos_da_area, disabled=is_battery_active)
tema_idx = topicos_da_area.index(tema_escolhido)

qtd_questoes_desejada = st.sidebar.number_input("Quantidade de questões:", min_value=1, max_value=15, value=5, step=1, disabled=is_battery_active)

is_simulado = "🏆 SIMULADO FINAL" in tema_escolhido

is_revisao = False
if not is_simulado:
    if area_idx < int(st.session_state.area_desbloqueada_idx):
        is_revisao = True
    elif area_idx == int(st.session_state.area_desbloqueada_idx) and tema_idx < int(st.session_state.topico_desbloqueado_idx.get(area_idx, 0)):
        is_revisao = True

st.title("📚 Português Total")
st.caption("Resolva a bateria inteira de exercícios para comprovar aprendizado e liberar o próximo bloco.")

btn_gerar = st.sidebar.button("Gerar Bateria" if not is_simulado else "INICIAR SIMULADO", on_click=resetar_estudo, type="primary", disabled=is_battery_active)

if btn_gerar or st.session_state.get("gerar_nova_bateria_agora", False):
    st.session_state.gerar_nova_bateria_agora = False
    with st.spinner("Preparando as questões das piores bancas para você..."):
        if is_simulado:
            prompt = f"""
            Aja como um professor especialista em concursos e crie um SIMULADO RIGOROSO sobre a área: "{area_escolhida}".
            Regras:
            1. NÃO gere aula teórica. Apenas uma fala inicial desafiadora.
            2. Gere EXATAMENTE {qtd_questoes_desejada} questões inéditas (nível FGV/FCC) misturando os tópicos dessa área.
            3. Responda em JSON EXATO com as chaves: "aula" (mensagem inicial), "questoes" (array numérico com objetos contendo: "enunciado_questao", "opcoes" (objeto de A a E), "resposta_correta" (só a letra) e "explicacoes" (objeto de A a E justificando o motivo de estar certo ou errado de forma isolada para cada letra)).
            """
        elif is_revisao:
            prompt = f"""
            Aja como um professor especialista. O aluno já estudou e ESTÁ REVISANDO o tema: "{tema_escolhido}" ({area_escolhida}).
            Regras IMPORTANTES para a REVISÃO MODO AVANÇADO:
            1. NÃO repita a teoria básica. Vá direto para exceções, pegadinhas de prova (FGV/FCC) e erros comuns de alunos bons.
            2. Use ABORDAGENS DIFERENTES e EXEMPLOS 100% INÉDITOS que não costumam aparecer na primeira aula de introdução.
            3. Gere UMA BATERIA DE EXATAMENTE {qtd_questoes_desejada} QUESTÕES inéditas e elaboradas (de alto nível de dificuldade).
            4. Responda em JSON EXATO com as chaves: "aula" (teoria focada nas pegadinhas + macete novo em markdown), "questoes" (array numérico com objetos contendo: "enunciado_questao", "opcoes" (com A a E), "resposta_correta" (letra) e "explicacoes" (um objeto de chaves A, B, C, D, E explicando detalhadamente APENAS cada alternativa sem revelar direto o gabarito nas alternativas erradas)).
            """
        else:
            prompt = f"""
            Aja como um professor especialista em concursos e explique o tema: "{tema_escolhido}" ({area_escolhida}).
            Regras:
            1. Aula ágil, direta ao ponto e de alto nível.
            2. Forneça o MACETE INFALÍVEL.
            3. IMPORTANTE: Gere UMA BATERIA DE EXATAMENTE {qtd_questoes_desejada} QUESTÕES inéditas (múltipla escolha) sobre o tema.
            4. Responda em JSON EXATO com as chaves: "aula" (teoria + macete em markdown), "questoes" (array com objetos contendo: "enunciado_questao", "opcoes" (com A a E), "resposta_correta" (letra) e "explicacoes" (um objeto de chaves A, B, C, D, E explicando detalhadamente APENAS cada alternativa sem revelar direto o gabarito nas alternativas erradas)).
            """
        try:
            resposta = modelo.generate_content(prompt)
            st.session_state.aula_dados = json.loads(resposta.text, strict=False)
        except Exception as e:
            st.error(f"Erro ao gerar material. Tente novamente! ({e})")

# Lógica Iterativa de Bateria de Questões
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
                        st.session_state.ultima_resposta_errada = None
                    else:
                        st.session_state.errou_atual = True
                        st.session_state.tentativas_atuais = st.session_state.get('tentativas_atuais', 0) + 1
                        st.session_state.ultima_resposta_errada = resposta_usuario[0]
                    st.rerun()
                else:
                    st.warning("Marque uma alternativa!")
            
            if st.session_state.errou_atual:
                letra_errada = st.session_state.ultima_resposta_errada
                explicacao = q_atual.get("explicacoes", {}).get(letra_errada, q_atual.get("comentario_gabarito", "A alternativa incorreta! Revise a teoria."))
                tentativas = st.session_state.get('tentativas_atuais', 0)
                
                if tentativas < 3:
                    st.error(f'❌ Incorreto (Tentativa {tentativas}/3).')
                    st.warning(f"**Por que a letra {letra_errada} está errada?**\n{explicacao}")
                    st.info("Você precisa acertar a questão para avançar. Tente de novo sem perder o foco!")
                else:
                    st.error('❌ Você esgotou as 3 tentativas para essa questão!')
                    st.warning(f"**Por que a letra {letra_errada} está errada?**\n{explicacao}")
                    st.info("A resposta correta era a letra **" + q_atual["resposta_correta"] + "**.")
                    if st.button("Gerar Nova Questão Substituta e Tentar Novamente", type="primary"):
                        with st.spinner("Buscando nova questão de mesma complexidade..."):
                            prompt_nova_questao = f"""
                            Aja como um professor exigente. Gere APENAS UMA NOVA QUESTÃO inédita e desafiadora sobre o tópico "{tema_escolhido}".
                            Responda EXATAMENTE neste formato JSON:
                            {{
                                "enunciado_questao": "...",
                                "opcoes": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
                                "resposta_correta": "...",
                                "explicacoes": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}}
                            }}
                            """
                            try:
                                resposta_nova = modelo.generate_content(prompt_nova_questao)
                                nova_q = json.loads(resposta_nova.text, strict=False)
                                st.session_state.aula_dados["questoes"][idx] = nova_q
                                st.session_state.errou_atual = False
                                st.session_state.tentativas_atuais = 0
                                st.session_state.ultima_resposta_errada = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao gerar questão. Clique novamente. ({e})")
                
        else:
            letra_certa = q_atual['resposta_correta']
            explicacao_certa = q_atual.get("explicacoes", {}).get(letra_certa, q_atual.get("comentario_gabarito", "Excelente resolução!"))
            
            st.success(f"🎉 Exato! A letra correta é a **{letra_certa}**.")
            st.info(f"💡 **Fixação da Regra:**\n{explicacao_certa}")
            
            if st.button("Avançar para Próxima Questão" if idx < qtd_questoes - 1 else "✅ FINALIZAR BATERIA", type="primary"):
                st.session_state.indice_questao_atual += 1
                st.session_state.acertou_atual = False
                st.session_state.errou_atual = False
                st.session_state.tentativas_atuais = 0
                st.session_state.ultima_resposta_errada = None
                
                # Fim da bateria - Lógica de Desbloqueios e Salvar Progresso
                if st.session_state.indice_questao_atual >= qtd_questoes:
                    if area_idx == st.session_state.area_desbloqueada_idx:
                        if is_simulado:
                            if area_idx < len(areas_ordenadas) - 1:
                                st.session_state.area_desbloqueada_idx += 1
                        else:
                            if tema_idx == st.session_state.topico_desbloqueado_idx.get(area_idx, 0):
                                st.session_state.topico_desbloqueado_idx[area_idx] += 1
                                
                    # Atualiza progresso se o usuário tiver avançado manualmente para áreas novas.
                    if area_idx > st.session_state.area_desbloqueada_idx:
                        st.session_state.area_desbloqueada_idx = area_idx
                        if not is_simulado:
                            st.session_state.topico_desbloqueado_idx[area_idx] = tema_idx + 1
                    elif area_idx == st.session_state.area_desbloqueada_idx and not is_simulado and tema_idx > st.session_state.topico_desbloqueado_idx.get(area_idx, 0):
                        st.session_state.topico_desbloqueado_idx[area_idx] = tema_idx + 1

                    salvar_progresso()
                st.rerun()
                    
    else: # Acertou todas as questões
        st.balloons()
        if is_simulado:
            st.success("🎓 ABSURDO! Você destruiu no Simulado e destravou uma NOVA GRANDE ÁREA! Continue assim!")
        else:
            st.success("🎯 Trabalho excelente! Você superou a bateria inteira de questões e liberou o próximo tópico.")
            
        st.write("### O que deseja fazer agora?")
        st.info("Para rever outros assuntos concluídos, clique no botão **Voltar ao Menu Principal** abaixo e selecione qualquer tópico pela barra lateral (esquerda). O aplicativo Ativará automaticamente o **Modo de Revisão Avançada**, criando novas explicações e pegadinhas para você nunca repetir a mesma aula!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Aprofundar e Revisar este tópico novamente", use_container_width=True):
                resetar_estudo()
                st.session_state.gerar_nova_bateria_agora = True
                st.rerun()
        with col2:
            if st.button("📋 Voltar ao Menu Principal", type="primary", use_container_width=True):
                resetar_estudo()
                st.rerun()
            
else:
    st.info("👈 Escoha seu assunto no menu ao lado e comece a etapa de fixação!")