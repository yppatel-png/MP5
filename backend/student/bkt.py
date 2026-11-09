"""
Bayesian Knowledge Tracing (BKT) Mastery Estimator.
Implemented with NumPy for auditable, deterministic, and explainable skill modeling.
Incorporates evidence reliability weighting, time decay, soft partial-credit observations,
and multi-session corroboration.
"""

import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.config import load_evidence_config

class BKTEstimator:
    def __init__(self):
        cfg = load_evidence_config()
        bkt_params = cfg.get("bkt_parameters", {})
        self.evidence_weights = cfg.get("evidence_weights", {})
        self.p_init_default = float(bkt_params.get("p_init_default", 0.1))
        self.p_transit = float(bkt_params.get("p_transit_default", 0.2))
        self.p_slip = float(bkt_params.get("p_slip_default", 0.1))
        self.p_guess = float(bkt_params.get("p_guess_default", 0.2))
        self.mastery_threshold = float(bkt_params.get("mastery_threshold", 0.85))
        self.min_items_required = int(bkt_params.get("min_items_required", 3))
        self.min_sessions_required = int(bkt_params.get("min_sessions_required", 2))
        self.decay_half_life_days = float(bkt_params.get("decay_half_life_days", 60.0))

        self.exercise_diffs: Dict[str, int] = {}
        try:
            import json
            from backend.db.seed_profile import get_seed_dir
            seed_dir = get_seed_dir()
            with open(seed_dir / "exercises.json", "r", encoding="utf-8") as f:
                self.exercise_diffs = {e["exercise_id"]: int(e.get("difficulty", 2)) for e in json.load(f)}
        except Exception:
            pass

    def _parse_timestamp(self, ts: Any) -> Optional[datetime]:
        if not ts:
            return None
        if isinstance(ts, datetime):
            return ts
        try:
            cleaned = str(ts).replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    def _apply_time_decay(self, p_curr: float, p_target: float, delta_days: float) -> float:
        """Decays mastery probability toward prior target using half-life exponential decay."""
        if delta_days <= 0.0 or self.decay_half_life_days <= 0.0:
            return p_curr
        alpha = 2.0 ** (-delta_days / self.decay_half_life_days)
        decayed = p_target + (p_curr - p_target) * alpha
        return float(np.clip(decayed, 0.01, 0.99))

    def estimate_skill_mastery(
        self,
        evidence_events: List[Dict[str, Any]],
        prior_probability: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Computes the updated mastery probability and evidence trail for a single skill.
        
        Args:
            evidence_events: chronological list of evidence events (dict with 'value', 'confidence', 'source_type')
            prior_probability: optional pre-computed prior from completed courses (e.g. 0.6 if passed course)
        """
        baseline_prior = float(prior_probability) if prior_probability is not None else float(self.p_init_default)
        baseline_prior = float(np.clip(baseline_prior, 0.01, 0.99))
        p_l = baseline_prior

        if not evidence_events:
            return {
                "p_mastery": round(p_l, 3),
                "confidence": 0.2 if prior_probability else 0.1,
                "mastered": False,  # No explicit evidence, cannot confirm mastery
                "evidence_count": 0,
                "evidence_trail": ["No explicit test evidence recorded; using baseline prior."]
            }

        trail = []
        total_weight = 0.0
        all_self_declared = all(ev.get("source_type") == "self_declared" for ev in evidence_events)

        # Parse timestamps for sequential time decay
        parsed_events = []
        for ev in evidence_events:
            dt = self._parse_timestamp(ev.get("timestamp"))
            parsed_events.append((dt, ev))

        # If timestamps exist, ensure chronological ordering
        if any(dt is not None for dt, _ in parsed_events):
            parsed_events.sort(key=lambda x: x[0] if x[0] is not None else datetime.min.replace(tzinfo=timezone.utc))

        last_dt = None
        for i, (dt, ev) in enumerate(parsed_events):
            # Apply time decay between consecutive events
            if dt is not None and last_dt is not None:
                delta_days = max(0.0, (dt - last_dt).total_seconds() / 86400.0)
                if delta_days > 0.0:
                    p_before_decay = p_l
                    p_l = self._apply_time_decay(p_l, baseline_prior, delta_days)
                    if abs(p_l - p_before_decay) >= 0.01:
                        trail.append(
                            f"Time decay ({round(delta_days, 1)} days elapsed): "
                            f"{round(p_before_decay, 3)} -> {round(p_l, 3)}"
                        )
            if dt is not None:
                last_dt = dt

            val = float(np.clip(ev.get("value", 0.0), 0.0, 1.0))
            source = ev.get("source_type", "unknown")
            # Weight by configured source reliability
            source_rel_weight = float(self.evidence_weights.get(source, ev.get("confidence", 0.5)))
            weight = float(np.clip(source_rel_weight, 0.1, 1.0))
            total_weight += weight

            # Difficulty weighting (1=easy, 2=medium, 3=hard, 4=expert)
            item_ref = ev.get("item_ref")
            raw_diff = ev.get("difficulty") or (self.exercise_diffs.get(item_ref, 2) if item_ref else 2)
            try:
                difficulty = max(1, min(4, int(raw_diff)))
            except (ValueError, TypeError):
                difficulty = 2

            # Difficulty-adjusted slip and guess
            diff_factor = difficulty - 2.0
            p_s_base = self.p_slip * (1.0 + 0.15 * diff_factor)
            p_g_base = self.p_guess * (1.0 - 0.20 * diff_factor)
            p_s = max(0.02, min(0.30, p_s_base * (1.0 - 0.2 * weight)))
            p_g = max(0.02, min(0.35, p_g_base * (1.0 - 0.2 * weight)))

            # Continuous Soft Evidence observation likelihood:
            # P(O | L=1) = val * (1 - p_s) + (1 - val) * p_s
            # P(O | L=0) = val * p_g + (1 - val) * (1 - p_g)
            p_obs_given_l1 = val * (1.0 - p_s) + (1.0 - val) * p_s
            p_obs_given_l0 = val * p_g + (1.0 - val) * (1.0 - p_g)

            numerator = p_l * p_obs_given_l1
            denominator = numerator + ((1.0 - p_l) * p_obs_given_l0)
            p_l_given_obs = numerator / max(denominator, 1e-6)

            # Transition update: P(L_t) = P(L|O) + (1 - P(L|O)) * P(T)
            diff_learning_multiplier = 0.85 + 0.10 * difficulty
            effective_transit = self.p_transit * weight * diff_learning_multiplier * (0.5 + 0.5 * val)
            p_l = p_l_given_obs + ((1.0 - p_l_given_obs) * effective_transit)
            p_l = float(np.clip(p_l, 0.01, 0.99))

            trail.append(
                f"Step {i+1}: {source.replace('_', ' ').title()} result ({round(val*100)}%, diff={difficulty}) "
                f"[weight: {round(weight, 2)}] -> updated mastery probability: {round(p_l, 3)}"
            )

        # Apply decay from the most recent event to current time (UTC)
        if last_dt is not None:
            now_dt = datetime.now(timezone.utc)
            delta_now_days = max(0.0, (now_dt - last_dt).total_seconds() / 86400.0)
            if delta_now_days > 1.0:
                p_before_recent_decay = p_l
                p_l = self._apply_time_decay(p_l, baseline_prior, delta_now_days)
                if abs(p_l - p_before_recent_decay) >= 0.01:
                    trail.append(
                        f"Retention decay ({round(delta_now_days, 1)} days to now): "
                        f"{round(p_before_recent_decay, 3)} -> {round(p_l, 3)}"
                    )

        # Multi-session corroboration factor: distinct sessions & sources
        distinct_dates = len(set(str(ev.get("timestamp"))[:10] for ev in evidence_events if ev.get("timestamp")))
        distinct_sources = len(set(ev.get("source_type") for ev in evidence_events if ev.get("source_type")))
        multi_session_boost = min(1.0, 0.4 + 0.3 * max(1, distinct_dates) + 0.15 * max(1, distinct_sources))
        confidence = float(np.clip((total_weight / (total_weight + 1.5)) * multi_session_boost, 0.1, 1.0))

        # Self-declared evidence CANNOT independently confer mastery
        mastered = bool(
            p_l >= self.mastery_threshold
            and len(evidence_events) >= self.min_items_required
            and not all_self_declared
        )

        return {
            "p_mastery": round(p_l, 3),
            "confidence": round(confidence, 2),
            "mastered": mastered,
            "evidence_count": len(evidence_events),
            "evidence_trail": trail
        }

bkt_estimator = BKTEstimator()
