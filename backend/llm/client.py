"""
LiteLLM Resilient Client Wrapper.
Encapsulates all LLM and embedding calls with:
- Configurable environment settings (LLM_MODEL, LLM_API_KEY, LLM_API_BASE)
- Strict timeouts and exponential backoff with jitter
- Cache-first lookup
- Deterministic fallback hooks when offline or on failure
- Token usage and latency telemetry logging
"""

import time
import json
import logging
import random
import os
from typing import Dict, Any, List, Optional

# Enforce offline local cost map to avoid outbound network socket attempts
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

from backend.config import settings
from backend.llm.cache import llm_cache
from backend.llm import fallbacks

logger = logging.getLogger("learning_buddy.llm")

try:
    import litellm
    litellm.telemetry = False
    litellm.drop_params = True
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logger.warning("litellm package not installed locally; will use deterministic fallbacks until containerized.")

class LLMCallLog:
    """In-memory telemetry log for admin dashboard and evaluation harness."""
    def __init__(self, max_records: int = 500):
        self.logs: List[Dict[str, Any]] = []
        self.max_records = max_records

    def add(self, record: Dict[str, Any]) -> None:
        self.logs.append(record)
        if len(self.logs) > self.max_records:
            self.logs.pop(0)

    def get_summary(self) -> Dict[str, Any]:
        if not self.logs:
            return {
                "total_calls": 0,
                "cached_calls": 0,
                "fallback_calls": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0
            }
        latencies = sorted([log["latency_ms"] for log in self.logs])
        p50 = latencies[len(latencies) // 2]
        p95_idx = int(len(latencies) * 0.95)
        p95 = latencies[min(p95_idx, len(latencies) - 1)]

        return {
            "total_calls": len(self.logs),
            "cached_calls": sum(1 for l in self.logs if l.get("cached")),
            "fallback_calls": sum(1 for l in self.logs if l.get("fallback_used")),
            "total_prompt_tokens": sum(l.get("prompt_tokens", 0) for l in self.logs),
            "total_completion_tokens": sum(l.get("completion_tokens", 0) for l in self.logs),
            "p50_latency_ms": round(p50, 2),
            "p95_latency_ms": round(p95, 2)
        }

call_logger = LLMCallLog()

class LiteLLMClient:
    def __init__(self):
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.api_base = settings.LLM_API_BASE
        self.offline = settings.OFFLINE_MODE or not self.api_key or not self.model or not LITELLM_AVAILABLE
        
    def is_live(self) -> bool:
        """Returns True if the client is armed with an active model key."""
        return not self.offline and LITELLM_AVAILABLE and bool(self.api_key) and bool(self.model)

    def generate(
        self,
        call_type: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 500,
        timeout_seconds: float = 8.0,
        max_retries: int = 2,
        known_valid_courses: Optional[List[str]] = None,
        fallback_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a robust completion call.
        Checks cache -> tries litellm -> retries on error -> fails over to deterministic fallback.
        """
        start_time = time.time()
        cache_key = llm_cache.compute_key(self.model or "offline", messages, temperature=temperature, max_tokens=max_tokens)
        
        # 1. Cache Check
        cached_res = llm_cache.get(cache_key)
        if cached_res:
            latency = (time.time() - start_time) * 1000
            call_logger.add({
                "call_type": call_type,
                "model": self.model,
                "cached": True,
                "fallback_used": cached_res.get("fallback_used", False),
                "latency_ms": latency,
                "prompt_tokens": cached_res.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": cached_res.get("usage", {}).get("completion_tokens", 0),
                "timestamp": time.time()
            })
            return cached_res

        # 2. Check for Forced Offline / Missing Keys
        if not self.is_live():
            fallback_content = self._invoke_fallback(call_type, messages, fallback_data)
            latency = (time.time() - start_time) * 1000
            res = {
                "content": fallback_content,
                "fallback_used": True,
                "model": "deterministic_fallback",
                "usage": {"prompt_tokens": 0, "completion_tokens": len(fallback_content.split())}
            }
            # Cache the fallback result
            llm_cache.set(cache_key, res)
            
            call_logger.add({
                "call_type": call_type,
                "model": "deterministic_fallback",
                "cached": False,
                "fallback_used": True,
                "latency_ms": latency,
                "prompt_tokens": 0,
                "completion_tokens": res["usage"]["completion_tokens"],
                "timestamp": time.time()
            })
            return res

        # 3. Execution via LiteLLM with Exponential Backoff
        attempts = 0
        last_error = None
        while attempts <= max_retries:
            try:
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": timeout_seconds,
                    "api_key": self.api_key
                }
                if self.api_base:
                    kwargs["api_base"] = self.api_base

                response = litellm.completion(**kwargs)
                content = response.choices[0].message.content or ""
                
                # Verify grounding if valid courses provided
                if known_valid_courses:
                    content = self._verify_course_codes(content, known_valid_courses)

                latency = (time.time() - start_time) * 1000
                usage = {
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(response.usage, "completion_tokens", 0)
                }
                result = {
                    "content": content,
                    "fallback_used": False,
                    "model": self.model,
                    "usage": usage
                }
                
                # Cache response
                llm_cache.set(cache_key, result)
                
                call_logger.add({
                    "call_type": call_type,
                    "model": self.model,
                    "cached": False,
                    "fallback_used": False,
                    "latency_ms": latency,
                    "prompt_tokens": usage["prompt_tokens"],
                    "completion_tokens": usage["completion_tokens"],
                    "timestamp": time.time()
                })
                return result

            except Exception as e:
                attempts += 1
                last_error = e
                logger.warning(f"LiteLLM attempt {attempts} failed: {e}. Backing off...")
                if attempts <= max_retries:
                    sleep_time = (0.5 * (2 ** (attempts - 1))) + random.uniform(0.1, 0.4)
                    time.sleep(sleep_time)

        # 4. Graceful Fallback if all retries exhausted
        logger.error(f"All {max_retries + 1} LiteLLM attempts failed ({last_error}). Triggering deterministic fallback.")
        fallback_content = self._invoke_fallback(call_type, messages, fallback_data)
        latency = (time.time() - start_time) * 1000
        result = {
            "content": fallback_content,
            "fallback_used": True,
            "error_fallback": str(last_error),
            "model": "deterministic_fallback",
            "usage": {"prompt_tokens": 0, "completion_tokens": len(fallback_content.split())}
        }
        llm_cache.set(cache_key, result)
        
        call_logger.add({
            "call_type": call_type,
            "model": "deterministic_fallback",
            "cached": False,
            "fallback_used": True,
            "latency_ms": latency,
            "prompt_tokens": 0,
            "completion_tokens": result["usage"]["completion_tokens"],
            "timestamp": time.time()
        })
        return result

    def _invoke_fallback(self, call_type: str, messages: List[Dict[str, str]], fallback_data: Optional[Dict[str, Any]]) -> str:
        data = fallback_data or {}
        last_msg = messages[-1]["content"] if messages else ""
        
        if call_type == "GOAL_INTAKE":
            return json.dumps(fallbacks.fallback_goal_intake(last_msg), indent=2)
        elif call_type == "EXPLAIN_PLAN":
            plan_items = data.get("plan_items", [])
            student_name = data.get("student_name", "Student")
            return fallbacks.fallback_explain_plan(plan_items, student_name)
        elif call_type == "EXPLAIN_CHANGE":
            diff_summary = data.get("diff_summary", {})
            return fallbacks.fallback_explain_change(diff_summary)
        elif call_type == "BUDDY_CHAT":
            return fallbacks.fallback_chat_response(last_msg, data)
        else:
            return "Request processed successfully via deterministic academic advisor."

    def _verify_course_codes(self, content: str, valid_courses: List[str]) -> str:
        """
        Scans for course patterns (e.g. 3 uppercase letters followed by 3 digits)
        and verifies they belong to the institute catalogue.
        """
        import re
        course_pattern = re.compile(r'\b[A-Z]{2,4}\s?[0-9]{3}\b')
        found = course_pattern.findall(content)
        for c in found:
            norm = c.replace(" ", "")
            if norm not in valid_courses and c not in valid_courses:
                content = content.replace(c, f"{c} (Note: Unverified course code)")
        return content

llm_client = LiteLLMClient()
