import os
import json
import streamlit as st
import csv
from datetime import datetime
import random

# ============================
# Funções utilitárias
# ============================
def rerun():
    """Reinicia a sessão do Streamlit (limpa tudo)"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ============================
# Configurações iniciais
# ============================
json_folder = "TEXTS_QUESTIONS"
resposta_arquivo = "resultados_usuarios.csv"

# ============================
# CSS para barra, gradiente e cards
# ============================
st.markdown(
    """
    <style>
    .header-bar {
        background-color: white;
        padding: 10px 20px;
        display: flex;
        align-items: center;
        border-bottom: 2px solid #e0e0e0;
    }
    .header-bar img {
        height: 50px;
        margin-right: 15px;
    }
    .header-bar h1 {
        color: #2F97A1;
        font-size: 1.8rem;
        margin: 0;
        font-weight: bold;
    }
    .intro-box {
        background: linear-gradient(to right, #226DAA, #2F97A1);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-top: 10px;
        font-size: 1rem;
    }
    .card-button-gradient {
        background: linear-gradient(to right, #226DAA, #2F97A1);
        color: white;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        text-align: center;
        font-weight: bold;
        border: 2px solid #2F97A1;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    .card-button-gradient:hover {
        transform: scale(1.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================
# Header
# ============================
st.markdown(
    """
    <div class="header-bar">
        <img src="https://raw.githubusercontent.com/PelizariGabriel/Scolex-Test/5cab7cc6b04920291b868be42e4ba29e14cc2b30/scolados_logo.png" alt="Logo">
        <h1>Scolex - Teste Adaptativo de Leitura</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================
# Caixa de apresentação com gradiente
# ============================
st.markdown(
    """
    <div class="intro-box">
        Bem-vindo! Este é um teste adaptativo que avalia seu nível de compreensão de leitura.<br>
        Ele começa no nível certo para sua série e muda de acordo com suas respostas.<br>
        Este teste pode levar entre 5 e 15 minutos.
    </div>
    """,
    unsafe_allow_html=True
)

# ============================
# Carregamento dos textos
# ============================
@st.cache_data
def carregar_textos():
    textos = []
    for file in os.listdir(json_folder):
        if file.endswith(".json"):
            with open(os.path.join(json_folder, file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                textos.append({
                    "filename": file,
                    "titulo": data["titulo"],
                    "texto": data["texto"],
                    "perguntas": data["perguntas"],
                    "scolex_level": data.get("scolex_level", 50)
                })
    return sorted(textos, key=lambda x: x["scolex_level"])

def escolher_texto(textos, scolex_alvo, usados):
    candidatos = [t for t in textos if t["filename"] not in usados]
    if not candidatos:
        return None
    return min(candidatos, key=lambda x: abs(x["scolex_level"] - scolex_alvo))

def salvar_resultado(nome, serie, resultado, opiniao):
    existe = os.path.exists(resposta_arquivo)
    with open(resposta_arquivo, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["data_hora", "nome", "serie_escolar", "resultado_scolex", "opiniao"])
        writer.writerow([datetime.now().isoformat(), nome, serie, resultado, opiniao])

# ============================
# Função principal
# ============================
def main():
    # ======== Coleta nome e série escolar ========
    if "nome" not in st.session_state:
        st.markdown('<div class="teste-box">', unsafe_allow_html=True)
        nome = st.text_input("Qual seu nome completo?")

        serie_options = [
            "1° ano", "2° ano", "3° ano", "4° ano", "5° ano", "6° ano",
            "7° ano", "8° ano", "9° ano", "1ª Série", "2ª Série", "3ª Série", "Graduado"
        ]
        serie = st.selectbox("Qual sua série escolar?", options=serie_options)

        if st.button("Começar teste"):
            if nome.strip() == "":
                st.warning("⚠️ Por favor, insira seu nome.")
                return

            st.session_state.nome = nome
            st.session_state.serie_escolar = serie

            if serie == "Graduado":
                st.session_state.scolex_atual = 70
            else:
                serie_map = {
                    "1° ano": 1, "2° ano": 2, "3° ano": 3,
                    "4° ano": 4, "5° ano": 5, "6° ano": 6,
                    "7° ano": 7, "8° ano": 8, "9° ano": 9,
                    "1ª Série": 10, "2ª Série": 11, "3ª Série": 12
                }
                serie_int = serie_map[serie]
                if 0 <= serie_int <= 3:
                    st.session_state.scolex_atual = 30
                elif 4 <= serie_int <= 6:
                    st.session_state.scolex_atual = 40
                elif 7 <= serie_int <= 9:
                    st.session_state.scolex_atual = 50
                elif 10 <= serie_int <= 12:
                    st.session_state.scolex_atual = 60
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ======== Inicialização do estado ========
    if "textos" not in st.session_state:
        st.session_state.textos = carregar_textos()
        st.session_state.usados = set()
        st.session_state.finalizado = False
        st.session_state.subindo = True
        st.session_state.resultado_final = None
        st.session_state.ultimo_scolex_bom = None
        st.session_state.primeira_rodada = True
        st.session_state.respostas_enviadas = False

    st.markdown('<div class="teste-box">', unsafe_allow_html=True)

    # ======== Resultado final e coleta de opinião ========
    if st.session_state.finalizado:
        st.success(f"✅ Seu nível Scolex é: {st.session_state.resultado_final:.2f}")
        if "opiniao" not in st.session_state:
            opiniao = st.text_area("✍️ Dê sua opinião sobre o teste")
            if st.button("Salvar resultado"):
                import io
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["data_hora", "nome", "serie_escolar", "resultado_scolex", "opiniao"])
                writer.writerow([datetime.now().isoformat(), st.session_state.nome,
                                 st.session_state.serie_escolar, st.session_state.resultado_final, opiniao])
                st.session_state.opiniao = opiniao
                st.success("📁 Resultado gerado.")
                st.download_button(
                    label="⬇️ Baixar meu resultado (.csv)",
                    data=output.getvalue(),
                    file_name=f"resultado_{st.session_state.nome.replace(' ', '_')}.csv",
                    mime="text/csv"
                )
            st.markdown('</div>', unsafe_allow_html=True)
            return
        if st.button("🔁 Reiniciar teste"):
            rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            return

    # ======== Seleciona texto atual ========
    if "texto_atual" not in st.session_state:
        texto = escolher_texto(st.session_state.textos, st.session_state.scolex_atual, st.session_state.usados)
        if texto is None:
            st.warning("🚫 Nenhum texto restante para o nível atual.")
            st.session_state.resultado_final = st.session_state.ultimo_scolex_bom or st.session_state.scolex_atual
            st.session_state.finalizado = True
            st.markdown('</div>', unsafe_allow_html=True)
            return
        st.session_state.texto_atual = texto
        st.session_state.usados.add(texto["filename"])

    texto = st.session_state.texto_atual

    # ======== Exibe texto e perguntas ========
    st.subheader(f"📈 Nível Scolex: {texto['scolex_level']:.2f}")
    st.markdown(f"### {texto['titulo']}")
    st.markdown(texto["texto"])
    st.markdown("### Perguntas")

    # Embaralhamento das perguntas
    if "shuffled_questions" not in st.session_state:
        shuffled_questions = []
        for pergunta in texto["perguntas"]:
            orig_options = pergunta["alternativas"]
            pair_list = list(enumerate(orig_options))
            random.shuffle(pair_list)
            options = []
            correct_option_value = None
            for orig_idx, label in pair_list:
                val = f"{orig_idx}||{label}"
                options.append(val)
                if orig_idx == pergunta["resposta_correta"]:
                    correct_option_value = val
            shuffled_questions.append({
                "pergunta": pergunta["pergunta"],
                "options": options,
                "correct_value": correct_option_value
            })
        st.session_state.shuffled_questions = shuffled_questions

    # ============================
    # Exibe perguntas como cards com gradiente
    # ============================
    for i, pergunta in enumerate(st.session_state.shuffled_questions):
        st.markdown(f"**{i+1}. {pergunta['pergunta']}**")
        cols = st.columns(len(pergunta["options"]))
        for j, opt in enumerate(pergunta["options"]):
            label = opt.split("||", 1)[1]
            # Botão com gradiente
            if cols[j].button(label, key=f"card_{i}_{j}"):
                st.session_state[f"q{i}"] = opt
                st.rerun()
        selected_card = st.session_state.get(f"q{i}", None)
        if selected_card:
            st.markdown(f"✅ Selecionado: **{selected_card.split('||')[1]}**")
        st.markdown("---")

    # ============================
    # Botão enviar respostas
    # ============================
    if st.button("Enviar respostas"):
        acertos = 0
        total = len(st.session_state.shuffled_questions)
        for i, pergunta in enumerate(st.session_state.shuffled_questions):
            chosen = st.session_state.get(f"q{i}", None)
            if chosen is not None and chosen == pergunta["correct_value"]:
                acertos += 1
        percentual = (acertos / total) * 100 if total > 0 else 0.0
        st.markdown(f"<h3>🎯 Você acertou {acertos} de {total} ({percentual:.1f}%)</h3>", unsafe_allow_html=True)

        # Atualiza Scolex
        min_scolex = min([t["scolex_level"] for t in st.session_state.textos])
        if percentual >= 80:
            if st.session_state.ultimo_scolex_bom is None or texto["scolex_level"] > st.session_state.ultimo_scolex_bom:
                st.session_state.ultimo_scolex_bom = texto["scolex_level"]
            max_nivel = max([t["scolex_level"] for t in st.session_state.textos])
            if texto["scolex_level"] >= max_nivel:
                st.session_state.resultado_final = texto["scolex_level"]
                st.session_state.finalizado = True
            elif st.session_state.subindo:
                st.session_state.scolex_atual += 5
            else:
                st.session_state.resultado_final = texto["scolex_level"]
                st.session_state.finalizado = True
        else:
            if st.session_state.subindo:
                if not st.session_state.primeira_rodada:
                    st.session_state.resultado_final = st.session_state.ultimo_scolex_bom or texto["scolex_level"]
                    st.session_state.finalizado = True
                else:
                    if st.session_state.scolex_atual - 5 >= min_scolex:
                        st.session_state.scolex_atual -= 5
                        st.session_state.subindo = False
                    else:
                        st.session_state.resultado_final = st.session_state.scolex_atual
                        st.session_state.finalizado = True
            else:
                if st.session_state.scolex_atual - 5 >= min_scolex:
                    st.session_state.scolex_atual -= 5
                else:
                    st.session_state.resultado_final = st.session_state.scolex_atual
                    st.session_state.finalizado = True

        st.session_state.primeira_rodada = False
        st.session_state.respostas_enviadas = True

    # Botão para próximo texto
    if st.session_state.respostas_enviadas and not st.session_state.finalizado:
        if st.button("Próximo texto"):
            st.session_state.pop("texto_atual", None)
            st.session_state.pop("shuffled_questions", None)
            for k in list(st.session_state.keys()):
                if k.startswith("q"):
                    st.session_state.pop(k, None)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
