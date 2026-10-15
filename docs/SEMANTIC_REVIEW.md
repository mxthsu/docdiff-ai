# Semantic review (experimental)

The selected change can be reviewed with an optional language model.
This workflow is separate from the offline document comparison.

The model proposes a category and an explanation, accompanied by an exact
quotation from each document version. The application checks that both
quotations occur in their respective original passages.

Verified quotations do not establish a correct interpretation: a person
must still evaluate the proposed meaning.

## Workflow

Run the local Streamlit workspace. Open a modified passage, inspect both
versions, explicitly authorize the optional model request and select
the interpretation action. Only the selected text from each side is submitted.

The public example-only mode never exposes the model controls.

## Categories

- possible change
- possible paraphrase
- unclear

The analysis may highlight potential changes involving obligations, exceptions,
deadlines, amounts, negation or other terms.

## Reproducible evaluation

Use the synthetic labelled dataset and the offline reference calculation:

    python scripts/evaluate_semantic.py --mode baseline

Optional external-model evaluations require both the selected model settings
and an explicit execution flag:

    python scripts/evaluate_semantic.py --mode llm --allow-external

The offline reference correctly matched six of eight labelled changed pairs
in the nine-case synthetic dataset. One identical pair was skipped.
This result does not measure model accuracy.

## Limitations

The method interprets only previously paired modified passages. Passage
alignment is still lexical, not semantic. Automatic risk decisions, legal
conclusions, page coordinates and production model metrics are out of scope.
