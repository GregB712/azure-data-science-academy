"""Governance and FinOps helpers for Module 9.

A required-tag policy checker (the local analogue of an Azure Policy "require a
tag" rule) and a monthly cost estimator with per-domain allocation. Both are
pure, testable functions; prices are inputs you supply from the pricing
calculator or the Retail Prices API, never baked-in truth.
"""

from .tags import DEFAULT_TAG_POLICY, check_tags
from .cost_estimate import CostLine, DEFAULT_PLATFORM, estimate

__all__ = ["DEFAULT_TAG_POLICY", "check_tags", "CostLine", "DEFAULT_PLATFORM", "estimate"]
