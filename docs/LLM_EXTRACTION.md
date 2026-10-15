# LLM-assisted extraction with verified text evidence

The default DocDiff AI comparison runs offline with deterministic rules. The
optional `--extraction llm` mode asks an explicitly configured language model
to propose candidate values for the same four fields:

- `total_price`
- `delivery_days`
- `warranty_months`
- `payment_days`

The model is **not a source of truth**. Each response must pass local verification.

## Use (explicitly opt in)

The endpoint must be HTTPS, except for `http://localhost`, `127.0.0.1`
or `[::1]`. The provider needs an OpenAI-compatible chat-completions API
supporting `response_format: {"type":"json_object"}`; not every model does.

~~~powershell
$env:DOCDIFF_API_KEY = "your-provider-api-key"
$env:DOCDIFF_MODEL = "supported-chat-model"
$env:DOCDIFF_BASE_URL = "https://api.openai.com/v1"
docdiff examples/proposal_a.md examples/proposal_b.md --extraction llm --format json
~~~

You may also select **LLM com validação textual** in the Streamlit UI.
Localhost providers can omit `DOCDIFF_API_KEY`, but remote HTTPS providers must
have a key. A provider may still require extra configuration or reject the
JSON-response mode; those failures are surfaced instead of silently falling
back to unverified values.

**Data privacy:** enabling this mode sends the **entire extracted document
text**, up to 40,000 characters per document, to the configured provider.
Do not use private or regulated documents unless your organization permits
this disclosure. The `--ai-summary` option is separate and transmits only
structured findings and source excerpts. With the default `rules` mode, no
network request is made.

The request is bounded (45-second timeout, up to 80 KB returned); documents
over the text limit fail explicitly instead of silently truncating. The model
is called once per document, without tools or automatic follow-up actions.

## Verification contract

A provider returns one JSON object with a `candidates` array:

~~~json
{
  "candidates": [
    {
      "field": "delivery_days",
      "raw": "30",
      "quote": "Delivery will take 30 days."
    }
  ]
}
~~~

For a candidate to be accepted:

1. The field must be requested and supported.
2. The quote must occur **exactly once** and entirely within one source-text
   line (for PDF/Office: in Docling-exported Markdown, not a PDF page).
3. The raw value must be a substring of the quote and have a valid
   currency/number shape.
4. The quote must include the field's context and expected unit or currency.
5. The normalized value must be valid.

Unsupported candidates are rejected locally. Multiple verified conflicting
values produce `ambiguous`; missing accepted values produce `missing`.
Malformed JSON or provider failures return an error, never fabricated evidence.

This is **literal-source verification, not semantic fact checking**. A quote
can be real and still be conditional, negated, misleading, or not the agreed
contractual value. Users must review the meaning of every accepted field.
Document text can contain prompt-injection attempts. Our system prompt treats
it as data, and the LLM has no tools, but no guarantee of full resistance is
implied.

## Evaluation

The synthetic, versioned dataset lives at `evaluation/dataset_v1.json`.
It covers labeled fields, English prose, Markdown tables, missing values,
conflicting mentions and adversarial text.

Run the **offline rules baseline**:

~~~bash
python scripts/evaluate_extraction.py --mode rules
~~~

Run an **actual model evaluation** only if you intend to pay the provider
and have configured access:

~~~bash
python scripts/evaluate_extraction.py --mode llm --allow-external
~~~

Evaluation returns exact field-value precision and recall across the supplied
synthetic cases, case-level exact matches, prompt version, model identity and
wall time. It does not estimate provider costs; token billing and pricing are
not measured. A model result is not valid without its provider and version.

Offline unit tests use a fake completion function to test the verification
contract and adversarial inputs without calling any model or spending money.
**Those mock tests are not model accuracy measurements.**

## Trade-offs and limitations

- Conservative quote matching sacrifices recall when source text spans lines
  or a quote appears identically more than once.
- A supported field can still require human semantic judgment.
- Long documents are not silently truncated; batching and page-level source
  anchors are future work.
- Extraction is limited to four fields; schema-driven extensibility is
  planned, not implemented here.
- Prompt version: `verified-fields-v1`.
- JSON mode records how many candidates were rejected and their reason codes,
  without persisting input texts or secrets.
