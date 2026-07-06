import streamlit as st
import pandas as pd
import random
import time

# --- CONFIGURAÇÃO DA PÁGINA WEB ---
st.set_page_config(page_title="Gênesis - Simulador de Vida Artificial", layout="wide")

# --- INICIALIZAÇÃO DO ESTADO GLOBAL DO SERVIDOR ---
# O Streamlit reinicia o script a cada frame. Usamos o 'session_state' para 
# garantir que o mundo continua a rodar sem perder a memória do passado.
if 'turno' not in st.session_state:
    st.session_state.turno = 1
    st.session_state.dia = 1
    st.session_state.ano = 1
    st.session_state.estacao = "Primavera"
    st.session_state.historico_populacao = [] # Guarda dados para o gráfico de linhas
    st.session_state.alertas = ["Servidor Web Inicializado. Ecossistema Persistente Ativo."]
    
    # Gerar o mapa clássico de biomas (15x15)
    tamanho = 15
    mapa = []
    for y in range(tamanho):
        linha = []
        for x in range(tamanho):
            dist_centro = abs(x - tamanho/2) + abs(y - tamanho/2)
            tipo = 'Terra' if dist_centro < 6 else 'Água'
            temp = 'Frio' if y < 4 else ('Quente' if y > 10 else 'Temperado')
            linha.append({'tipo': tipo, 'temperatura': temp, 'nutrientes': 0})
        mapa.append(linha)
    st.session_state.mapa = mapa

    # Criar 25 seres iniciais na nuvem
    populacao = []
    for _ in range(25):
        populacao.append({
            'x': random.randint(0, tamanho-1),
            'y': random.randint(0, tamanho-1),
            'energia': 100,
            'dna': "FFhhccdd",
            'geracao': 1,
            'raca': "Primitiva"
        })
    st.session_state.populacao = populacao

# --- DESIGN DA INTERFACE WEB (FRONTEND) ---
st.title("🧬 Projecto Gênesis: Vida Artificial Permanente")
st.caption("Um ecossistema persistente regido por genética procedimental e seleção natural na nuvem.")

# Barra Lateral com Controlo e Legendas
st.sidebar.header("🕹️ Painel de Controlo Onisciente")
executando = st.sidebar.checkbox("Ativar Simulação Contínua", value=True)
velocidade = st.sidebar.slider("Velocidade do Tempo (segundos por ciclo)", 0.1, 2.0, 0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Legenda dos Biomas")
st.sidebar.info("💧 Água Temperada | 🧊 Água Fria | 🔥 Água Quente | ⛰️ Terra Seca")
st.sidebar.subheader("🦠 Entidades")
st.sidebar.markdown("🟢 `*` Planta | 🔵 `H` Herbívoro | 🟡 `O` Onívoro | 🔴 `C` Carnívoro | 🟤 `,` Nutriente")

# --- LÓGICA DO MOTOR EM SEGUNDO PLANO (BACKEND) ---
def rodar_turno_servidor():
    tamanho = 15
    st.session_state.turno += 1
    
    # Atualizar tempo histórico
    if st.session_state.turno % 10 == 0:
        st.session_state.dia += 1
    if st.session_state.dia > 30:
        st.session_state.dia = 1
        st.session_state.ano += 1
        estacoes = ["Primavera", "Verão", "Outono", "Inverno"]
        st.session_state.estacao = estacoes[st.session_state.ano % 4]
        st.session_state.alertas.append(f"Ano {st.session_state.ano}: Mudança climática global para o {st.session_state.estacao}!")

    ganho_solar = 6.0
    if st.session_state.estacao == "Inverno": ganho_solar = 3.0
    if st.session_state.estacao == "Verão": ganho_solar = 9.0

    novos_nascidos = []
    pop_atual = st.session_state.populacao
    mapa_atual = st.session_state.mapa

    # Processar Ciclo de Vida Individual
    for ser in pop_atual:
        quad = mapa_atual[ser['y']][ser['x']]
        
        # Custo Metabólico
        custo = 1.8 + (len(ser['dna']) * 0.05)
        if quad['temperatura'] == 'Frio': custo += 2.0
        if quad['tipo'] == 'Terra' and "H" not in ser['dna'] and "C" not in ser['dna']: custo += 3.0
        
        # Mutações procedimentais escondidas de resistência
        for char in ser['dna']:
            if char.isupper() and char not in ["F", "H", "C", "D"] and ord(char) % 3 == 0:
                custo *= 0.75 # Gene de resistência ativa
        
        ser['energia'] -= custo

        # Alimentação
        if "F" in ser['dna']: # Fotossíntese
            ser['energia'] += ganho_solar if quad['tipo'] == 'Água' else ganho_solar * 0.5
        if "D" in ser['dna'] and quad['nutrientes'] > 0: # Decompositor
            abs_nutri = min(quad['nutrientes'], 15)
            quad['nutrientes'] -= abs_nutri
            ser['energia'] += abs_nutri * 1.2

        # Movimento
        if random.random() < 0.75:
            ser['x'] = max(0, min(tamanho-1, ser['x'] + random.choice([-1, 0, 1])))
            ser['y'] = max(0, min(tamanho-1, ser['y'] + random.choice([-1, 0, 1])))

        # Morte
        if ser['energia'] <= 0:
            quad['nutrientes'] += 40
            continue

        # Reprodução / Mitose
        if ser['energia'] >= 150:
            ser['energia'] = 60
            letras = list(ser['dna'])
            if random.random() < 0.35: # Mutação Estrutural
                if random.random() < 0.5: letras.append(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"))
                else: letras.pop(random.randint(0, len(letras)-1))
            
            novo_dna = "".join(letras)
            novos_nascidos.append({
                'x': ser['x'], 'y': ser['y'], 'energia': 60, 'dna': novo_dna, 
                'geracao': ser['geracao'] + 1, 'raca': ser['raca']
            })

    # Filtrar sobreviventes e adicionar filhos
    pop_viva = [s for s in pop_atual if s['energia'] > 0] + novos_nascidos

    # Resolução da Cadeia Alimentar (Colisões)
    for a in pop_viva:
        for b in pop_viva:
            if a == b or a['energia'] <= 0 or b['energia'] <= 0: continue
            if a['x'] == b['x'] and a['y'] == b['y']:
                if "C" in a['dna'] and "F" not in b['dna']: # Carnívoro caça animal
                    b['energia'] = 0
                    mapa_atual[a['y']][a['x']]['nutrientes'] += 20
                    a['energia'] = min(200, a['energia'] + 60)
                elif "H" in a['dna'] and "F" in b['dna']: # Herbívoro caça planta
                    b['energia'] = 0
                    mapa_atual[a['y']][a['x']]['nutrientes'] += 15
                    a['energia'] = min(200, a['energia'] + 45)

    pop_final = [s for s in pop_viva if s['energia'] > 0]
    
    # Salvar dados de taxonomia de raças
    dnas_ativos = [s['dna'] for s in pop_final]
    for s in pop_final:
        if dnas_ativos.count(s['dna']) >= 3 and s['raca'] == "Primitiva" and len(s['dna']) > 8:
            s['raca'] = f"Clã-{s['dna'][-1].upper()}"
            st.session_state.alertas.append(f"Ano {st.session_state.ano}: Nova Raça [{s['raca']}] isolou-se biologicamente.")

    # Se houver extinção iminente, injetar esporos primordiais
    if len(pop_final) < 4:
        pop_final.append({'x': random.randint(0, tamanho-1), 'y': random.randint(0, tamanho-1), 'energia': 100, 'dna': "FFhhccdd", 'geracao': 1, 'raca': "Primitiva"})

    st.session_state.populacao = pop_final
    st.session_state.mapa = mapa_total = mapa_atual

    # Classificação de dados para o censo gráfico
    censo = {'Planta': 0, 'Herbívoro': 0, 'Carnívoro': 0, 'Onívoro': 0}
    for s in pop_final:
        has_F, has_H, has_C = "F" in s['dna'], "H" in s['dna'], "C" in s['dna']
        if has_H and has_C: censo['Onívoro'] += 1
        elif has_C: censo['Carnívoro'] += 1
        elif has_H: censo['Herbívoro'] += 1
        elif has_F: censo['Planta'] += 1

    # Adicionar ao histórico que alimenta o gráfico web
    st.session_state.historico_populacao.append({
        'Turno': st.session_state.turno, 'Plantas': censo['Planta'], 
        'Herbívoros': censo['Herbívoro'], 'Carnívoros': censo['Carnívoro'], 'Onívoros': censo['Onívoro']
    })

# --- RENDERIZAR PAINEL WEB ---
if executando:
    rodar_turno_servidor()

# Layout em colunas (Mapa à esquerda, Gráficos e Crónicas à direita)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"📅 Calendário Global: Ano {st.session_state.ano} | Dia {st.session_state.dia} ({st.session_state.estacao})")
    
    # Desenhar o mapa visualmente como uma tabela HTML estilizada
    tamanho = 15
    html_grid = "<table style='width:100%; border-collapse:collapse; text-align:center; font-family:monospace; font-size:18px;'>"
    
    for y in range(tamanho):
        html_grid += "<tr>"
        for x in range(tamanho):
            quad = st.session_state.mapa[y][x]
            ser_aqui = next((s for s in st.session_state.populacao if s['x'] == x and s['y'] == y), None)
            
            # Definir a cor de fundo do bioma
            if quad['tipo'] == 'Terra': bg_color = "#4a3b2c"  # Castanho para terra
            elif quad['temperatura'] == 'Frio': bg_color = "#1a3a5c"  # Azul escuro para frio
            elif quad['temperatura'] == 'Quente': bg_color = "#1e5e71"  # Ciano para quente
            else: bg_color = "#124463"  # Azul temperado
            
            # Definir o conteúdo (ser ou nutriente)
            if ser_aqui:
                has_F, has_H, has_C, _ = "F" in ser_aqui['dna'], "H" in ser_aqui['dna'], "C" in ser_aqui['dna']
                if has_H and has_C: char, color = 'O', '#ffcc00'
                elif has_C: char, color = 'C', '#ff3333'
                elif has_H: char, color = 'H', '#33ff33'
                elif has_F: char, color = '🟢', '#66ff66'
                else: char, color = '?', '#cc66ff'
                conteudo = f"<b style='color:{color};'>{char}</b>"
            elif quad['nutrientes'] > 20:
                conteudo = "<span style='color:#888888;'>,</span>"
            else:
                conteudo = "<span style='color:rgba(255,255,255,0.15);'>.</span>"
                
            html_grid += f"<td style='background-color:{bg_color}; padding:6px; border:1px solid #222;'>{conteudo}</td>"
        html_grid += "</tr>"
    html_grid += "</table>"
    st.markdown(html_grid, unsafe_allow_html=True)

with col2:
    st.subheader("📈 Censo Demográfico em Tempo Real")
    if len(st.session_state.historico_populacao) > 0:
        df_historico = pd.DataFrame(st.session_state.historico_populacao)
        # Exibe um gráfico de linhas interativo nativo da web!
        st.line_chart(df_historico.set_index('Turno')[['Plantas', 'Herbívoros', 'Carnívoros', 'Onívoros']])
    
    st.subheader("📜 Crónicas Históricas do Mundo")
    for alerta in st.session_state.alertas[-4:]:
        st.warning(alerta)

# Botão de atualização manual e estatísticas rápidas
st.markdown("---")
col_e1, col_e2, col_e3 = st.columns(3)
col_e1.metric("População Total Viva", len(st.session_state.populacao))
dnas_totais = [s['dna'] for s in st.session_state.populacao]
dna_top = max(set(dnas_totais), key=dnas_totais.count) if dnas_totais else "N/A"
col_e2.metric("DNA Dominante na Nuvem", f"[{dna_top[:6]}...]")
max_g = max([s['geracao'] for s in st.session_state.populacao]) if st.session_state.populacao else 1
col_e3.metric("Maior Linhagem Histórica", f"Gen {max_g}")

# JavaScript para forçar a página a atualizar automaticamente e rodar o servidor continuamente
if executando:
    time.sleep(velocidade)
    st.rerun()
