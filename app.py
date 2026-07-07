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
    st.session_state.alertas = ["Gênesis: Epistasia e Leis de Supressão Ativadas."]
    
    st.session_state.O2 = 21000.0  
    st.session_state.CO2 = 1000.0  
    
    st.session_state.genes_descobertos = set(["F", "H", "C", "D", "A", "T"])
    st.session_state.genes_extintos = set()
    
    # REGRAS DE EPISTASIA INICIAIS (Quem inativa quem)
    st.session_state.inibicoes = {'H': 'F', 'C': 'F'}

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

    populacao = []
    for _ in range(25):
        populacao.append({
            'x': random.randint(0, tamanho-1), 'y': random.randint(0, tamanho-1),
            'energia': 100, 'dna': "FFhhccddAA" if random.random() < 0.7 else "FFhhccddTT",
            'dna_ativo': "", 'geracao': 1, 'raca': "Primitiva"
        })
    st.session_state.populacao = populacao

if st.session_state.CO2 < 0 or st.session_state.O2 > 100000:
    st.session_state.O2 = 21000.0
    st.session_state.CO2 = 1000.0

st.title("🧬 Projecto Gênesis: Biosfera Avançada")

st.sidebar.header("🕹️ Painel de Controlo")
executando = st.sidebar.checkbox("Ativar Simulação", value=True)
velocidade = st.sidebar.slider("Velocidade (seg/ciclo)", 0.1, 2.0, 0.4)

st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Novos Genes de Habitat")
st.sidebar.info("💧 `A` (Aquático) | ⛰️ `T` (Terrestre) | 🦅 `P` (Alado/Pássaro)")

# --- MOTOR DO JOGO ---
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
    if st.session_state.CO2 > 5000: ganho_solar += 2.0 
    
    novos_nascidos = []
    pop_atual = st.session_state.populacao
    mapa_atual = st.session_state.mapa

    for ser in pop_atual:
        if ser['energia'] <= 0: continue
        
        quad = mapa_atual[ser['y']][ser['x']]
        dna_base = ser['dna'].upper()
        
        # 1. PROCESSAR EPISTASIA (MASCARAR GENES)
        dna_ativo = dna_base
        for supressor, alvo in st.session_state.inibicoes.items():
            if supressor in dna_ativo:
                dna_ativo = dna_ativo.replace(alvo, "") # Remove o gene alvo da expressão
        
        ser['dna_ativo'] = dna_ativo # Guarda o DNA que realmente funciona para usar no render
        
        has_F, has_H, has_C = "F" in dna_ativo, "H" in dna_ativo, "C" in dna_ativo
        has_A, has_T, has_P = "A" in dna_ativo, "T" in dna_ativo, "P" in dna_ativo
        
        custo = 1.5 + (len(dna_base) * 0.05)
        if quad['temperatura'] == 'Frio': custo += 1.5
        if has_P: custo += 2.0 
        if quad['tipo'] == 'Terra' and not has_T and not has_P: custo += 4.0 
        if quad['tipo'] == 'Água' and not has_A and not has_P: custo += 4.0 
        if (has_H or has_C) and st.session_state.CO2 > 10000.0: custo += 1.5

        passos_base = 1

        if has_F:
            if st.session_state.CO2 >= 1.0:
                st.session_state.CO2 -= 1.0
                st.session_state.O2 += 1.0
                ser['energia'] += ganho_solar if quad['tipo'] == 'Água' else ganho_solar * 0.6
            else:
                ser['energia'] -= 2.0 
                if random.random() < 0.005: st.session_state.alertas.append(f"T{st.session_state.turno}: COLAPSO - Plantas sem CO2!")

        if has_H or has_C:
            if st.session_state.O2 >= 1.0:
                st.session_state.O2 -= 1.0
                st.session_state.CO2 += 1.0
            else:
                ser['energia'] -= 5.0 
                passos_base = 0 
                if random.random() < 0.005: st.session_state.alertas.append(f"T{st.session_state.turno}: COLAPSO - Animais sem O2!")

        ser['energia'] -= custo

        if "D" in dna_ativo and quad['nutrientes'] > 0:
            abs_nutri = min(quad['nutrientes'], 15)
            quad['nutrientes'] -= abs_nutri
            ser['energia'] += abs_nutri * 1.2

        passos = passos_base + (1 if has_P else 0)
        if random.random() < 0.75:
            for _ in range(passos):
                ser['x'] = max(0, min(tamanho-1, ser['x'] + random.choice([-1, 0, 1])))
                ser['y'] = max(0, min(tamanho-1, ser['y'] + random.choice([-1, 0, 1])))

        limite_mitose = 130 if (has_F and st.session_state.CO2 > 5000) else 160
        if ser['energia'] >= limite_mitose:
            ser['energia'] = 60
            letras = list(dna_base)
            
            # MUTAÇÕES E GERAÇÃO DE NOVOS GENES/REGRAS
            if random.random() < 0.35:
                if random.random() < 0.5: 
                    nova_letra = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                    letras.append(nova_letra)
                    
                    # 10% de chance de uma letra inédita criar uma nova lei de supressão no ecossistema
                    if nova_letra not in st.session_state.genes_descobertos and random.random() < 0.10:
                        alvo = random.choice(list(st.session_state.genes_descobertos))
                        if nova_letra != alvo:
                            st.session_state.inibicoes[nova_letra] = alvo
                            st.session_state.alertas.append(f"T{st.session_state.turno}: ⛔ EPISTASIA! A mutação [{nova_letra}] inativa o gene [{alvo}]!")

                else: 
                    letras.pop(random.randint(0, len(letras)-1))
            
            novos_nascidos.append({
                'x': ser['x'], 'y': ser['y'], 'energia': 60, 'dna': "".join(letras), 'dna_ativo': "",
                'geracao': ser['geracao'] + 1, 'raca': ser['raca']
            })

    pop_viva = [s for s in pop_atual if s['energia'] > 0] + novos_nascidos

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
                # Usa o DNA ATIVO para a caça (um ser com 'C' e 'F' caça e não faz fotossíntese)
                dna_a, dna_b = a.get('dna_ativo', a['dna']), b.get('dna_ativo', b['dna'])
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

    for s in pop_atual:
        if s['energia'] <= 0:
            mapa_atual[s['y']][s['x']]['nutrientes'] += 30

    pop_final = [s for s in pop_viva if s['energia'] > 0]
    
    genes_atuais = set()
    contagem_genes = {}
    for s in pop_final:
        for letra in set(s['dna'].upper()):
            genes_atuais.add(letra)
            contagem_genes[letra] = contagem_genes.get(letra, 0) + 1

    novos_genes = genes_atuais - st.session_state.genes_descobertos
    if novos_genes:
        st.session_state.genes_descobertos.update(novos_genes)
    st.session_state.genes_extintos = st.session_state.genes_descobertos - genes_atuais

    if len(pop_final) < 4:
        pop_final.append({'x': random.randint(0, tamanho-1), 'y': random.randint(0, tamanho-1), 'energia': 100, 'dna': "FFhhccddAA", 'dna_ativo': "FFhhccddAA", 'geracao': 1, 'raca': "Primitiva"})

    st.session_state.populacao = pop_final
    st.session_state.mapa = mapa_atual
    st.session_state.contagem_genes = contagem_genes

    censo = {'Planta': 0, 'Herbívoro': 0, 'Carnívoro': 0, 'Onívoro': 0, 'Neutro': 0}
    for s in pop_final:
        dna_exp = s.get('dna_ativo', s['dna'])
        has_F, has_H, has_C = "F" in dna_exp, "H" in dna_exp, "C" in dna_exp
        if has_H and has_C: censo['Onívoro'] += 1
        elif has_C: censo['Carnívoro'] += 1
        elif has_H: censo['Herbívoro'] += 1
        elif has_F: censo['Planta'] += 1
        else: censo['Neutro'] += 1

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
    
    pct_O2 = st.session_state.O2 / 1000.0
    pct_CO2 = st.session_state.CO2 / 1000.0

    st.markdown(f"**☁️ Composição da Atmosfera**")
    st.progress(min(1.0, max(0.0, pct_O2 / 35.0)), text=f"Oxigénio (O2): {pct_O2:.2f}%")
    st.progress(min(1.0, max(0.0, pct_CO2 / 15.0)), text=f"Dióxido de Carbono (CO2): {pct_CO2:.2f}%")

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
                # O Renderizador agora avalia apenas os genes não inativados
                dna_exp = ser_aqui.get('dna_ativo', ser_aqui['dna'])
                has_F, has_H, has_C = "F" in dna_exp, "H" in dna_exp, "C" in dna_exp
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
    
    st.subheader("🧬 Laboratório de Genética")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("**Genes Mais Dominantes (%):**")
        genes_formatados = []
        genes_ordenados = sorted(st.session_state.contagem_genes.items(), key=lambda x: x[1], reverse=True)
        for letra, contagem in genes_ordenados[:10]: 
            pct_gene = (contagem / total_pop) * 100 if total_pop > 0 else 0
            genes_formatados.append(f"`{letra}`: {pct_gene:.1f}%")
        st.markdown(" | ".join(genes_formatados))
        
    with col_g2:
        st.markdown("**⛔ Regras de Supressão (Epistasia):**")
        supressoes = [f"`{k}` silencia `{v}`" for k, v in st.session_state.inibicoes.items()]
        st.info(" | ".join(supressoes))

    for alerta in st.session_state.alertas[-3:]:
        st.caption(f"📜 {alerta}")

if executando:
    time.sleep(velocidade)
    st.rerun()
