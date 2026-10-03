"""One inference followed by deterministic validation, merge and compilation."""

from copy import deepcopy
from time import perf_counter

from slot_extractor.evaluation.assertions import canonical
from slot_extractor.prompts.template import PromptBuilder
from slot_extractor.schemas.output import parse_model_json
from slot_extractor.schemas.search_state import empty_search_state
from slot_extractor.search import (
    QueryCompileError,
    SearchValidationError,
    collect_validation_errors,
    compile_typesense_query,
    merge_search_state,
    validate_patch,
    validate_state,
)

from .models import ModelSideResult, SearchEvent, SearchTrace


def state_diff(before, after, registry):
    def value(state, name):
        if name in {"query_text", "sort"}:
            return state[name]
        return {
            key: [c for c in state[key] if c["field"] == name]
            for key in ("hard_filters", "soft_preferences")
        }

    rows = []
    for name in [*registry.model_extractable_fields(), "query_text", "sort"]:
        old, new = value(before, name), value(after, name)
        if canonical(old) != canonical(new):
            rows.append({"field": name, "before": old, "after": new})
    return rows


class SearchComparisonOrchestrator:
    def __init__(self, backend, registry, *, currency="USD", model_id=None):
        self.backend = backend
        self.registry = registry
        self.currency = currency
        self.model_id = model_id or backend.model
        self.builder = PromptBuilder(registry)

    def run(self, user_input, current_search_state=None):
        current = (
            validate_state(current_search_state, self.registry).to_dict()
            if (current_search_state is not None)
            else None
        )
        result = ModelSideResult(
            self.model_id, current_state=deepcopy(current), next_state=deepcopy(current)
        )
        events = []
        stage = "inference"
        started = perf_counter()
        inference_ms = 0.0
        try:
            messages = self.builder.build_messages(
                {
                    "current_search_state": current,
                    "user_input": user_input,
                }
            )
            inference_started = perf_counter()
            try:
                generation = self.backend.generate(messages)
            finally:
                inference_ms = (perf_counter() - inference_started) * 1000
            result.raw_output = generation.text
            result.metrics = {
                "model": generation.model,
                "input_tokens": generation.input_tokens,
                "output_tokens": generation.output_tokens,
                "first_token_ms": generation.first_token_ms,
                "backend_total_ms": generation.total_ms,
                "tokens_per_s": generation.tokens_per_s,
            }
            events.append(SearchEvent("search_patch_generated", {"raw_output": generation.text}))
            stage = "parse"
            decoded = parse_model_json(generation.text)
            result.parsed_patch = decoded
            events.append(SearchEvent("search_patch_parsed", {"patch": decoded}))
            stage = "validation"
            errors = collect_validation_errors(decoded, self.registry)
            result.validation = {"valid": not errors, "errors": [vars(e) for e in errors]}
            events.append(SearchEvent("search_patch_validated", result.validation))
            if errors:
                raise SearchValidationError(errors)
            patch = validate_patch(decoded, self.registry)
            stage = "merge"
            result.merged_state = merge_search_state(current, patch, self.registry).to_dict()
            result.state_diff = state_diff(
                current or empty_search_state().to_dict(), result.merged_state, self.registry
            )
            events.append(
                SearchEvent(
                    "search_state_merged",
                    {
                        "state": result.merged_state,
                        "diff": result.state_diff,
                    },
                )
            )
            stage = "compile"
            result.compiled_query = compile_typesense_query(
                result.merged_state, self.registry, currency=self.currency
            ).to_dict()
            events.append(SearchEvent("search_query_compiled", result.compiled_query))
            result.next_state = deepcopy(result.merged_state)
            result.status = "complete"
        except (ValueError, QueryCompileError, ConnectionError, OSError) as exc:
            if stage == "parse":
                result.validation = {
                    "valid": False,
                    "errors": [{"code": "invalid_json", "path": "$", "message": str(exc)}],
                }
                events.append(SearchEvent("search_patch_validated", result.validation))
            result.error = {"stage": stage, "message": str(exc)}
            events.append(SearchEvent("search_error", result.error))
        # Unexpected backend exceptions are handled by the app with diagnostic traceback.
        result.metrics["inference_duration_ms"] = inference_ms
        result.metrics["pipeline_duration_ms"] = (perf_counter() - started) * 1000
        events.append(SearchEvent("search_metrics", result.metrics))
        return SearchTrace(result, tuple(events))
