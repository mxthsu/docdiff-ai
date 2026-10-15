"""Optional human-friendly interface to the core comparison engine."""

import json

import streamlit as st

from docdiff_ai.ai import AIReviewError, summarize_with_llm
from docdiff_ai.core import STATUS_LABELS, compare, report_to_markdown
from docdiff_ai.documents import DocumentReadError, from_bytes
from docdiff_ai.verified_extraction import ExtractionError, VerifiedLLMExtractor

st.set_page_config(page_title="DocDiff AI", page_icon="📄", layout="wide")
st.title("DocDiff AI")
st.caption("Compare propostas e documentos com evidências verificáveis.")
st.info("Análise experimental: confira as evidências antes de tomar decisões.")

uploaded = st.file_uploader(
    "Selecione de 2 a 10 arquivos (TXT, MD, PDF, DOCX ou PPTX)",
    type=["txt", "md", "pdf", "docx", "pptx"],
    accept_multiple_files=True,
)
with st.expander("Como funciona"):
    st.write(
        "O motor inicial reconhece valores totais, prazos de entrega, garantia e "
        "prazos de pagamento em linhas rotuladas. PDF e Office exigem Docling. "
        "PDF com texto selecionável utiliza conversão nativa (sem OCR). "
        "Números de linha dos arquivos convertidos referem-se ao Markdown extraído, não à página física. "
        "A síntese por IA é opcional e não substitui a evidência original."
    )

extraction_mode = st.radio(
    "Extração",
    ["Regras locais (offline)", "LLM com validação textual"],
    horizontal=True,
)
if extraction_mode.startswith("LLM"):
    st.warning(
        "Ao comparar, o texto completo dos documentos será enviado ao provedor configurado "
        "em DOCDIFF_BASE_URL. Revise as permissões dos documentos antes de prosseguir."
    )

if st.button("Comparar documentos", type="primary", disabled=not (2 <= len(uploaded) <= 10)):
    try:
        documents = [from_bytes(file.name, file.getvalue()) for file in uploaded]
        extractor = VerifiedLLMExtractor() if extraction_mode.startswith("LLM") else None
        report = compare(documents, extractor=extractor) if extractor else compare(documents)
        st.session_state["report"] = report
        st.session_state["llm_rejected"] = len(extractor.rejected) if extractor else None
    except (DocumentReadError, ValueError, ExtractionError) as exc:
        st.error(str(exc))

if "report" in st.session_state:
    report = st.session_state["report"]
    st.subheader("Resultados")
    if st.session_state.get("llm_rejected") is not None:
        st.caption(
            f"LLM com validação de trechos: {st.session_state['llm_rejected']} candidatos "
            "descartados por não cumprirem as verificações. "
            "Trecho exato não equivale a interpretação semântica correta."
        )
    for result in report.fields:
        with st.expander(
            f"{result.label} — {STATUS_LABELS[result.status]}", expanded=result.status != "match"
        ):
            for name, evidence in result.evidence.items():
                st.markdown(f"**{name}**")
                if not evidence:
                    st.caption("Informação não identificada.")
                for hit in evidence:
                    local = (
                        "Linha do Markdown convertido"
                        if hit.reference_type == "converted_markdown_line"
                        else "Linha do arquivo texto"
                    )
                    st.write(f"{local} {hit.line} · {hit.raw}")
                    st.code(hit.excerpt, language=None)
    st.download_button(
        "Baixar relatório Markdown",
        report_to_markdown(report),
        file_name="comparacao.md",
        mime="text/markdown",
    )
    st.download_button(
        "Baixar resultado JSON",
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        file_name="comparacao.json",
        mime="application/json",
    )
    if st.button("Gerar resumo por IA (envia evidências a um provedor externo)"):
        try:
            st.warning("Texto produzido por IA: revise cada afirmação no relatório.")
            st.write(summarize_with_llm(report))
        except AIReviewError as exc:
            st.error(str(exc))
