"""DocDiff AI review workspace: a useful local demo with no external credentials."""

from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from docdiff_ai.ai import AIReviewError, summarize_with_llm
from docdiff_ai.core import STATUS_LABELS, SourceDocument, compare, report_to_markdown
from docdiff_ai.documents import DocumentReadError, from_bytes
from docdiff_ai.verified_extraction import ExtractionError, VerifiedLLMExtractor
from docdiff_ai.version_diff import ReviewReport, compare_versions, review_to_markdown

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
DEMO_ONLY = os.getenv("DOCDIFF_DEMO_ONLY") == "1"
STATUS = {
    "modified": "Alterado",
    "added": "Adicionado",
    "removed": "Removido",
    "unchanged": "Preservado",
}
MATCH_LABELS = {
    "identical_text": "texto idêntico",
    "same_heading": "mesmo título",
    "lexical_similarity": "similaridade textual",
    "unmatched": "sem correspondência",
}
MARKERS = {
    "modified": "🟠",
    "added": "🟢",
    "removed": "🔴",
    "unchanged": "⚪",
}

st.set_page_config(page_title="Revisa Documentos | Revisão de documentos", page_icon="📑", layout="wide")
st.markdown(
    """
    <style>
      .block-container {max-width: 1220px; padding-top: 2rem; padding-bottom: 3rem;}
      [data-testid="stMetric"] {
          border: 1px solid rgba(128, 128, 128, 0.25);
          border-radius: 12px; padding: 15px; }
      .docdiff-kicker {color: #d27b37; font-weight: 750; letter-spacing: .09em;
          font-size: .80rem; margin-bottom: .25rem;}
      .docdiff-heading {font-size: clamp(2rem, 3.2vw, 3.1rem); font-weight: 750;
          line-height: 1.08; margin-bottom: 0.75rem;}
      .docdiff-subtitle {font-size: 1.05rem; opacity: .78; margin-bottom: 1.3rem;}
    </style>
    <div class="docdiff-kicker">REVISA DOCUMENTOS · CÓDIGO ABERTO</div>
    <div class="docdiff-heading">Documentos diferentes.<br>Decisões com evidências.</div>
    <div class="docdiff-subtitle">Revise alterações entre versões e encontre divergências
      com o texto original sempre à vista.</div>
    """,
    unsafe_allow_html=True,
)
st.caption("Prévia alfa · comparação textual local · não substitui uma análise jurídica ou humana")

mode = st.radio(
    "Escolha o fluxo",
    ("Revisar duas versões", "Comparar campos entre documentos"),
    horizontal=True,
    label_visibility="collapsed",
)


# Exemplos mostrados no site. Mantemos os arquivos técnicos do repositório
# inalterados para não afetar a CLI ou as suítes de testes existentes.
DEMO_ANTES = """# Contrato de prestação de serviços

## 1. Objeto
A contratada realizará serviços de suporte e manutenção de equipamentos.

## 2. Pagamento
O pagamento será realizado em até 30 dias após o recebimento da fatura.

## 3. Rescisão
Qualquer parte poderá encerrar o contrato com aviso prévio de 60 dias.

## 4. Confidencialidade
As partes preservarão o sigilo das informações comerciais recebidas.

## 5. Foro
As partes elegem a comarca indicada no instrumento principal.

*Exemplo fictício para demonstração. Não constitui orientação jurídica.*
"""

DEMO_DEPOIS = """# Contrato de prestação de serviços

## 1. Objeto
A contratada realizará serviços de suporte e manutenção de equipamentos.

## 2. Pagamento
O pagamento será realizado em até 45 dias após o recebimento da fatura.

## 3. Rescisão
Qualquer parte poderá encerrar o contrato com aviso prévio de 90 dias.

## 4. Proteção de dados
Cada parte deverá restringir o acesso aos dados pessoais aos colaboradores autorizados.

## 5. Foro
As partes elegem a comarca indicada no instrumento principal.

*Exemplo fictício para demonstração. Não constitui orientação jurídica.*
"""


def demo_documents() -> tuple[SourceDocument, SourceDocument]:
    return (
        SourceDocument("acordo_anterior.md", DEMO_ANTES.strip()),
        SourceDocument("acordo_revisado.md", DEMO_DEPOIS.strip()),
    )


def render_review(report: ReviewReport) -> None:
    st.divider()
    st.subheader("O que mudou entre as versões?")
    st.caption(
        f"{report.before_name}  →  {report.after_name}  · "
        "alinhamento textual, sem inferência de risco ou significado por IA"
    )
    metrics = st.columns(4)
    for item, key in zip(metrics, ("modified", "added", "removed", "unchanged"), strict=True):
        with item:
            st.metric(STATUS[key], report.counts[key])
    st.caption(
        "Mudanças no texto são verificadas. O pareamento de trechos semelhantes é "
        "heurístico e deve ser confirmado por uma pessoa."
    )
    view = st.selectbox(
        "Exibir trechos",
        ("Alterados, adicionados e removidos", "Todos", "Apenas preservados"),
        key="review_filter",
    )
    visible = [
        change
        for change in report.changes
        if (
            view == "Todos"
            or (view == "Apenas preservados" and change.status == "unchanged")
            or (view == "Alterados, adicionados e removidos" and change.status != "unchanged")
        )
    ]
    if not visible:
        st.info("Nenhum trecho nessa categoria.")
    for i, change in enumerate(visible, start=1):
        current = change.after or change.before
        heading = current.heading or f"Trecho {i}"
        label = f"{MARKERS[change.status]} {STATUS[change.status]} · {heading}"
        if change.numbers_changed:
            label += " · números diferentes"
        with st.expander(label, expanded=change.status != "unchanged"):
            before_col, after_col = st.columns(2, gap="medium")
            for column, title, passage in (
                (before_col, "VERSÃO ANTERIOR", change.before),
                (after_col, "VERSÃO REVISADA", change.after),
            ):
                with column:
                    st.markdown(f"**{title}**")
                    if passage is None:
                        st.caption("Trecho não presente nesta versão")
                        continue
                    location = (
                        "Markdown convertido"
                        if passage.reference_type == "converted_markdown_line"
                        else "Arquivo texto"
                    )
                    st.caption(
                        f"{passage.document} · linhas {passage.start_line}–{passage.end_line} ({location})"
                    )
                    st.code(passage.text, language=None)
            if change.numbers_changed:
                st.warning("O trecho contém números diferentes. Confira valores, unidades e contexto.")
            if change.status == "modified":
                st.caption(
                    f"Associação dos trechos: {MATCH_LABELS.get(change.matched_by, 'não identificada')}. "
                    "Sem garantia de equivalência semântica."
                )

    st.divider()
    st.subheader("Exportar relatório")
    left, right = st.columns(2)
    with left:
        st.download_button(
            "Baixar relatório de revisão (.md)",
            review_to_markdown(report),
            file_name="revisao_de_versoes.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with right:
        st.download_button(
            "Baixar evidências estruturadas (.json)",
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            file_name="revisao_de_versoes.json",
            mime="application/json",
            use_container_width=True,
        )
    st.caption(
        "Referências de arquivos convertidos apontam para linhas do Markdown extraído, "
        "não para páginas físicas do PDF."
    )


if mode == "Revisar duas versões":
    st.subheader("Experimente com um contrato fictício")
    st.caption(
        "Compare cláusulas de pagamento, rescisão e outras condições. "
        "Os exemplos são sintéticos e não exigem API nem login."
    )
    with st.container(border=True):
        left, right = st.columns([1, 1])
        with left:
            if st.button("▶ Executar demonstração", type="primary", use_container_width=True):
                before, after = demo_documents()
                st.session_state["version_review"] = compare_versions(before, after)
                st.session_state["version_review_origin"] = "demo"
        with right:
            st.caption("Exemplo: 30 → 45 dias para pagamento; 60 → 90 dias de aviso prévio.")
    uploads = []
    if DEMO_ONLY:
        st.caption("Modo público de demonstração: uploads desativados por segurança.")
    else:
        uploads = st.file_uploader(
            "Ou envie duas versões na ordem anterior → revisada",
            type=["md", "txt", "pdf", "docx", "pptx"],
            accept_multiple_files=True,
            key="version_uploads",
        )
    if not DEMO_ONLY and st.button(
        "Comparar meus documentos",
        disabled=len(uploads) != 2,
        use_container_width=True,
    ):
        try:
            before, after = (from_bytes(file.name, file.getvalue()) for file in uploads)
            st.session_state["version_review"] = compare_versions(before, after)
            st.session_state["version_review_origin"] = "upload"
        except (DocumentReadError, ValueError) as exc:
            st.error(str(exc))
    if "version_review" not in st.session_state:
        before, after = demo_documents()
        st.session_state["version_review"] = compare_versions(before, after)
        st.session_state["version_review_origin"] = "demo"
    if st.session_state["version_review_origin"] == "demo":
        st.info("Você está vendo uma comparação real de arquivos de exemplo fictícios.")
    render_review(st.session_state["version_review"])

else:
    st.subheader("Compare informações comerciais")
    st.caption(
        "Encontre valores, prazos e garantias em até 10 documentos. As regras locais funcionam sem Internet."
    )
    if DEMO_ONLY:
        st.caption("Modo público de demonstração: uploads e provedores externos estão desativados.")
        if st.button("Comparar propostas de exemplo", type="primary"):
            example_files = (EXAMPLES / "proposal_a.md", EXAMPLES / "proposal_b.md")
            documents = [
                SourceDocument(path.name, path.read_text(encoding="utf-8")) for path in example_files
            ]
            st.session_state["field_report"] = compare(documents)
            st.session_state["llm_rejected"] = None
    else:
        uploads = st.file_uploader(
            "Selecione de 2 a 10 arquivos (TXT, MD, PDF, DOCX ou PPTX)",
            type=["txt", "md", "pdf", "docx", "pptx"],
            accept_multiple_files=True,
            key="field_uploads",
        )
        extraction_mode = st.radio(
            "Extração",
            ["Regras locais (offline)", "LLM com validação textual"],
            horizontal=True,
        )
        if extraction_mode.startswith("LLM"):
            st.warning(
                "Ao comparar, o texto completo extraído será enviado ao provedor configurado "
                "em DOCDIFF_BASE_URL. Não use documentos confidenciais sem autorização."
            )
        if st.button("Comparar informações", type="primary", disabled=not (2 <= len(uploads) <= 10)):
            try:
                documents = [from_bytes(file.name, file.getvalue()) for file in uploads]
                extractor = VerifiedLLMExtractor() if extraction_mode.startswith("LLM") else None
                report = compare(documents, extractor=extractor) if extractor else compare(documents)
                st.session_state["field_report"] = report
                st.session_state["llm_rejected"] = len(extractor.rejected) if extractor else None
            except (DocumentReadError, ValueError, ExtractionError) as exc:
                st.error(str(exc))

    if "field_report" in st.session_state:
        report = st.session_state["field_report"]
        st.divider()
        st.subheader("Resultados por campo")
        if st.session_state.get("llm_rejected") is not None:
            st.caption(
                f"{st.session_state['llm_rejected']} sugestões do LLM descartadas "
                "na validação de evidências. Citação não garante interpretação correta."
            )
        for result in report.fields:
            with st.expander(
                f"{result.label} · {STATUS_LABELS[result.status]}",
                expanded=result.status != "match",
            ):
                for name, evidence in result.evidence.items():
                    st.markdown(f"**{name}**")
                    if not evidence:
                        st.caption("Informação não encontrada")
                    for hit in evidence:
                        location = (
                            "Linha do Markdown convertido"
                            if hit.reference_type == "converted_markdown_line"
                            else "Linha do arquivo texto"
                        )
                        st.caption(f"{location} {hit.line} · {hit.raw}")
                        st.code(hit.excerpt, language=None)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Baixar relatório (.md)",
                report_to_markdown(report),
                file_name="comparacao.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "Baixar dados (.json)",
                json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
                file_name="comparacao.json",
                mime="application/json",
                use_container_width=True,
            )
        if not DEMO_ONLY and st.button("Gerar resumo por IA (envia trechos a provedor externo)"):
            try:
                st.warning("Resumo não verificado: confira cada informação nas fontes.")
                st.write(summarize_with_llm(report))
            except AIReviewError as exc:
                st.error(str(exc))

with st.sidebar:
    st.markdown("### Sobre a ferramenta")
    st.write(
        "Revisa Documentos é uma ferramenta de código aberto para revisão de documentos. "
        "Utiliza Docling opcionalmente para PDF e Office."
    )
    st.markdown("**Verificação ≠ interpretação**")
    st.caption(
        "Mudanças textuais são verificáveis; pareamentos aproximados "
        "podem falhar. Nenhuma conclusão jurídica é automatizada."
    )
    st.markdown("[Repositório no GitHub](https://github.com/mxthsu/docdiff-ai)")
    st.caption("Dados de demonstração fictícios · processamento local por padrão")
