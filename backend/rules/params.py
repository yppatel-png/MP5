"""
Centralised Academic Rule Parameters Accessor (§2.1, §2.3).
Provides a single audited accessor for all credit ceilings, floors, overload caps,
CGPA cutoffs, and workload ratios from academic_rules.json and config/*.yaml.
Eliminates magic numbers across the planner, validator, buddy, and simulator.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from backend.db.seed_profile import get_seed_dir

_RULES_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def _load_rules_cache() -> Dict[str, Dict[str, Any]]:
    global _RULES_CACHE
    if _RULES_CACHE is not None:
        return _RULES_CACHE
    seed_dir = get_seed_dir()
    rules_file = seed_dir / "academic_rules.json"
    if rules_file.exists():
        with open(rules_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            _RULES_CACHE = {r["rule_id"]: r for r in data}
    else:
        _RULES_CACHE = {}
    return _RULES_CACHE


def reload_rules_cache() -> None:
    """Forces cache refresh (used in tests and admin updates)."""
    global _RULES_CACHE
    _RULES_CACHE = None
    _load_rules_cache()


def get_rule(rule_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full rule metadata including provenance, clause_id, and reason."""
    rules = _load_rules_cache()
    return rules.get(rule_id)


def get_rule_param(rule_id: str, key: str, default: Any = None) -> Any:
    """
    Retrieves a specific parameter for an academic rule.
    If parameter is not found:
      - Returns default if default is explicitly provided (not None).
      - Otherwise raises KeyError indicating the parameter is unavailable.
    """
    rule = get_rule(rule_id)
    if not rule:
        if default is not None:
            return default
        raise KeyError(f"Academic rule '{rule_id}' is unavailable.")
    
    params = rule.get("parameters", {})
    if key in params:
        return params[key]
    
    if default is not None:
        return default
    raise KeyError(f"Parameter '{key}' for academic rule '{rule_id}' is unavailable.")


def get_standard_credit_cap() -> float:
    """Returns statutory or assumed standard semester credit ceiling (from academic_rules.json)."""
    return float(get_rule_param("rule_sem_max_credits", "max_credits"))


def get_min_semester_credits() -> float:
    """Returns statutory or assumed minimum semester credit floor (from academic_rules.json)."""
    return float(get_rule_param("rule_sem_min_credits", "min_credits"))


def get_overload_credit_cap() -> float:
    """Returns overload semester credit ceiling (from academic_rules.json)."""
    return float(get_rule_param("rule_credit_overload_cap", "max_overload_credits"))


def get_overload_cgpa_threshold() -> float:
    """Returns CGPA threshold required for credit overload eligibility (from academic_rules.json)."""
    return float(get_rule_param("rule_credit_overload_cap", "min_cgpa_required"))


def get_workload_hours_ratio() -> float:
    """Returns hours of independent study per credit-week (from academic_rules.json)."""
    return float(get_rule_param("rule_workload_hours", "hours_per_credit_week"))


def get_minor_cgpa_cutoff() -> float:
    """Returns CGPA cutoff for minor program eligibility (e.g. 7.0)."""
    return float(get_rule_param("rule_minor_cse_eligibility", "min_cgpa_cutoff", default=7.0))

