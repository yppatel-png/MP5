"""
Fixed Interests & Skill Mapping (§3 UX, Appendix A).
Defines the canonical list of 8 student interests and maps each to skills in skills.json.
"""

from typing import List, Dict

FIXED_INTERESTS: List[str] = [
    "AI/ML",
    "Systems",
    "Web and App Dev",
    "Data and Databases",
    "Algorithms and Theory",
    "Security",
    "Research",
    "Product and Business",
]

INTEREST_TO_SKILLS_MAP: Dict[str, List[str]] = {
    "AI/ML": [
        "artificial_intelligence",
        "llm_software",
        "probability_statistics",
    ],
    "Systems": [
        "operating_systems",
        "computer_architecture",
        "compiler_design",
        "computer_networks",
    ],
    "Web and App Dev": [
        "software_engineering",
        "software_tools",
        "llm_software",
        "database_systems",
    ],
    "Data and Databases": [
        "database_systems",
        "data_structures",
        "probability_statistics",
    ],
    "Algorithms and Theory": [
        "algorithms",
        "data_structures",
        "discrete_mathematics",
        "theory_computation",
    ],
    "Security": [
        "computer_networks",
        "operating_systems",
        "formal_verification",
    ],
    "Research": [
        "research_methods",
        "theory_computation",
        "formal_verification",
        "algorithms",
    ],
    "Product and Business": [
        "finance",
        "macroeconomics",
        "microeconomics",
        "communication",
        "international_trade",
    ],
}

def get_skills_for_interests(interests: List[str]) -> List[str]:
    """Returns deduplicated skill IDs matching the student's declared interests."""
    skills = []
    for interest in interests:
        for skill_id in INTEREST_TO_SKILLS_MAP.get(interest, []):
            if skill_id not in skills:
                skills.append(skill_id)
    return skills
