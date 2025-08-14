import os
import json
import streamlit as st
import sys
import csv
from datetime import datetime
import base64
import random
from pathlib import Path
from PIL import Image



# ============================
# Funções utilitárias
# ============================
# Caminho da logo — garante que funciona no deploy e local
logo_path = Path(__file__).parent / "scolados_logo.png"

if not logo_path.exists():
    st.error("❌ Arquivo da logo 'scolados_logo.png' não encontrado.")
else:
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()

def rerun():
    sys.exit()

# ============================
# Configurações iniciais
# ============================
json_folder = "TEXTS_QUESTIONS"
resposta_arquivo = "resultados_usuarios.csv"

# ============================
# CSS + HEADER FIXO
# ============================
st.markdown(
    f"""
    <style>
        .block-container {{
            padding: 0;
            max-width: 100% !important;
            background-color: white;
        }}
        body {{
            background-color: white;
            margin: 0;
        }}
        .top-bar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 999;
            background: white;
            color: #2F97A1;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            border-bottom: 2px solid #e0e0e0;
            height: 60px;
        }}
        .top-bar img {{
            height: 40px;
            margin-right: 15px;
        }}
        .top-bar h1 {{
            font-size: 1.5rem;
            margin: 0;
            font-weight: bold;
            color: #2F97A1;
        }}
        .intro-bar {{
            position: fixed;
            top: 60px;
            left: 0;
            right: 0;
            z-index: 998;
            background: linear-gradient(to right, #226DAA, #2F97A1);
            color: white;
            padding: 8px 20px;
            font-size: 1rem;
            font-weight: 500;
            height: 105px;
            display: flex;
            align-items: center;
        }}
        .content-container {{
            padding-top: 175px;
            background-color: white;
        }}
        .teste-box {{
            border: 2px solid #2F97A1;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            background-color: #f9f9f9;
            max-height: calc(100vh - 180px);
            overflow-y: auto;
        }}
    </style>

    <div class="top-bar">
        <img src="https://raw.githubusercontent.com/PelizariGabriel/Scolex-Test/5cab7cc6b04920291b868be42e4ba29e14cc2b30/scolados_logo.png" alt="Logo">
        <h1>Scolex - Teste Adaptativo de Leitura</h1>
    </div>
    <div class="intro-bar">
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
    # Container principal com padding para barra fixa
    with st.container():
        st.markdown('<div class="content-container teste-box" style="margin-top:100px;">', unsafe_allow_html=True)

        # ======== Coleta nome e série escolar ========
        if "nome" not in st.session_state:
            nome = st.text_input("Qual seu nome completo?")
            serie = st.selectbox(
                "Qual sua série escolar?",
                options=[str(i) for i in range(1, 13)] + ["Graduado"]
            )
            if st.button("Começar teste"):
                if nome.strip() == "":
                    st.warning("⚠️ Por favor, insira seu nome.")
                    return
                st.session_state.nome = nome
                st.session_state.serie_escolar = serie
                # Define ponto de entrada inicial
                if serie == "Graduado":
                    st.session_state.scolex_atual = 70
                else:
                    serie_int = int(serie)
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
                return
            if st.button("🔁 Reiniciar teste"):
                for key in list(st.session_state.keys()):
                    st.session_state.pop(key)
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

        respostas = []

        # Embaralha alternativas para cada pergunta
        shuffled_questions = []
        for pergunta in texto["perguntas"]:
            alternativas = list(enumerate(pergunta["alternativas"]))
            random.shuffle(alternativas)
            shuffled_questions.append({
                "pergunta": pergunta["pergunta"],
                "alternativas": alternativas,
                "resposta_correta": next(i for i, alt in alternativas if i == pergunta["resposta_correta"])
            })

        for i, pergunta in enumerate(shuffled_questions):
            resposta = st.radio(
                f"{i+1}. {pergunta['pergunta']}",
                options=pergunta["alternativas"],
                format_func=lambda x: x[1],
                key=f"q{i}"
            )
            respostas.append(resposta[0])

        if st.button("Enviar respostas"):
            acertos = sum([1 for i, p in enumerate(shuffled_questions) if respostas[i] == p["resposta_correta"]])
            total = len(shuffled_questions)
            percentual = (acertos / total) * 100

            st.markdown(f"<h3>🎯 Você acertou {acertos} de {total} ({percentual:.1f}%)</h3>", unsafe_allow_html=True)

            # Atualiza nível Scolex normalmente
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

        # ===== Botão manual para avançar para o próximo texto =====
        if st.session_state.respostas_enviadas and not st.session_state.finalizado:
            if st.button("Próximo texto"):
                st.session_state.pop("texto_atual")
                st.session_state.respostas_enviadas = False
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)  # Fecha container teste-box

if __name__ == "__main__":
    main()
