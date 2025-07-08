import os
import json
import streamlit as st
import sys
import csv
from datetime import datetime

json_folder = "TEXTS_QUESTIONS"
resposta_arquivo = "resultados_usuarios.csv"

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

def rerun():
    sys.exit()

def main():
    st.title("📘 Teste Adaptativo de Leitura - Escala Scolex")

    # Coleta nome e série escolar
    if "nome" not in st.session_state:
        nome = st.text_input("Qual seu nome completo?")
        serie = st.selectbox(
            "Qual sua série escolar?",
            options=[str(i) for i in range(0, 13)] + ["Graduado"]
        )

        if st.button("Começar teste"):
            if nome.strip() == "":
                st.warning("⚠️ Por favor, insira seu nome.")
                return

            st.session_state.nome = nome
            st.session_state.serie_escolar = serie

            # Define ponto de entrada inicial baseado na série escolar
            if serie == "Graduado":
                st.session_state.scolex_atual = 60
            else:
                serie_int = int(serie)
                if 0 <= serie_int <= 3:
                    st.session_state.scolex_atual = 20
                elif 4 <= serie_int <= 6:
                    st.session_state.scolex_atual = 30
                elif 7 <= serie_int <= 9:
                    st.session_state.scolex_atual = 40
                elif 10 <= serie_int <= 12:
                    st.session_state.scolex_atual = 50
            st.rerun()
        return  # Aguarda início do teste

    # Inicialização do estado
    if "textos" not in st.session_state:
        st.session_state.textos = carregar_textos()
        st.session_state.usados = set()
        st.session_state.finalizado = False
        st.session_state.subindo = True
        st.session_state.resultado_final = None
        st.session_state.ultimo_scolex_bom = None
        st.session_state.primeira_rodada = True
        st.session_state.respostas_enviadas = False

    # Resultado final e coleta de opinião
    if st.session_state.finalizado:
        st.success(f"✅ Resultado final do teste: seu nível Scolex é {st.session_state.resultado_final:.2f}")

        if "opiniao" not in st.session_state:
            opiniao = st.text_area("✍️ Dê sua opinião sobre o teste (dificuldade, resultado, formato de aplicação, etc...)")
            if st.button("Salvar opinião e finalizar"):
                salvar_resultado(
                    nome=st.session_state.nome,
                    serie=st.session_state.serie_escolar,
                    resultado=st.session_state.resultado_final,
                    opiniao=opiniao
                )
                st.session_state.opiniao = opiniao
                st.success("📁 Obrigado! Sua opinião foi registrada.")
            return

        if st.button("🔁 Reiniciar teste"):
            for key in ["textos", "usados", "scolex_atual", "finalizado", "subindo", "resultado_final",
                        "ultimo_scolex_bom", "primeira_rodada", "respostas_enviadas", "texto_atual",
                        "nome", "serie_escolar", "opiniao"]:
                st.session_state.pop(key, None)
            rerun()
        return

    # Seleciona texto
    if "texto_atual" not in st.session_state:
        texto = escolher_texto(st.session_state.textos, st.session_state.scolex_atual, st.session_state.usados)
        if texto is None:
            st.warning("🚫 Nenhum texto restante para o nível atual.")
            if st.session_state.ultimo_scolex_bom is not None:
                st.session_state.resultado_final = st.session_state.ultimo_scolex_bom
            else:
                st.session_state.resultado_final = st.session_state.scolex_atual
            st.session_state.finalizado = True
            return
        st.session_state.texto_atual = texto
        st.session_state.usados.add(texto["filename"])

    texto = st.session_state.texto_atual

    st.subheader(f"📈 Nível Scolex: {texto['scolex_level']:.2f}")
    st.markdown(f"### {texto['titulo']}")
    st.markdown(texto["texto"])

    st.markdown("### Perguntas")
    respostas = []
    for i, pergunta in enumerate(texto["perguntas"]):
        resposta = st.radio(
            f"{i+1}. {pergunta['pergunta']}",
            options=list(enumerate(pergunta["alternativas"])),
            format_func=lambda x: x[1],
            key=f"q{i}"
        )
        respostas.append(resposta[0])

    if st.button("Enviar respostas"):
        acertos = sum([1 for i, p in enumerate(texto["perguntas"]) if respostas[i] == p["resposta_correta"]])
        total = len(texto["perguntas"])
        percentual = (acertos / total) * 100

        st.markdown(f"### 🎯 Você acertou {acertos} de {total} ({percentual:.1f}%)")

        if percentual >= 80:
            st.success("✅ Desempenho bom!")
            if not st.session_state.primeira_rodada:
                st.session_state.ultimo_scolex_bom = texto["scolex_level"]
            if st.session_state.subindo:
                st.session_state.scolex_atual += 5
            else:
                st.session_state.resultado_final = texto["scolex_level"]
                st.session_state.finalizado = True
        else:
            st.warning("⚠️ Desempenho abaixo do esperado.")
            if st.session_state.subindo:
                if not st.session_state.primeira_rodada:
                    if st.session_state.ultimo_scolex_bom is not None:
                        st.session_state.resultado_final = st.session_state.ultimo_scolex_bom
                    else:
                        st.session_state.resultado_final = texto["scolex_level"]
                    st.session_state.finalizado = True
                else:
                    st.session_state.scolex_atual -= 5
                    st.session_state.subindo = False
            else:
                st.session_state.scolex_atual -= 5

        st.session_state.primeira_rodada = False
        st.session_state.respostas_enviadas = True

    if st.session_state.respostas_enviadas and not st.session_state.finalizado and st.button("Próximo texto"):
        st.session_state.pop("texto_atual")
        st.session_state.respostas_enviadas = False
        rerun()

if __name__ == "__main__":
    main()
