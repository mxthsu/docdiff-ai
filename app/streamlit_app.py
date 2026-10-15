"""Optional human-friendly interface to the core comparison engine."""

import json

import streamlit as st

from docdiff_ai.ai import AIReviewError, summarize_with_llm
from docdiff_ai.core import STATUS_LABELS, compare, report_to_markdown
from docdiff_ai.documents import DocumentReadError, from_bytes

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
        "A síntese por IA é opcional e não substitui a evidência original."
    )

if st.button("Comparar documentos", type="primary", disabled=not (2 <= len(uploaded) <= 10)):
    try:
        documents = [from_bytes(file.name, file.getvalue()) for file in uploaded]
        report = compare(documents)
        st.session_state["report"] = report
    except (DocumentReadError, ValueError) as exc:
        st.error(str(exc))

if "report" in st.session_state:
    report = st.session_state["report"]
    st.subheader("Resultados")
    for result in report.fields:
        with st.expander(
            f"{result.label} — {STATUS_LABELS[result.status]}", expanded=result.status != "match"
        ):
            for name, evidence in result.evidence.items():
                st.markdown(f"**{name}**")
                if not evidence:
                    st.caption("Informação não identificada.")
                for hit in evidence:
                    st.write(f"Linha {hit.line} · {hit.raw}")
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
