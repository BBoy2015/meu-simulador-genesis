import streamlit as st
import pandas as pd
import random
import time
import numpy as np  # opcional, mas recomendado

st.set_page_config(page_title="Gênesis - Vida Artificial", layout="wide")

# ------------------ FUNÇÕES DA SIMULAÇÃO ------------------
def inicializar_estado():
    """Retorna o estado inicial completo."""
    estado = {
        'turno': 1,
        'dia': 1,
        'ano': 1,
        'estacao': "Primavera",
        'historico_populacao': [],
        'alertas': ["Gênesis: Respiração Celular Universal e Efeito Rubisco ativados."],
        'O2': 21000.0,
        'CO2': 1000.0,
        'genes_descobertos': set(["F", "H", "C", "D", "A", "T", "R"]),
        'genes_extintos': set(),
        'inibicoes': {'H': 'F', 'C': 'F'},
        'mapa': [],
        'populacao': [],
        'contagem_genes': {}
    }

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
    estado['mapa'] = mapa

    populacao = []
    for _ in range(25):
        populacao.append({
            'x': random.randint(0, tamanho-1), 'y': random.randint(0, tamanho-1),
            'energia': 100, 'dna': "FFffddddAARR" if random.random() < 0.5 else "FFffddddTTRR",
            'dna_ativo': "", 'geracao': 1, 'raca': "Primitiva"
        })
    estado['populacao'] = populacao
    return estado

def processar_turno(estado):
    """Executa um turno completo e retorna o estado atualizado e novos alertas."""
    tamanho = 15
    estado['turno'] += 1
    if estado['turno'] % 10 == 0:
        estado['dia'] += 1
    if estado['dia'] > 30:
        estado['dia'] = 1
        estado['ano'] += 1
        estacoes = ["Primavera", "Verão", "Outono", "Inverno"]
        estado['estacao'] = estacoes[estado['ano'] % 4]

    ganho_solar = 6.0
    if estado['estacao'] == "Inverno":
        ganho_solar = 3.0
    elif estado['estacao'] == "Verão":
        ganho_solar = 9.0
    if estado['CO2'] > 5000:
        ganho_solar += 2.0

    novos_nascidos = []
    pop_atual = estado['populacao']
    mapa_atual = estado['mapa']
    alertas = []

    # Extrair coordenadas para vetorização (se disponível)
    try:
        coords = np.array([[s['x'], s['y']] for s in pop_atual if s['energia'] > 0])
    except:
        coords = None

    for ser in pop_atual:
        if ser['energia'] <= 0:
            continue
        quad = mapa_atual[ser['y']][ser['x']]
        dna_base = ser['dna']
        # Atualiza DNA ativo (com supressão)
        dna_ativo = dna_base
        for supressor, alvo in estado['inibicoes'].items():
            if supressor in dna_ativo:
                dna_ativo = dna_ativo.replace(alvo, "")
        ser['dna_ativo'] = dna_ativo

        has_F, has_H, has_C = "F" in dna_ativo, "H" in dna_ativo, "C" in dna_ativo
        has_A, has_T, has_P = "A" in dna_ativo, "T" in dna_ativo, "P" in dna_ativo
        has_R = "R" in dna_ativo

        custo = 1.5 + (len(dna_base) * 0.05)
        if quad['temperatura'] == 'Frio':
            custo += 1.5
        if has_P:
            custo += 2.0
        if quad['tipo'] == 'Terra' and not has_T and not has_P:
            custo += 4.0
        if quad['tipo'] == 'Água' and not has_A and not has_P:
            custo += 4.0

        passos_base = 1

        # Respiração
        if has_R:
            taxa_respiracao = 1.5 if (has_H or has_C) else 0.5
            if estado['O2'] >= taxa_respiracao:
                estado['O2'] -= taxa_respiracao
                estado['CO2'] += taxa_respiracao
            else:
                ser['energia'] -= 4.0
                passos_base = 0
                if random.random() < 0.005:
                    alertas.append(f"T{estado['turno']}: O2 insuficiente! Asfixia Aeróbica.")
        else:
            if estado['O2'] > 5000.0:
                ser['energia'] -= 5.0
                if random.random() < 0.005:
                    alertas.append(f"T{estado['turno']}: Toxicidade de O2 a queimar seres anaeróbicos!")

        # Fotossíntese
        if has_F:
            if has_R and estado['O2'] > 21800.0:
                ser['energia'] -= 1.5
                if random.random() < 0.005:
                    alertas.append(f"T{estado['turno']}: O2 a 21.8%! Plantas entram em Fotorrespiração.")
            else:
                if estado['CO2'] >= 2.0:
                    estado['CO2'] -= 2.0
                    estado['O2'] += 2.0
                    ser['energia'] += ganho_solar if quad['tipo'] == 'Água' else ganho_solar * 0.6
                else:
                    ser['energia'] -= 2.0
                    if random.random() < 0.005:
                        alertas.append(f"T{estado['turno']}: Fome de Carbono (Plantas a sufocar)!")

        ser['energia'] -= custo

        # Decomposição (gene D)
        if "D" in dna_ativo and quad['nutrientes'] > 0:
            abs_nutri = min(quad['nutrientes'], 15)
            quad['nutrientes'] -= abs_nutri
            ser['energia'] += abs_nutri * 1.2
            if estado['O2'] >= 1.0:
                estado['O2'] -= 1.0
                estado['CO2'] += 1.0

        # Movimento
        passos = passos_base + (1 if has_P else 0)
        if random.random() < 0.75 and passos > 0:
            # Movimento individual (mantido para simplicidade)
            for _ in range(passos):
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                ser['x'] = max(0, min(tamanho-1, ser['x'] + dx))
                ser['y'] = max(0, min(tamanho-1, ser['y'] + dy))

        # Reprodução
        limite_mitose = 130 if (has_F and estado['CO2'] > 5000) else 160
        if ser['energia'] >= limite_mitose:
            ser['energia'] = 60
            letras = list(dna_base)
            if random.random() < 0.35:
                if random.random() < 0.5:
                    nova_letra = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
                    letras.append(nova_letra)
                    if nova_letra.isupper() and nova_letra not in estado['genes_descobertos'] and random.random() < 0.10:
                        alvo = random.choice([g for g in estado['genes_descobertos'] if g.isupper()])
                        if nova_letra != alvo:
                            estado['inibicoes'][nova_letra] = alvo
                            alertas.append(f"T{estado['turno']}: ⛔ EPISTASIA! Gene [{nova_letra}] inativa [{alvo}]!")
                else:
                    if len(letras) > 3:
                        letras.pop(random.randint(0, len(letras)-1))
            novos_nascidos.append({
                'x': ser['x'], 'y': ser['y'], 'energia': 60,
                'dna': "".join(letras), 'dna_ativo': "",
                'geracao': ser['geracao'] + 1, 'raca': ser['raca']
            })

    # Juntar população viva e novos
    pop_viva = [s for s in pop_atual if s['energia'] > 0] + novos_nascidos

    # Interações (predação)
    posicoes = {}
    for s in pop_viva:
        pos = (s['x'], s['y'])
        posicoes.setdefault(pos, []).append(s)

    for pos, seres_aqui in posicoes.items():
        if len(seres_aqui) < 2:
            continue
        for a in seres_aqui:
            for b in seres_aqui:
                if a is b or a['energia'] <= 0 or b['energia'] <= 0:
                    continue
                dna_a = a.get('dna_ativo', a['dna'])
                dna_b = b.get('dna_ativo', b['dna'])
                has_Fa, has_Ha, has_Ca = "F" in dna_a, "H" in dna_a, "C" in dna_a
                has_Fb = "F" in dna_b
                if has_Ca and not has_Fb:
                    b['energia'] = 0
                    mapa_atual[pos[1]][pos[0]]['nutrientes'] += 15
                    a['energia'] = min(200, a['energia'] + 50)
                elif has_Ha and has_Fb:
                    b['energia'] = 0
                    mapa_atual[pos[1]][pos[0]]['nutrientes'] += 10
                    a['energia'] = min(200, a['energia'] + 40)

    # Adicionar nutrientes de mortos
    for s in pop_atual:
        if s['energia'] <= 0:
            mapa_atual[s['y']][s['x']]['nutrientes'] += 30

    # Filtrar vivos
    pop_final = [s for s in pop_viva if s['energia'] > 0]

    # Atualizar genes descobertos e contagem
    genes_atuais = set()
    contagem_genes = {}
    for s in pop_final:
        dna_ativo = s.get('dna_ativo', s['dna'])
        for letra in set(c for c in dna_ativo if c.isupper()):
            genes_atuais.add(letra)
            contagem_genes[letra] = contagem_genes.get(letra, 0) + 1
    estado['genes_descobertos'].update(genes_atuais)
    estado['genes_extintos'] = estado['genes_descobertos'] - genes_atuais
    estado['contagem_genes'] = contagem_genes

    # Repovoamento emergencial
    if len(pop_final) < 4:
        for _ in range(4 - len(pop_final)):
            pop_final.append({
                'x': random.randint(0, tamanho-1), 'y': random.randint(0, tamanho-1),
                'energia': 100, 'dna': "FFffddddAARR" if random.random() < 0.5 else "FFffddddTTRR",
                'dna_ativo': "", 'geracao': 1, 'raca': "Esporo Primordial"
            })

    estado['populacao'] = pop_final
    estado['mapa'] = mapa_atual

    # Estatísticas para o histórico
    censo = {'Planta': 0, 'Herbívoro': 0, 'Carnívoro': 0, 'Onívoro': 0, 'Neutro': 0, 'Anaeróbico': 0}
    for s in pop_final:
        dna_exp = s.get('dna_ativo', s['dna'])
        has_F, has_H, has_C = "F" in dna_exp, "H" in dna_exp, "C" in dna_exp
        if "R" not in dna_exp:
            censo['Anaeróbico'] += 1
        if has_H and has_C:
            censo['Onívoro'] += 1
        elif has_C:
            censo['Carnívoro'] += 1
        elif has_H:
            censo['Herbívoro'] += 1
        elif has_F:
            censo['Planta'] += 1
        else:
            censo['Neutro'] += 1

    estado['historico_populacao'].append({
        'Turno': estado['turno'],
        'Plantas': censo['Planta'],
        'Herbívoros': censo['Herbívoro'],
        'Carnívoros': censo['Carnívoro'],
        'Onívoros': censo['Onívoro'],
        'Anaeróbicos': censo['Anaeróbico']
    })

    return estado, alertas

# ------------------ FUNÇÕES DE RENDERIZAÇÃO ------------------
def renderizar_mapa_html(estado):
    """Gera o HTML do mapa."""
    tamanho = 15
    mapa = estado['mapa']
    populacao = estado['populacao']
    # Criar dicionário de posições para acesso rápido
    pos_to_ser = {(s['x'], s['y']): s for s in populacao}

    html = "<table style='width:100%; border-collapse:collapse; text-align:center; font-family:monospace; font-size:16px;'>"
    for y in range(tamanho):
        html += "<tr>"
        for x in range(tamanho):
            quad = mapa[y][x]
            ser = pos_to_ser.get((x, y))
            # Cor de fundo
            if quad['tipo'] == 'Terra':
                bg = "#4a3b2c"
            else:
                if quad['temperatura'] == 'Frio':
                    bg = "#1a3a5c"
                elif quad['temperatura'] == 'Quente':
                    bg = "#1e5e71"
                else:
                    bg = "#124463"

            # Conteúdo
            if ser:
                dna_exp = ser.get('dna_ativo', ser['dna'])
                has_F, has_H, has_C = "F" in dna_exp, "H" in dna_exp, "C" in dna_exp
                if has_H and has_C:
                    char, color = 'O', '#ffcc00'
                elif has_C:
                    char, color = 'C', '#ff3333'
                elif has_H:
                    char, color = 'H', '#33ff33'
                elif has_F:
                    char, color = '🟢', '#66ff66'
                else:
                    char, color = '?', '#cc66ff'
                conteudo = f"<b style='color:{color};'>{char}</b>"
            elif quad['nutrientes'] > 20:
                conteudo = "<span style='color:#888888;'>,</span>"
            else:
                conteudo = "<span style='color:rgba(255,255,255,0.1);'>.</span>"

            html += f"<td style='background-color:{bg}; padding:4px; border:1px solid #222;'>{conteudo}</td>"
        html += "</tr>"
    html += "</table>"
    return html

def renderizar_metricas(estado):
    """Exibe métricas principais."""
    col1, col2, col3 = st.columns(3)
    pct_O2 = estado['O2'] / 1000.0
    pct_CO2 = estado['CO2'] / 1000.0
    col1.metric("🌬️ Oxigénio (O2)", f"{pct_O2:.2f}%")
    col2.metric("🌿 CO2", f"{pct_CO2:.2f}%")
    col3.metric("👥 População Total", len(estado['populacao']))

def renderizar_grafico(estado):
    """Exibe o gráfico de população."""
    if len(estado['historico_populacao']) > 0:
        df = pd.DataFrame(estado['historico_populacao'])
        st.line_chart(df.set_index('Turno')[['Plantas', 'Herbívoros', 'Carnívoros', 'Anaeróbicos']], height=250)

def renderizar_geneticas(estado):
    """Exibe genes e supressões."""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Genes Mais Dominantes (%):**")
        total = len(estado['populacao'])
        genes = sorted(estado['contagem_genes'].items(), key=lambda x: x[1], reverse=True)[:10]
        if total > 0:
            genes_formatados = [f"`{g}`: {(c/total)*100:.1f}%" for g, c in genes]
        else:
            genes_formatados = ["Nenhum"]
        st.markdown(" | ".join(genes_formatados))
    with col2:
        st.markdown("**⛔ Regras de Supressão (Epistasia):**")
        if estado['inibicoes']:
            supressoes = [f"`{k}` → `{v}`" for k, v in estado['inibicoes'].items()]
            st.info(" | ".join(supressoes))
        else:
            st.info("Nenhuma")

# ------------------ INICIALIZAÇÃO ------------------
if 'estado' not in st.session_state:
    st.session_state.estado = inicializar_estado()
    st.session_state.pausado = False  # controle de pausa

estado = st.session_state.estado

# ------------------ INTERFACE PRINCIPAL ------------------
st.title("🧬 Projecto Gênesis: Biosfera Avançada")

# Sidebar
st.sidebar.header("🕹️ Painel de Controlo")
if st.sidebar.button("▶️ Iniciar" if st.session_state.pausado else "⏸️ Pausar"):
    st.session_state.pausado = not st.session_state.pausado

velocidade = st.sidebar.slider("Velocidade (seg/ciclo)", 0.1, 2.0, 0.4, step=0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Genes Especiais")
st.sidebar.info("💧 `A` (Água) | ⛰️ `T` (Terra) | 🦅 `P` (Voo) | 🫁 `R` (Resp. Aeróbica)")

# Placeholders para atualização seletiva
placeholder_mapa = st.empty()
placeholder_metricas = st.empty()
placeholder_grafico = st.empty()
placeholder_geneticas = st.empty()
placeholder_alertas = st.empty()

# ------------------ LOOP PRINCIPAL (com pausa) ------------------
if not st.session_state.pausado:
    estado, novos_alertas = processar_turno(estado)
    # Atualizar alertas (manter últimos 20)
    estado['alertas'] = (estado['alertas'] + novos_alertas)[-20:]
    st.session_state.estado = estado

# Renderização (sempre atualiza, mesmo em pausa)
with placeholder_mapa.container():
    st.subheader(f"📅 Ano {estado['ano']} | Dia {estado['dia']} ({estado['estacao']})")
    st.markdown(renderizar_mapa_html(estado), unsafe_allow_html=True)

with placeholder_metricas.container():
    renderizar_metricas(estado)

with placeholder_grafico.container():
    st.subheader("📈 Dinâmica Populacional")
    renderizar_grafico(estado)

with placeholder_geneticas.container():
    st.subheader("🧬 Laboratório de Genética")
    renderizar_geneticas(estado)

with placeholder_alertas.container():
    if estado['alertas']:
        st.subheader("📜 Últimos Alertas")
        for alerta in estado['alertas'][-5:]:
            st.caption(f"• {alerta}")

# Aguardar e repetir
if not st.session_state.pausado:
    time.sleep(velocidade)
    st.rerun()
