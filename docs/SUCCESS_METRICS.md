# Success Metrics & Pilot Key Performance Indicators (KPIs)
Quantitative benchmarks and measurement methodology for the Adobe Personalised Learning Buddy pilot at IIT Delhi.

---

## 1. Primary Success Metrics

| Metric ID | Indicator | Target KPI | Measurement Mechanism |
| :--- | :--- | :--- | :--- |
| **KPI-1** | **Time-to-First-Valid-Plan** | **$< 2.5$ seconds** | Wall-clock latency from onboarding submission to verified 9-rule valid schedule. |
| **KPI-2** | **Plan Validity & Feasibility** | **$100\%$ Valid** | Decoupled validator passing 9/9 rules across all generated schedules (zero cycle, parity, credit breaches). |
| **KPI-3** | **Plan Adherence Rate (4+ Weeks)** | **$\ge 75\%$** | Percentage of students continuing to log study sessions and complete weekly checklists over a 4-week window. |
| **KPI-4** | **Diagnostic Score Improvement** | **$+25\%$ Normalized Gain** | Delta between baseline diagnostic assessment score and post-practice checkpoint scores. |
| **KPI-5** | **Student Usefulness Rating** | **$\ge 4.4 / 5.0$ CSAT** | Post-recommendation feedback thumbs and Likert scale ("This plan made my semester clearer"). |
| **KPI-6** | **Zero Course Code Hallucination** | **$100\%$ Grounded** | Interceptor strips $100\%$ of invented course codes; every code verified against institute catalogue. |
| **KPI-7** | **Zero System Crashes** | **$0$ Unhandled Exceptions** | Deterministic template fallbacks trigger on any external LLM timeout, rate limit, or socket failure. |

---

## 2. Secondary Educational Impact Metrics

1. **Prerequisite Friction Reduction**:
   - Baseline: $78.2\%$ of surveyed students discovered missing prerequisites too late.
   - Target: $< 5\%$ of pilot students experience a prerequisite registration rejection.

2. **Workload Calibration Accuracy**:
   - Delta between student-budgeted self-study hours ($8.0$ hrs/wk) and estimated course study demand.
   - Target: $< 15\%$ variance between planned study hours and actual logged weekly hours.

3. **Adaptation Responsiveness**:
   - Percentage of performance or behavioral signals (quiz score $< 40\%$, hours $< 60\%$) resulting in an immediate transparent plan adjustment within 1 session.
   - Target: $100\%$ of triggers evaluated with actionable student notifications.

