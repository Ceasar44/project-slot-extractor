from typing import Protocol

from slot_extractor.evaluation.assertions import EvaluationContext
from slot_extractor.schemas.results import DimensionScore


class Scorer(Protocol):
    def score(self, context: EvaluationContext) -> dict[str, DimensionScore]: ...
