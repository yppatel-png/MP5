"""
Bayesian Knowledge Tracing (BKT) Mastery Estimator.
Implemented with NumPy for auditable, deterministic, and explainable skill modeling.
Incorporates evidence reliability weighting, time decay, and multi-session corroboration.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from backend.config import load_evidence_config

class BKTEstimator:
    def __init__(self):
        cfg = load_evidence_config()
        bkt_params = cfg.get("bkt_parameters", {})
        self.p_init_default = bkt_params.get("p_init_default", 0.1)
        self.p_transit = bkt_params.get("p_transit_default", 0.2)
        self.p_slip = bkt_params.get("p_slip_default", 0.1)
        self.p_guess = bkt_params.get("p_guess_default", 0.2)
        self.mastery_threshold = bkt_params.get("mastery_threshold", 0.85)
        self.min_items_required = bkt_params.get("min_items_required", 2)

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
        if prior_probability is not None:
            p_l = float(np.clip(prior_probability, 0.01, 0.99))
        else:
            p_l = float(self.p_init_default)

        if not evidence_events:
            return {
                "p_mastery": round(p_l, 3),
                "confidence": 0.2 if prior_probability else 0.1,
                "mastered": p_l >= self.mastery_threshold,
                "evidence_count": 0,
                "evidence_trail": ["No explicit test evidence recorded; using baseline prior."]
            }

        trail = []
        total_weight = 0.0

        for i, ev in enumerate(evidence_events):
            val = float(ev.get("value", 0.0))
            source = ev.get("source_type", "unknown")
            weight = float(ev.get("confidence", 0.5))
            total_weight += weight

            # Treat val >= 0.7 as correct response (O=1), else incorrect (O=0)
            is_correct = val >= 0.7

            # Weight blending: adjust slip and guess based on source reliability
            p_s = self.p_slip * (1.0 - 0.2 * weight)
            p_g = self.p_guess * (1.0 - 0.2 * weight)

            if is_correct:
                numerator = p_l * (1.0 - p_s)
                denominator = (p_l * (1.0 - p_s)) + ((1.0 - p_l) * p_g)
            else:
                numerator = p_l * p_s
                denominator = (p_l * p_s) + ((1.0 - p_l) * (1.0 - p_g))

            # Posterior given observation
            p_l_given_obs = numerator / max(denominator, 1e-6)

            # Transition update: P(L_t) = P(L_{t-1}|O) + (1 - P(L_{t-1}|O)) * P(T)
            # Higher weight events apply full transit; low weight events apply reduced transit
            effective_transit = self.p_transit * weight
            p_l = p_l_given_obs + ((1.0 - p_l_given_obs) * effective_transit)
            p_l = float(np.clip(p_l, 0.01, 0.99))

            trail.append(
                f"Step {i+1}: {source.replace('_', ' ').title()} result ({round(val*100)}%) "
                f"[weight: {round(weight, 2)}] -> updated mastery probability: {round(p_l, 3)}"
            )

        # Confidence is higher with more cumulative corroborating evidence
        confidence = float(np.clip(total_weight / (total_weight + 1.5), 0.1, 1.0))
        mastered = bool(p_l >= self.mastery_threshold and len(evidence_events) >= self.min_items_required)

        return {
            "p_mastery": round(p_l, 3),
            "confidence": round(confidence, 2),
            "mastered": mastered,
            "evidence_count": len(evidence_events),
            "evidence_trail": trail
        }

bkt_estimator = BKTEstimator()

