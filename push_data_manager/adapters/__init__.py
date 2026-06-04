from .alpha import AlphaAdapter
from .beta import BetaAdapter
from .protocol import ATSAdapter, NormalizedApplication

REGISTRY: dict[str, ATSAdapter] = {
    "alpha": AlphaAdapter(),
    "beta": BetaAdapter(),
}

__all__ = ["REGISTRY", "ATSAdapter", "NormalizedApplication"]
