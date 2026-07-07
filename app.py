import streamlit as st
import pandas as pd
import random
import time

st.set_page_config(page_title="Gênesis - Vida Artificial", layout="wide")

# --- INICIALIZAÇÃO DO SERVIDOR ---
if 'turno' not in st.session_state:
    st.session_state.turno = 1
    st.session_state.dia = 1
    st.session_state.ano = 1
    st.session_state.estacao = "Primavera"
    st.session_state.historico_populacao = []
    st.session_state.alertas = ["Gênesis: Atmosfera e Genética Avançada ativadas."]
    
    # Atmosfera Global Inicial
    st.session_state.O2 = 10000.0
    st.session_state.CO2 = 5000.0
    
    # Memória Genética
    st.session_state.genes_descobertos = set(["F", "H", "C", "D", "A", "T"])
    st.session_state.genes_extintos = set()

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

    # Criar 25 seres: Maioria Aquática (A), alguns Terrestres (T)
    populacao = []
    for _ in range(25):
        populacao.append({
            'x': random.randint(0, tamanho-1), 'y': random.randint(0, tamanho-1),
            'energia': 100, 'dna': "FFhhccddAA" if random.random() < 0.7 else "FFhhccddTT",
            'geracao': 1, 'raca': "Primitiva"
        })
    st.session_state.populacao = populacao

st.title("🧬 Projecto Gênesis: Biosfera Avançada")

st.sidebar.header("🕹️ Painel de Controlo")
executando = st.sidebar.checkbox("Ativar Simulação", value=True)
velocidade = st.sidebar.slider("Velocidade (seg/ciclo)", 0.1, 2.0, 0.4)

st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Novos Genes de Habitat")
st.sidebar.info("💧 `A` (Aquático) | ⛰️ `T` (Terrestre) | 🦅 `P` (Alado/Pássaro)")

# --- MOTOR DO JOGO OTIMIZADO ---
def rodar_turno_servidor():
    tamanho = 15
    st.session_state.turno += 1
    
    if st.session_state.turno % 10 == 0: st.session_state.dia += 1
    if st.session_state.dia > 30:
        st.session_state.dia = 1
        st.session_state.ano += 1
        estacoes = ["Primavera", "Verão", "Outono", "Inverno"]
        st.session_state.estacao = estacoes[st.session_state.ano % 4]

    ganho_solar = 6.0
    if st.session_state.estacao == "Inverno": ganho_solar = 3.0
    if st.session_state.estacao == "Verão": ganho_solar = 9.0

    # Bónus de CO2 para Plantas
    if st.session_state.CO2 > 8000: ganho_solar += 3.0 
    
    novos_nascidos = []
    pop_atual = st.session_state.populacao
    mapa_atual = st.session_state.mapa

    # Processar Ciclo de Vida Individual
    for ser in pop_atual:
        if ser['energia'] <= 0: continue
        
        quad = mapa_atual[ser['y']][ser['x']]
        dna = ser['dna']
        
        # Leitura de Genes
        has_F, has_H, has_C = "F" in dna, "H" in dna, "C" in dna
        has_A = "A" in dna # Aquático
        has_T = "T" in dna # Terrestre
        has_P = "P" in dna # Alado/Voador
        
        # Custo Metabólico Base
        custo = 1.5 + (len(dna) * 0.05)
        if quad['temperatura'] == 'Frio': custo += 1.5
        if has_P: custo += 2.0 # Voar gasta muita energia
        
        # Penalidade de Habitat
        if quad['tipo'] == 'Terra' and not has_T and not has_P: custo += 4.0 # Asfixia na terra
        if quad['tipo'] == 'Água' and not has_A and not has_P: custo += 4.0 # Afogamento na água

        # Penalidade de O2 para animais
        if (has_H or has_C) and st.session_state.O2 < 2000:
            custo += 2.0 # Asfixia global
            passos_base = 0 # Ficam lentos
        else:
            passos_base = 1

        ser['energia'] -= custo

        # Trocas Gasosas e Alimentação
        if has_F:
            ser['energia'] += ganho_solar if quad['tipo'] == 'Água' else ganho_solar * 0.6
            st.session_state.O2 += 2.5
            st.session_state.CO2 -= 1.5
        if has_H or has_C:
            st.session_state.O2 -= 1.0
            st.session_state.CO2 += 1.5

        if "D" in dna and quad['nutrientes'] > 0:
            abs_nutri = min(quad['nutrientes'], 15)
            quad['nutrientes'] -= abs_nutri
            ser['energia'] += abs_nutri * 1.2

        # Movimento
        passos = passos_base + (1 if has_P else 0)
        if random.random() < 0.75:
            for _ in range(passos):
                ser['x'] = max(0, min(tamanho-1, ser['x'] + random.choice([-1, 0, 1])))
                ser['y'] = max(0, min(tamanho-1, ser['y'] + random.choice([-1, 0, 1])))

        # Reprodução
        limite_mitose = 140 if (has_F and st.session_state.CO2 > 8000) else 160
        if ser['energia'] >= limite_mitose:
            ser['energia'] = 60
            letras = list(dna)
            if random.random() < 0.35:
                if random.random() < 0.5: letras.append(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
                else: letras.pop(random.randint(0, len(letras)-1))
            
            novos_nascidos.append({
                'x': ser['x'], 'y': ser['y'], 'energia': 60, 'dna': "".join(letras), 
                'geracao': ser['geracao'] + 1, 'raca': ser['raca']
            })

    pop_viva = [s for s in pop_atual if s['energia'] > 0] + novos_nascidos

    # OTIMIZAÇÃO: Agrupar por posições para Cadeia Alimentar O(N)
    posicoes = {}
    for s in pop_viva:
        pos = (s['x'], s['y'])
        if pos not in posicoes: posicoes[pos] = []
        posicoes[pos].append(s)

    for pos, seres_aqui in posicoes.items():
        if len(seres_aqui) < 2: continue
        for a in seres_aqui:
            for b in seres_aqui:
                if a == b or a['energia'] <= 0 or b['energia'] <= 0: continue
                has_Fa, has_Ha, has_Ca = "F" in a['dna'], "H" in a['dna'], "C" in a['dna']
                has_Fb = "F" in b['dna']
                
                if has_Ca and not has_Fb: # Carnívoro caça animal
                    b['energia'] = 0
                    mapa_atual[pos[1]][pos[0]]['nutrientes'] += 15
                    a['energia'] = min(200, a['energia'] + 50)
                elif has_Ha and has_Fb: # Herbívoro caça planta
                    b['energia'] = 0
                    mapa_atual[pos[1]][pos[0]]['nutrientes'] += 10
                    a['energia'] = min(200, a['energia'] + 40)

    # Limpeza e Cadáveres
    for s in pop_atual:
        if s['energia'] <= 0:
            mapa_atual[s['y']][s['x']]['nutrientes'] += 30

    pop_final = [s for s in pop_viva if s['energia'] > 0]
    
    # Rastreio de Genes Exatos
    genes_atuais = set()
    contagem_genes = {}
    for s in pop_final:
        for letra in set(s['dna'].upper()):
            genes_atuais.add(letra)
            contagem_genes[letra] = contagem_genes.get(letra, 0) + 1

    # Atualizar Descobertas e Extinções
    novos_genes = genes_atuais - st.session_state.genes_descobertos
    if novos_genes:
        st.session_state.genes_descobertos.update(novos_genes)
        st.session_state.alertas.append(f"MUTACÃO: Novos genes descobertos na biosfera: {novos_genes}")
    
    genes_perdidos = st.session_state.genes_descobertos - genes_atuais
    st.session_state.genes_extintos = genes_perdidos

    if len(pop_final) < 4:
        pop_final.append({'x': random.randint(0, tamanho-1), 'y': random.randint(0, tamanho-1), 'energia': 100, 'dna': "FFhhccddAA", 'geracao': 1, 'raca': "Primitiva"})

    st.session_state.populacao = pop_final
    st.session_state.mapa = mapa_atual
    st.session_state.contagem_genes = contagem_genes

    censo = {'Planta': 0, 'Herbívoro': 0, 'Carnívoro': 0, 'Onívoro': 0}
    for s in pop_final:
        has_F, has_H, has_C = "F" in s['dna'], "H" in s['dna'], "C" in s['dna']
        if has_H and has_C: censo['Onívoro'] += 1
        elif has_C: censo['Carnívoro'] += 1
        elif has_H: censo['Herbívoro'] += 1
        elif has_F: censo['Planta'] += 1

    st.session_state.historico_populacao.append({
        'Turno': st.session_state.turno, 'Plantas': censo['Planta'], 
        'Herbívoros': censo['Herbívoro'], 'Carnívoros': censo['Carnívoro'], 'Onívoros': censo['Onívoro']
    })

if executando:
    rodar_turno_servidor()

# --- RENDERIZAR PAINEL ---
col_mapa, col_graficos = st.columns([1, 1.2])

with col_mapa:
    st.subheader(f"📅 Ano {st.session_state.ano} | Dia {st.session_state.dia} ({st.session_state.estacao})")
    
    # Progresso Atmosférico
    st.markdown(f"**☁️ Atmosfera Planetária**")
    st.progress(min(1.0, max(0.0, st.session_state.O2 / 20000.0)), text=f"Oxigénio (O2): {int(st.session_state.O2)}")
    st.progress(min(1.0, max(0.0, st.session_state.CO2 / 20000.0)), text=f"Dióxido de Carbono (CO2): {int(st.session_state.CO2)}")

    tamanho = 15
    html_grid = "<table style='width:100%; border-collapse:collapse; text-align:center; font-family:monospace; font-size:16px;'>"
    for y in range(tamanho):
        html_grid += "<tr>"
        for x in range(tamanho):
            quad = st.session_state.mapa[y][x]
            ser_aqui = next((s for s in st.session_state.populacao if s['x'] == x and s['y'] == y), None)
            
            if quad['tipo'] == 'Terra': bg_color = "#4a3b2c"
            elif quad['temperatura'] == 'Frio': bg_color = "#1a3a5c"
            elif quad['temperatura'] == 'Quente': bg_color = "#1e5e71"
            else: bg_color = "#124463"
            
            if ser_aqui:
                has_F, has_H, has_C = "F" in ser_aqui['dna'], "H" in ser_aqui['dna'], "C" in ser_aqui['dna']
                if has_H and has_C: char, color = 'O', '#ffcc00'
                elif has_C: char, color = 'C', '#ff3333'
                elif has_H: char, color = 'H', '#33ff33'
                elif has_F: char, color = '🟢', '#66ff66'
                else: char, color = '?', '#cc66ff'
                conteudo = f"<b style='color:{color};'>{char}</b>"
            elif quad['nutrientes'] > 20:
                conteudo = "<span style='color:#888888;'>,</span>"
            else:
                conteudo = "<span style='color:rgba(255,255,255,0.1);'>.</span>"
                
            html_grid += f"<td style='background-color:{bg_color}; padding:4px; border:1px solid #222;'>{conteudo}</td>"
        html_grid += "</tr>"
    html_grid += "</table>"
    st.markdown(html_grid, unsafe_allow_html=True)

with col_graficos:
    total_pop = len(st.session_state.populacao)
    st.subheader(f"📈 Dinâmica Populacional (Total: {total_pop})")
    
    if len(st.session_state.historico_populacao) > 0:
        df_historico = pd.DataFrame(st.session_state.historico_populacao)
        st.line_chart(df_historico.set_index('Turno')[['Plantas', 'Herbívoros', 'Carnívoros', 'Onívoros']], height=250)
    
    # Censo em Percentagem
    ultimo_censo = st.session_state.historico_populacao[-1]
    if total_pop > 0:
        pct_p = (ultimo_censo['Plantas'] / total_pop) * 100
        pct_h = (ultimo_censo['Herbívoros'] / total_pop) * 100
        pct_c = (ultimo_censo['Carnívoros'] / total_pop) * 100
        st.markdown(f"**Distribuição:** 🌱 Plantas: **{pct_p:.1f}%** | 🦕 Herbívoros: **{pct_h:.1f}%** | 🐅 Carnívoros: **{pct_c:.1f}%**")

    # Painel Genético Detalhado
    st.subheader("🧬 Laboratório de Genética")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("**Genes Circulantes (% da População):**")
        genes_formatados = []
        # Ordenar os genes do mais comum para o mais raro
        genes_ordenados = sorted(st.session_state.contagem_genes.items(), key=lambda x: x[1], reverse=True)
        for letra, contagem in genes_ordenados[:8]: # Mostra o Top 8
            pct_gene = (contagem / total_pop) * 100 if total_pop > 0 else 0
            genes_formatados.append(f"`{letra}`: {pct_gene:.1f}%")
        st.markdown(" | ".join(genes_formatados))
        
    with col_g2:
        st.markdown("**Registo de Extinções:**")
        if st.session_state.genes_extintos:
            st.error(f"💀 Extintos: {', '.join(st.session_state.genes_extintos)}")
        else:
            st.success("Nenhum gene foi perdido ainda.")

    for alerta in st.session_state.alertas[-2:]:
        st.caption(f"📜 {alerta}")

if executando:
    time.sleep(velocidade)
    st.rerun()
