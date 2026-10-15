# Revisa Documentos

**Compare versões de documentos. Identifique alterações. Confira as evidências.**

O **Revisa Documentos** é uma ferramenta de código aberto para comparar versões de contratos, propostas e outros documentos comerciais. Ela destaca trechos **alterados, adicionados, removidos e preservados**, mostra os textos anterior e revisado lado a lado e permite consultar de onde veio cada informação.

Você pode experimentar o projeto **localmente, sem cadastro, sem chave de API e sem pagar por um modelo de IA**.

> **Situação:** versão alfa (0.1). A revisão textual já funciona; não é uma auditoria jurídica automática nem um serviço público hospedado.

## Experimente agora

Requer **Python 3.11 ou superior**. Na pasta do projeto, execute:

~~~bash
python -m pip install -e ".[ui]"
streamlit run app/streamlit_app.py
~~~

O aplicativo já abre com dois contratos fictícios comparados. Você pode inspecionar as alterações, carregar duas versões próprias, filtrar os resultados e baixar o relatório em Markdown ou JSON.

Para executar apenas a demonstração restrita, sem upload de arquivos e sem ações de IA:

~~~bash
streamlit run app/demo_app.py
~~~

**A demonstração pública ainda não está hospedada.** As instruções estão em [Publicação da demonstração](docs/DEPLOYMENT.md).

### PDF, DOCX e PPTX

A integração opcional com o [Docling](https://github.com/docling-project/docling) permite extrair o texto desses formatos:

~~~bash
python -m pip install -e ".[documents,ui]"
~~~

PDFs digitalizados, compostos apenas por imagem, exigem OCR e **não são suportados** pelo conversor nativo utilizado atualmente.

## Exemplo de comparação

Dois contratos fictícios apresentam:

| Informação | Versão anterior | Versão revisada |
|---|---|---|
| Prazo de pagamento | 30 dias | 45 dias |
| Aviso prévio de rescisão | 60 dias | 90 dias |
| Confidencialidade | Cláusula presente | Cláusula removida |
| Proteção de dados | Cláusula ausente | Cláusula adicionada |

Cada alteração aponta para os trechos originais e suas linhas no texto processado. **O sistema não afirma que uma mudança é irregular ou juridicamente arriscada.**

## Interface de linha de comando

A comparação textual funciona sem conexão com serviços de IA:

~~~bash
python -m pip install -e .
docdiff examples/agreement_before.md examples/agreement_after.md --review-versions
docdiff examples/agreement_before.md examples/agreement_after.md --review-versions --format json
~~~

O comparador de **campos comerciais** também está disponível:

~~~bash
docdiff examples/proposal_a.md examples/proposal_b.md
~~~

Ele compara quatro informações: valor total, prazo de entrega, garantia e prazo de pagamento.

Também existe uma extração **opcional por modelo de linguagem** com validação de trechos originais. Ela precisa ser ativada explicitamente e envia o texto extraído ao provedor configurado. Consulte [Extração por IA](docs/LLM_EXTRACTION.md).

## Qual é a diferença para o Docling?

O **Docling** converte documentos e identifica sua estrutura. O **Revisa Documentos** utiliza essa conversão para oferecer um fluxo de **comparação entre versões, revisão de trechos e geração de relatórios com evidências**. Este repositório é um aplicativo independente, não um substituto nem uma cópia do Docling.

~~~text
Documentos TXT / MD / PDF / DOCX / PPTX
                  |
        Leitura local ou Docling
                  |
        +---------+----------+
        |                    |
  Revisão de versões   Comparação de campos
  • trechos            • valores normalizados
  • alterações         • evidências
  • antes/depois       • regras locais por padrão
        |                    |
  Interface e relatórios em Markdown / JSON
~~~

A análise de mudanças de significado com um modelo de IA está sendo desenvolvida em [um PR separado](https://github.com/mxthsu/docdiff-ai/pull/10), ainda **não integrado à versão principal**. A comparação de versões presente na `main` utiliza correspondência textual e similaridade lexical, não uma compreensão semântica completa.

## Limitações importantes

- A similaridade textual não garante equivalência de significado. Paráfrases e mudanças complexas podem ser classificadas incorretamente.
- A detecção de números diferentes **não equivale a uma avaliação de risco**.
- Trechos de PDF/Office convertidos apontam para linhas do Markdown gerado, **não para coordenadas físicas na página original**.
- PDFs somente com imagem exigem OCR, ainda não oferecido nessa configuração.
- Não há hospedagem pública verificada nem proteção suficiente para processar uploads de pessoas desconhecidas em um serviço aberto.
- Não existem métricas comprovadas de desempenho com modelos de IA em documentos reais.
- Os relatórios apoiam a revisão humana; não aprovam contratos automaticamente.

## Documentação técnica

Os arquivos técnicos abaixo continuam em inglês nesta etapa. Somente este README e a interface do site estão sendo padronizados em português.

- [Revisão de versões](docs/VERSION_REVIEW.md)
- [Formato dos arquivos e Docling](docs/DOCUMENTS.md)
- [Extração opcional por IA e privacidade](docs/LLM_EXTRACTION.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Publicação segura da demonstração](docs/DEPLOYMENT.md)
- [Ferramentas semelhantes](docs/ALTERNATIVES.md)
- [Como contribuir](CONTRIBUTING.md)

## Desenvolvimento e qualidade

~~~bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m unittest discover -s tests -v
python .github/scripts/check_skills.py
python scripts/evaluate_extraction.py --mode rules
~~~

O teste opcional da interface exige `.[ui]`:

~~~bash
python scripts/smoke_ui.py
~~~

Os testes reais de conversão estão documentados em [Formatos e testes](docs/DOCUMENTS.md).

### Idioma do projeto

Nesta etapa, **o README e os textos visíveis do site utilizam português do Brasil (pt-BR)**. O código, as skills, os testes, a documentação técnica e os identificadores internos podem continuar em inglês. Os comandos e o endereço `mxthsu/docdiff-ai` foram preservados para manter a compatibilidade.

A versão em inglês do README e do site será organizada posteriormente, com uma estratégia de internacionalização própria.

**Licença:** MIT. Contribuições e relatos de problemas reproduzíveis são bem-vindos. Não envie documentos confidenciais para issues, PRs ou testes.
