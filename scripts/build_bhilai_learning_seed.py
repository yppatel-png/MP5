#!/usr/bin/env python3
"""Build the IIT Bhilai seed from verified PDF facts and team-authored learning records."""

import csv
import json
import random
import re
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT_DIR / "data" / "seed_bhilai"
SOURCE_PATH = ROOT_DIR / "data" / "raw" / "courses_of_study_extracted.json"
REVIEW_PATH = ROOT_DIR / "data" / "review_queue.csv"
TODAY = "2026-11-06"

SKILLS = [
    ("programming_fundamentals", "Programming fundamentals", "Computer Science", "Read and reason about imperative programs and basic data types."),
    ("software_tools", "Software tools and collaboration", "Computer Science", "Use command-line, versioning, testing, and development tools."),
    ("discrete_mathematics", "Discrete mathematics", "Mathematics", "Use sets, relations, logic, proof, counting, and graph concepts."),
    ("data_structures", "Data structures", "Computer Science", "Select and reason about linear and non-linear data structures."),
    ("algorithms", "Algorithm design and analysis", "Computer Science", "Analyze and design algorithms using established paradigms."),
    ("computer_architecture", "Computer architecture", "Computer Science", "Explain instruction execution, arithmetic units, memory, and I/O."),
    ("theory_computation", "Theory of computation", "Computer Science", "Reason about formal languages, automata, and computability."),
    ("operating_systems", "Operating systems", "Computer Science", "Explain processes, concurrency, memory, and persistence."),
    ("compiler_design", "Compiler design", "Computer Science", "Describe the phases and intermediate representations of compilation."),
    ("database_systems", "Database systems", "Computer Science", "Model, query, and normalize relational data."),
    ("artificial_intelligence", "Artificial intelligence", "Computer Science", "Apply search, representation, reasoning, and learning concepts."),
    ("computer_networks", "Computer networks", "Computer Science", "Explain network layers, protocols, and communication."),
    ("software_engineering", "Software engineering", "Computer Science", "Specify, construct, test, and review software systems."),
    ("llm_software", "LLM-assisted software development", "Computer Science", "Use constrained prompts, structured outputs, tools, and evaluation responsibly."),
    ("research_methods", "Research and project methods", "Computer Science", "Frame a problem, develop a solution, and communicate evidence."),
    ("probability_statistics", "Probability and statistics", "Mathematics", "Use probability and statistical reasoning to analyze uncertainty."),
    ("communication", "Communication", "Humanities", "Communicate an idea clearly for a defined audience."),
    ("finance", "Personal and institutional finance", "Humanities", "Interpret foundational finance concepts and terminology."),
    ("macroeconomics", "Macroeconomics", "Humanities", "Reason about aggregate economic activity and policy."),
    ("microeconomics", "Microeconomics", "Humanities", "Reason about individual choices, markets, and incentives."),
    ("international_trade", "International trade", "Humanities", "Explain trade flows and the role of trade policy."),
    ("indian_society", "Society and institutions", "Humanities", "Analyze social structures and institutions using course themes."),
    ("literary_analysis", "Literary analysis", "Humanities", "Interpret literary form, context, and narrative."),
    ("formal_verification", "Formal verification", "Computer Science", "Express and verify properties of systems using formal methods."),
]

# code, title, credits, L, T, P, semester, category, source page, prerequisite codes,
# syllabus topics as (topic, learning text, skill id)
COURSES = [
    ("CSL100", "Introduction to Programming", 4.5, 2, 1, 3, 1, "core", 83, [], [
        ("C programming", "The source syllabus covers programming using C and primitive data types.", "programming_fundamentals"),
        ("Control flow", "The source syllabus covers conditional statements, loops, and functions.", "programming_fundamentals"),
        ("Memory and data", "The source syllabus covers dynamic memory allocation, pointers, and complex data types.", "programming_fundamentals"),
        ("Program construction", "The source syllabus covers recursion, file handling, linked lists, sorting, and searching.", "programming_fundamentals"),
    ]),
    ("ECL101", "Basic Electronics Engineering", 4, 3, 0, 2, 2, "institute_core", 21, [], [
        ("Electronics foundations", "This team-authored learning unit introduces basic electronics; the PDF verifies the course title, credits, and semester, not this unit syllabus.", "computer_architecture"),
        ("Digital signals", "This team-authored unit introduces digital-signal concepts for computing students.", "computer_architecture"),
        ("Circuits and systems", "This team-authored unit introduces circuit terminology; it is not an official course syllabus.", "computer_architecture"),
    ]),
    ("MAL403", "Probability & Statistics", 4, 3, 1, 0, 3, "program_linked", 21, [], [
        ("Probability", "This team-authored learning unit introduces probability vocabulary; the PDF verifies the course title and credit, not this unit syllabus.", "probability_statistics"),
        ("Statistical reasoning", "This team-authored unit introduces statistical reasoning; the PDF verifies the course title and credit, not this unit syllabus.", "probability_statistics"),
        ("Uncertainty", "This team-authored unit uses probability to reason about uncertainty; it is not an official course syllabus.", "probability_statistics"),
    ]),
    ("CSL201", "Discrete Mathematics", 4, 3, 1, 0, 3, "core", 83, [], [
        ("Sets and relations", "The syllabus lists sets, relations, functions, equivalence, and partial orders.", "discrete_mathematics"),
        ("Logic and proof", "The syllabus lists propositional logic, predicates, proof techniques, and induction.", "discrete_mathematics"),
        ("Counting and recurrence", "The syllabus lists counting techniques, pigeonhole principle, and recurrence relations.", "discrete_mathematics"),
        ("Graph and number theory", "The syllabus lists graph theory, divisibility, Euclidean algorithm, and modular arithmetic.", "discrete_mathematics"),
    ]),
    ("CSL202", "Data Structures", 4, 2, 1, 2, 3, "core", 83, ["CSL100"], [
        ("Stacks and queues", "The syllabus covers stacks, queues, and lists as data structures.", "data_structures"),
        ("Trees and traversals", "The syllabus covers trees, tree traversals, heaps, and binary search trees.", "data_structures"),
        ("Graph traversal", "The syllabus names graph representations, depth-first search, and breadth-first search.", "data_structures"),
        ("Sorting and searching", "The syllabus includes sorting and searching techniques.", "algorithms"),
    ]),
    ("CSP203", "Software Tools & Technologies Lab", 3, 1, 0, 4, 3, "core", 83, ["CSL100"], [
        ("Linux commands", "The syllabus identifies Linux fundamentals and Linux commands.", "software_tools"),
        ("Development environment", "This team-authored lab unit applies command-line tools to a small C project.", "software_tools"),
        ("Versioned changes", "This team-authored lab unit practices recording and reviewing source changes.", "software_tools"),
    ]),
    ("CSL251", "Computer Organization & Architecture", 4, 3, 0, 2, 4, "core", 83, ["CSL100", "ECL101"], [
        ("Digital building blocks", "The syllabus covers digital building blocks, truth tables, and number representation.", "computer_architecture"),
        ("Instruction execution", "The syllabus covers machine instructions and assembly-language programming.", "computer_architecture"),
        ("Memory hierarchy", "The syllabus covers ROM, RAM, cache memories, virtual memory, and secondary storage.", "computer_architecture"),
        ("Input and pipelining", "The syllabus covers I/O, interrupts, DMA, instruction pipelines, and hazards.", "computer_architecture"),
    ]),
    ("CSL252", "Design and Analysis of Algorithms", 4, 3, 1, 0, 4, "core", 84, ["CSL100", "CSL201", "CSL202"], [
        ("Algorithm analysis", "The syllabus covers worst- and average-case analysis, recurrences, and asymptotes.", "algorithms"),
        ("Divide and conquer", "The syllabus lists randomized techniques and divide-and-conquer algorithms.", "algorithms"),
        ("Greedy and dynamic programming", "The syllabus covers dynamic programming and greedy algorithms.", "algorithms"),
        ("Graph algorithms and hardness", "The syllabus covers graph algorithms, shortest paths, NP-completeness, and approximation.", "algorithms"),
    ]),
    ("CSL253", "Theory of Computation", 4, 3, 1, 0, 4, "core", 84, ["CSL201", "CSL202"], [
        ("Finite-state machines", "The syllabus covers alphabets, languages, and finite-state machines.", "theory_computation"),
        ("Context-free languages", "The syllabus covers context-free grammars, parse trees, and pushdown automata.", "theory_computation"),
        ("Turing machines", "The syllabus covers Turing machines and their variants.", "theory_computation"),
        ("Undecidability and complexity", "The syllabus covers undecidability, space and time complexity, and NP-completeness.", "theory_computation"),
    ]),
    ("CSL301", "Operating Systems", 4, 3, 0, 2, 5, "core", 84, ["CSL202", "CSL251"], [
        ("Operating-system foundations", "The syllabus introduces operating systems, virtualization, concurrency, and persistence.", "operating_systems"),
        ("Processes and scheduling", "The syllabus covers processes, the process API, process control blocks, and CPU scheduling.", "operating_systems"),
        ("Memory virtualization", "The syllabus covers virtual memory and memory management.", "operating_systems"),
    ]),
    ("CSL302", "Compiler Design", 4, 3, 0, 2, 5, "core", 84, ["CSL251", "CSL253"], [
        ("Compiler phases", "The syllabus covers the analysis-synthesis model and phases of compiler construction.", "compiler_design"),
        ("Lexing and parsing", "The syllabus names lexical analysis and syntax analysis.", "compiler_design"),
        ("Translation and checking", "The syllabus covers syntax-directed translation and type checking.", "compiler_design"),
        ("Code generation", "The syllabus covers intermediate code, optimization, and machine code generation.", "compiler_design"),
    ]),
    ("CSL303", "Database Management Systems", 4, 3, 0, 2, 5, "core", 85, [], [
        ("Data models", "The syllabus covers data models, schemas, instances, and database languages.", "database_systems"),
        ("Relational algebra", "The syllabus names SELECT, PROJECT, set operations, JOIN, and DIVISION.", "database_systems"),
        ("Entity-relationship design", "The syllabus covers entity-relationship models, keys, relationships, and mapping.", "database_systems"),
        ("Normalization and SQL", "The syllabus covers functional dependencies, normal forms, and SQL programming.", "database_systems"),
    ]),
    ("CSL304", "Artificial Intelligence", 4, 3, 0, 2, 5, "core", 85, [], [
        ("Search and problem solving", "The syllabus covers state spaces, graph search, game playing, and constraint satisfaction.", "artificial_intelligence"),
        ("Automated reasoning", "The syllabus covers propositional and first-order logic, inference, and knowledge-based systems.", "artificial_intelligence"),
        ("Planning", "The syllabus covers state-space planning, plan-space planning, and planning algorithms.", "artificial_intelligence"),
        ("Uncertainty and learning", "The syllabus covers probabilistic reasoning, belief networks, fuzzy logic, and reinforcement learning.", "artificial_intelligence"),
    ]),
    ("CSL351", "Computer Networks", 4, 3, 0, 2, 6, "core", 85, [], [
        ("Network architecture", "The source syllabus covers network architecture and communication protocols.", "computer_networks"),
        ("Communication layers", "This team-authored unit explains how layered protocols divide communication tasks.", "computer_networks"),
        ("Network reliability", "This team-authored unit introduces fault handling and reliable data transfer.", "computer_networks"),
    ]),
    ("CSP352", "AI-Augmented Software Development", 3, 1, 0, 4, 6, "core", 86, ["IC100"], [
        ("LLMs in software work", "The syllabus covers coding assistants, testing, debugging, documentation, and review.", "llm_software"),
        ("Structured prompts", "The syllabus covers task specifications, constraints, acceptance criteria, and structured prompts.", "llm_software"),
        ("Validated integration", "The syllabus covers APIs, structured outputs, schema validation, and error handling.", "llm_software"),
        ("Bounded agents", "The syllabus covers tool permissions, bounded execution, evaluation, and human approval.", "llm_software"),
    ]),
    ("CSQ401", "BTech Project-I", 3, 0, 0, 6, 7, "core", 87, [], [
        ("Research question", "The course description calls for research and development projects on practical and theoretical problems.", "research_methods"),
        ("Project goals", "The description expects students to work toward goals set with a project supervisor.", "research_methods"),
        ("Presentations and reports", "The description states that evaluation uses regular presentations and written reports.", "communication"),
    ]),
    ("LAL100", "Introduction to Communication Skills", 2, 1, 1, 0, 3, "liberal_arts", 136, [], [
        ("Audience and purpose", "This team-authored communication unit develops audience-aware writing; the PDF verifies the course title and credit, not this unit syllabus.", "communication"),
        ("Clear explanations", "This team-authored unit practices concise spoken and written explanations.", "communication"),
        ("Evidence and structure", "This team-authored unit practices organizing claims and supporting evidence.", "communication"),
    ]),
    ("LAL101", "Introduction to Finance", 1, 1, 0, 0, 4, "liberal_arts", 136, [], [
        ("Financial vocabulary", "This team-authored finance unit introduces common financial terms; the PDF verifies the course title and credit, not this unit syllabus.", "finance"),
        ("Time and value", "This team-authored unit introduces time value as a finance concept.", "finance"),
        ("Risk and return", "This team-authored unit introduces the relationship between risk and return.", "finance"),
    ]),
    ("CSL504", "Graph Theory and Applications", 3, 3, 0, 0, None, "catalogue_elective", 88, [], [
        ("Graph representations", "The syllabus covers graphs, digraphs, representations, isomorphism, and graphic sequences.", "discrete_mathematics"),
        ("Matchings and connectivity", "The syllabus covers matchings, covers, Hall's theorem, connectivity, and Menger's theorem.", "discrete_mathematics"),
        ("Coloring and planar graphs", "The syllabus covers graph coloring, Eulerian and Hamiltonian graphs, and planar graphs.", "discrete_mathematics"),
    ]),
    ("CSL505", "Cryptography", 3, 3, 0, 0, None, "catalogue_elective", 88, [], [
        ("Cryptographic notions", "The syllabus begins with formal notions and a mathematics recap.", "theory_computation"),
        ("Historical ciphers", "The syllabus includes historical ciphers as an introductory topic.", "theory_computation"),
        ("Security reasoning", "This team-authored unit practices distinguishing a security claim from an implementation detail.", "theory_computation"),
    ]),
    ("CSL510", "Approximation Algorithms", 3, 3, 0, 0, None, "catalogue_elective", 88, ["CSL252"], [
        ("Approximation algorithms", "The syllabus covers approximation algorithms and approximation hardness.", "algorithms"),
        ("Primal-dual method", "The syllabus lists the primal-dual method.", "algorithms"),
        ("Metric rounding", "The syllabus covers metric rounding of linear-program relaxations.", "algorithms"),
    ]),
    ("CSL511", "Introduction to Formal Verification and its Applications", 3, 3, 0, 0, None, "catalogue_elective", 89, [], [
        ("Hoare logic", "The syllabus covers axioms and rules of Floyd-Hoare logic.", "formal_verification"),
        ("Decision diagrams", "The syllabus covers binary decision diagrams and reduced ordered binary decision diagrams.", "formal_verification"),
        ("Temporal logic", "The syllabus covers linear- and branching-time temporal logic and CTL model checking.", "formal_verification"),
    ]),
    ("CSL512", "Parallel Algorithms", 3, 3, 0, 0, None, "catalogue_elective", 89, ["CSL252"], [
        ("Parallel models", "The syllabus covers PRAM variants, interconnection networks, and synchronous and asynchronous models.", "algorithms"),
        ("Parallel techniques", "The syllabus covers matrix multiplication, sorting, searching, partitioning, and pipelining.", "algorithms"),
        ("Parallel graph algorithms", "The syllabus covers connected components, graph coloring, minimum spanning trees, and shortest paths.", "algorithms"),
    ]),
    ("CSL515", "Randomized Algorithms", 3, 3, 0, 0, None, "catalogue_elective", 89, ["CSL252"], [
        ("Randomized methods", "The syllabus identifies randomized algorithms and their analysis.", "algorithms"),
        ("Probability in algorithms", "This team-authored module uses probability to reason about randomized algorithm outcomes.", "probability_statistics"),
        ("Algorithm guarantees", "This team-authored module compares deterministic and probabilistic guarantees.", "algorithms"),
    ]),
    ("CSL518", "Fundamentals of Distributed Algorithms", 3, 3, 0, 0, None, "catalogue_elective", 90, ["CSL252"], [
        ("Distributed computing models", "The syllabus covers distributed computing models and challenges.", "computer_networks"),
        ("Broadcast and trees", "The syllabus covers broadcast, convergecast, and breadth-first-search tree construction.", "algorithms"),
        ("Leader election", "The syllabus covers leader election algorithms and lower bounds.", "algorithms"),
    ]),
    ("CSL559", "Computer Systems Design", 4, 3, 0, 2, None, "catalogue_elective", 90, [], [
        ("System goals", "The syllabus covers setting goals for a system and principles of good design.", "software_engineering"),
        ("Quantitative system models", "The syllabus covers queuing systems, fundamental laws, and asymptotic bounds.", "software_engineering"),
        ("Resource management", "The syllabus covers scheduling, load balancing, and TCP throughput models.", "computer_networks"),
    ]),
    ("LAL200", "Macroeconomics", 2, 2, 0, 0, None, "open_elective", 137, [], [
        ("Aggregate economic activity", "This team-authored introduction develops aggregate-economy vocabulary; the PDF verifies the course title and credit, not this unit syllabus.", "macroeconomics"),
        ("Economic indicators", "This team-authored unit practices reading common aggregate indicators.", "macroeconomics"),
        ("Policy questions", "This team-authored unit frames questions about economy-wide policy.", "macroeconomics"),
    ]),
    ("LAL201", "Microeconomics", 1, 1, 0, 0, None, "open_elective", 137, [], [
        ("Choice and incentives", "This team-authored microeconomics unit introduces individual choice and incentives; the PDF verifies the course title and credit, not this unit syllabus.", "microeconomics"),
        ("Markets", "This team-authored unit introduces supply, demand, and market interaction.", "microeconomics"),
        ("Trade-offs", "This team-authored unit practices identifying trade-offs in a simple choice.", "microeconomics"),
    ]),
    ("LAL202", "International Trade", 2, 2, 0, 0, None, "open_elective", 137, [], [
        ("Trade flows", "This team-authored unit introduces the idea of cross-border trade flows; the PDF verifies the course title and credit, not this unit syllabus.", "international_trade"),
        ("Trade restrictions", "This team-authored unit introduces tariff and non-tariff restrictions.", "international_trade"),
        ("Trade policy", "This team-authored unit frames the role of international trade policy.", "international_trade"),
    ]),
    ("LAL221", "Indian Writing in English", 2, 2, 0, 0, None, "liberal_arts_elective", 138, [], [
        ("Reading in context", "This team-authored unit practices interpreting a text in its social and historical context; the PDF verifies course title and credit.", "literary_analysis"),
        ("Voice and perspective", "This team-authored unit practices identifying narrative voice and perspective.", "literary_analysis"),
        ("Evidence-based interpretation", "This team-authored unit practices supporting an interpretation with textual evidence.", "literary_analysis"),
    ]),
    ("LAL222", "City in Literature", 2, 2, 0, 0, None, "liberal_arts_elective", 138, [], [
        ("Literary representations of cities", "This team-authored unit explores how a text represents urban settings; the PDF verifies course title and credit.", "literary_analysis"),
        ("Setting and character", "This team-authored unit practices tracing how setting shapes a character's choices.", "literary_analysis"),
        ("Textual evidence", "This team-authored unit practices citing textual details in an interpretation.", "literary_analysis"),
    ]),
    ("LAL223", "Introduction to Partition Literature", 2, 2, 0, 0, None, "liberal_arts_elective", 139, [], [
        ("Literature and historical context", "This team-authored unit practices reading literature in historical context; the PDF verifies course title and credit.", "literary_analysis"),
        ("Narrative perspective", "This team-authored unit practices comparing narrative perspectives.", "literary_analysis"),
        ("Memory and representation", "This team-authored unit examines how texts represent memory and experience.", "literary_analysis"),
    ]),
    ("LAL224", "Introduction to Postcolonial Literature", 2, 2, 0, 0, None, "liberal_arts_elective", 139, [], [
        ("Literature and power", "This team-authored unit practices examining how literature represents power; the PDF verifies course title and credit.", "literary_analysis"),
        ("Voice and identity", "This team-authored unit practices identifying voice and identity in a text.", "literary_analysis"),
        ("Close reading", "This team-authored unit practices close reading with evidence.", "literary_analysis"),
    ]),
    ("LAL225", "Self and Society in Modern India", 2, 2, 0, 0, None, "liberal_arts_elective", 139, [], [
        ("Self and society", "This team-authored unit frames relationships between individual experience and social context; the PDF verifies course title and credit.", "indian_society"),
        ("Social institutions", "This team-authored unit practices identifying how institutions shape social experience.", "indian_society"),
        ("Evidence and interpretation", "This team-authored unit practices supporting a social analysis with evidence.", "indian_society"),
    ]),
]

RESOURCE_CATALOG = [
    ("mit_6006", "Introduction to Algorithms", "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", ["data_structures", "algorithms"], "2026-11-06"),
    ("mit_6042", "Mathematics for Computer Science", "https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-spring-2015/", ["discrete_mathematics", "probability_statistics"], "2026-11-06"),
    ("mit_6004", "Computation Structures", "https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/", ["computer_architecture"], "2026-11-06"),
    ("mit_6034", "Artificial Intelligence", "https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/", ["artificial_intelligence"], "2026-11-06"),
    ("mit_6830", "Database Systems", "https://ocw.mit.edu/courses/6-830-database-systems-fall-2010/", ["database_systems"], "2026-11-06"),
    ("mit_61810", "Operating System Engineering", "https://ocw.mit.edu/courses/6-1810-operating-system-engineering-fall-2023/", ["operating_systems"], "2026-11-06"),
]


def write_json(name: str, data: object) -> None:
    (SEED_DIR / name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_courses(source_pages: dict[int, str]) -> tuple[list[dict], list[dict]]:
    courses = []
    review = []
    for (code, title, credits, lecture, tutorial, practical, semester, category,
         source_page, prerequisites, topics) in COURSES:
        normalized_source = " ".join(source_pages[source_page].split()).casefold()
        if code.casefold() not in normalized_source or title.casefold() not in normalized_source:
            raise ValueError(f"{code} title was not found on cited PDF page {source_page}.")
        description_credit = re.search(
            rf"{re.escape(str(credits).removesuffix('.0'))}\s+Credits?\s*\(\s*{lecture}\s*-\s*{tutorial}\s*-\s*{practical}\s*\)",
            normalized_source,
            flags=re.IGNORECASE,
        )
        table_credit = re.search(
            rf"{lecture}\s*-\s*{tutorial}\s*-\s*{practical}\s*-\s*{re.escape(str(credits).removesuffix('.0'))}",
            normalized_source,
            flags=re.IGNORECASE,
        )
        if not (description_credit or table_credit):
            raise ValueError(f"{code} L-T-P-C did not match cited PDF page {source_page}.")
        courses.append({
            "code": code,
            "title": title,
            "department": "Liberal Arts" if category.startswith("liberal_arts") or category in {"open_elective"} else ("Mathematics" if code == "MAL403" else "Computer Science and Engineering"),
            "credits": credits,
            "ltpc": [lecture, tutorial, practical, credits],
            "semester_offered": f"semester_{semester}" if semester else "catalogue_unscheduled",
            "course_type": category,
            "mode": "offline",
            "level": "undergraduate",
            "workload_hours_per_week": None,
            "syllabus": (
                "; ".join(topic for topic, _, _ in topics)
                if any("source syllabus" in text for _, text, _ in topics)
                else None
            ),
            "learning_objectives": None,
            "source": f"IIT Bhilai Courses of Study, October 2026, PDF p. {source_page}",
            "source_page": source_page,
            "provenance": "verified",
            "last_verified": TODAY,
            "programme_role": "scheduled_BTech_CSE" if semester else "catalogue_only_selection_unverified",
        })
        for prereq in prerequisites:
            if prereq not in {row[0] for row in COURSES}:
                review.append({
                    "item_type": "prerequisite_reference",
                    "item_id": f"{code}:{prereq}",
                    "issue": f"Official prerequisite {prereq} is outside this compact catalogue or unresolved; retain as an explicit constraint.",
                    "source_page": source_page,
                })
    return courses, review


def build_seed() -> None:
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    if source["source_page_count"] != 208 or len(source["pages"]) != 208:
        raise ValueError("Expected complete 208-page extracted source.")
    source_pages = {row["source_page"]: row["text"] for row in source["pages"]}
    courses, review = build_courses(source_pages)
    if not 20 <= len(courses) <= 40:
        raise ValueError(f"Expected 20-40 courses, got {len(courses)}.")

    skills = [
        {
            "skill_id": skill_id,
            "name": name,
            "domain": domain,
            "description": description,
            "parent_skill_id": None,
            "source": "Team-authored skill taxonomy mapped to cited course syllabus topics",
            "source_page": None,
            "provenance": "team_authored",
            "last_verified": TODAY,
        }
        for skill_id, name, domain, description in SKILLS
    ]
    skill_domains = {skill_id: domain for skill_id, _, domain, _ in SKILLS}
    modules = []
    course_skills = {}
    for (code, _title, _credits, _l, _t, _p, _sem, _category,
         source_page, _prerequisites, topics) in COURSES:
        syllabus_page = 84 if code == "CSL251" else source_page
        for topic_index, (topic, text, skill_id) in enumerate(topics, start=1):
            module_id = f"mod_{code.lower()}_{topic_index}"
            modules.append({
                "module_id": module_id,
                "course_code": code,
                "order": topic_index,
                "title": topic,
                "text": text,
                "est_minutes": 15,
                "skill_ids": [skill_id],
                "source": f"Derived from IIT Bhilai Courses of Study, PDF p. {syllabus_page}" if "source syllabus" in text else f"Team-authored learning unit; course context verified on IIT Bhilai Courses of Study, PDF p. {source_page}",
                "source_page": syllabus_page,
                "provenance": "derived" if "source syllabus" in text else "team_authored",
            })
            mapping = course_skills.setdefault((code, skill_id), {
                "course_code": code,
                "skill_id": skill_id,
                "depth": "intro" if topic_index == 1 else "intermediate",
                "weight": 0.75,
                "confidence": 0.75,
                "provenance": "derived",
                "source": f"Derived from syllabus page {source_page}",
                "source_page": source_page,
            })
            if skill_domains[skill_id] not in {"Computer Science", "Mathematics", "Humanities"}:
                raise ValueError(f"Unexpected skill domain in mapping: {skill_id}")

    topic_terms = [row["title"] for row in modules]
    exercises = []
    for index, module in enumerate(modules):
        forbidden = module["title"].casefold()
        distractors = []
        for offset in range(1, len(topic_terms)):
            candidate = topic_terms[(index + offset) % len(topic_terms)]
            if candidate.casefold() != forbidden and candidate.casefold() not in module["text"].casefold():
                distractors.append(candidate)
            if len(distractors) == 3:
                break
        if len(distractors) != 3:
            raise ValueError(f"Could not build three distinct distractors for {module['module_id']}.")
        options = [module["title"], *distractors]
        random.Random(module["module_id"]).shuffle(options)
        exercises.append({
            "exercise_id": f"ex_{module['module_id']}",
            "skill_id": module["skill_ids"][0],
            "module_id": module["module_id"],
            "type": "mcq",
            "difficulty": 1 if module["order"] == 1 else 2,
            "prompt": "Which topic is explicitly named in the learning unit above?",
            "answer_key": {
                "options": options,
                "correct": module["title"],
                "explanation": f"The unit explicitly identifies {module['title']}.",
            },
            "source": f"Original team-authored question grounded in {module['module_id']}",
            "source_page": module["source_page"],
            "provenance": "team_authored",
        })

    by_id = {row["skill_id"]: row for row in skills}
    for resource_id, title, url, skill_ids, verified in RESOURCE_CATALOG:
        for skill_id in skill_ids:
            if skill_id not in by_id:
                raise ValueError(f"Unknown resource skill: {skill_id}")
    resources = [
        {
            "resource_id": resource_id,
            "title": title,
            "provider": "MIT OpenCourseWare",
            "url": url,
            "license": "CC BY-NC-SA 4.0 (course page structured metadata)",
            "license_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
            "license_verified": True,
            "format": "Open course materials",
            "difficulty": "intermediate",
            "est_minutes": 60,
            "credit_eligible": False,
            "skill_ids": skill_ids,
            "source": "MIT OpenCourseWare official course page",
            "provenance": "team_authored",
            "date_verified": verified,
            "last_verified": verified,
        }
        for resource_id, title, url, skill_ids, verified in RESOURCE_CATALOG
    ]

    goals = [
        ("goal_software", "Software Engineering", "Software engineer", ["programming_fundamentals", "data_structures", "algorithms", "database_systems", "software_engineering", "software_tools"]),
        ("goal_higher_studies", "Higher Studies", "Computing researcher", ["discrete_mathematics", "algorithms", "probability_statistics", "research_methods", "communication"]),
        ("goal_upsc", "UPSC Preparation", "Civil services aspirant", ["communication", "macroeconomics", "microeconomics", "international_trade", "indian_society", "literary_analysis"]),
        ("goal_startup", "Startup", "Technology founder", ["programming_fundamentals", "software_engineering", "database_systems", "finance", "communication"]),
    ]
    goal_templates = [
        {
            "goal_id": goal_id,
            "name": name,
            "target_role": role,
            "typical_duration_semesters": 8,
            "required_skills": [
                {"skill_id": skill_id, "target_level": 0.7, "critical": index < 2}
                for index, skill_id in enumerate(required)
            ],
            "milestones": [],
            "source": "Team-authored development goal; not an IIT Bhilai academic requirement",
            "provenance": "team_authored",
        }
        for goal_id, name, role, required in goals
    ]

    codes = {row["code"] for row in courses}
    prerequisites = []
    for (code, _title, _credits, _l, _t, _p, _sem, _category,
         source_page, required, _topics) in COURSES:
        for prereq in required:
            prerequisites.append({
                "course_code": code,
                "requires_code": prereq,
                "type": "hard",
                "source": f"IIT Bhilai Courses of Study, PDF p. {source_page}",
                "source_page": source_page,
                "provenance": "verified",
            })
            if prereq not in codes:
                review.append({
                    "item_type": "prerequisite_course",
                    "item_id": prereq,
                    "issue": "Prerequisite appears in an official CSE description but is not in this course bundle; student must report it as completed before the dependent course is recommended.",
                    "source_page": source_page,
                })

    assumptions = [
        ("rule_sem_min_credits", "Minimum recommended semester credits", "credit_min", {"min_credits": 12.0}, "Demo planning floor; no semester minimum was found in the supplied PDF. Pending ordinance."),
        ("rule_sem_max_credits", "Standard semester credit cap", "credit_cap_max", {"max_credits": 24.0}, "Demo planning cap; no semester maximum was found in the supplied PDF. Pending ordinance."),
        ("rule_credit_overload_cap", "Overload credit cap", "credit_overload_max", {"max_overload_credits": 27.0, "min_cgpa_required": 8.0}, "Demo overload threshold approved by the project owner; not an IIT Bhilai rule. Pending ordinance."),
        ("rule_minor_cse_eligibility", "CS minor eligibility", "minor_eligibility", {"min_cgpa_cutoff": 7.0}, "Illustrative threshold only. The supplied PDF contains no CS minor pathway or eligibility policy. Pending ordinance; this does not establish a credential."),
        ("rule_online_credit_transfer_limit", "Online credit planning cap", "online_credit_limit", {"max_online_credits_total": 25, "max_online_courses_per_semester": 1}, "Demo planning limit approved by the project owner; no online-credit policy was found in the supplied PDF. Pending ordinance."),
        ("rule_semester_parity", "Annual catalogue offering assumption", "semester_parity", {"assume_annual_scheduled_offering": True, "catalogue_electives_selectable": True}, "Scheduled courses are assumed to run in the semester printed in the curriculum; catalogue-only electives are assumed selectable for demo planning. Neither availability nor elective eligibility is guaranteed by the PDF. Pending ordinance."),
        ("rule_workload_hours", "Independent study workload estimate", "workload_hours", {"hours_per_credit_week": 2}, "Planning estimate approved by the project owner; not an IIT Bhilai workload standard. Pending ordinance."),
    ]
    academic_rules = [
        {
            "rule_id": rule_id,
            "name": name,
            "type": rule_type,
            "parameters": parameters,
            "source_text": reason,
            "source_url": "",
            "clause_id": "pending ordinance",
            "provenance": "assumption",
            "reason": reason,
            "last_verified": TODAY,
        }
        for rule_id, name, rule_type, parameters, reason in assumptions
    ]
    programme = [{
        "code": "BH-CSE-BTECH",
        "name": "BTech in Computer Science and Engineering",
        "department": "Computer Science and Engineering",
        "total_credits": 144,
        "semesters": 8,
        "core_credits": 96,
        "elective_credits": 22.5,
        "open_credits": 15,
        "structure": {
            "graded_total_credits": 144,
            "non_graded_core_units": 12,
            "categories": {"IC": 40.5, "PL": 4, "PC": 52, "PE": 22.5, "OE": 15, "LA": 10},
            "source_page": 21,
        },
        "source": "IIT Bhilai Courses of Study, October 2026, PDF p. 21",
        "source_page": 21,
        "provenance": "verified",
        "last_verified": TODAY,
    }]

    hero_profiles = [
        ("BH-SW-001", "Aarav Sharma", 4, 7.8, "goal_software", "Software engineer", ["CSL100", "CSL201", "CSL202", "CSP203", "CSL251", "CSL252", "CSL253"]),
        ("BH-HS-001", "Diya Iyer", 4, 8.7, "goal_higher_studies", "Computing researcher", ["CSL100", "CSL201", "CSL202", "CSP203", "CSL251", "CSL252", "CSL253"]),
        ("BH-UP-001", "Kabir Verma", 3, 7.2, "goal_upsc", "Civil services aspirant", ["CSL100", "CSL201", "CSL202", "CSP203"]),
    ]
    profiles = [
        {
            "student_id": sid,
            "name": name + " (Demo)",
            "programme": "BH-CSE-BTECH",
            "year": (semester + 1) // 2,
            "current_semester": semester,
            "cgpa": cgpa,
            "goal_id": goal_id,
            "target_role": role,
            "available_hours_per_week": 14,
            "remaining_elective_slots": 4,
            "completed_courses": [
                {"course_code": code, "grade": "B+" if cgpa < 8.5 else "A-", "semester_completed": min(semester, 6)}
                for code in completed
            ],
            "interests": [role],
            "constraints": {},
            "preferences": {"learning_style": ["practice questions", "short modules"]},
            "diagnostic_evidence": [],
            "provenance": "team_authored_demo_profile",
        }
        for sid, name, semester, cgpa, goal_id, role, completed in hero_profiles
    ]
    synthetic = []
    rng = random.Random(20261106)
    core_by_semester = {
        1: ["CSL100"],
        2: ["CSL100"],
        3: ["CSL201", "CSL202", "CSP203", "MAL403"],
        4: ["CSL201", "CSL202", "CSL251", "CSL252", "CSL253"],
        5: ["CSL202", "CSL251", "CSL252", "CSL253", "CSL301", "CSL302", "CSL303", "CSL304"],
        6: ["CSL252", "CSL253", "CSL301", "CSL302", "CSL303", "CSL304", "CSL351", "CSP352"],
    }
    valid_codes = {course["code"] for course in courses}
    for index in range(1, 76):
        semester = rng.choice([1, 2, 3, 4, 5, 6])
        completed = [code for code in core_by_semester[semester] if code in valid_codes]
        synthetic.append({
            "student_id": f"BH-SYN-{index:03d}",
            "name": f"{rng.choice(['Mira', 'Rohan', 'Anaya', 'Ishaan', 'Tara', 'Dev'])} {rng.choice(['Rao', 'Shah', 'Nair', 'Mehta', 'Das', 'Kapoor'])} (Synthetic)",
            "programme": "BH-CSE-BTECH",
            "year": (semester + 1) // 2,
            "current_semester": semester,
            "cgpa": round(rng.uniform(6.2, 9.6), 2),
            "goal_id": goals[(index - 1) % len(goals)][0],
            "target_role": goals[(index - 1) % len(goals)][2],
            "available_hours_per_week": rng.choice([8, 10, 12, 14, 16]),
            "remaining_elective_slots": rng.choice([2, 3, 4, 5]),
            "completed_courses": [
                {"course_code": code, "grade": rng.choice(["B", "B+", "A-", "A"]), "semester_completed": max(1, semester - 1)}
                for code in completed
            ],
            "interests": [],
            "constraints": {},
            "preferences": {"learning_style": ["practice questions"]},
            "diagnostic_evidence": [],
            "provenance": "team_authored_synthetic_profile",
        })

    curriculum_facts = {
        "profile": "iit_bhilai",
        "institution": "Indian Institute of Technology Bhilai",
        "programme": "BTech in Computer Science and Engineering",
        "source": "IIT Bhilai Courses of Study, October 2026; applicable for 2023 batch onwards",
        "source_file": "data/raw/courses of study.pdf",
        "full_extraction": "data/raw/courses_of_study_extracted.json",
        "source_page_count": 208,
        "source_pages_used": sorted({row["source_page"] for row in courses} | {21, 22, 9, 10, 11, 12}),
        "provenance_tiers": {
            "tier_1": "Verified PDF facts: course identity, codes, credits, L-T-P-C, schedule, programme structure, and printed prerequisite statements.",
            "tier_2": "Explicit demo assumptions marked pending ordinance and never represented as IIT Bhilai policy.",
            "tier_3": "Team-authored and derived skills, lessons, goal templates, and original assessments; skill links cite source syllabus pages where applicable.",
        },
        "limitations": [
            "No CS minor pathway or eligibility is stated in the supplied PDF.",
            "CSE catalogue-only courses are not assigned to BTech CSE PE/OE slots; their use is visibly assumption-backed.",
            "IC100 in the CSP352 prerequisite is printed in the source but could not be resolved to a course entry in this PDF.",
            "The PDF prints SL302 in one programme table and CSL302 in the next table/catalogue.",
            "The Liberal Arts catalogue titles and credits are verified; team-authored lessons are not official course syllabi.",
        ],
    }

    write_json("dataset.json", curriculum_facts)
    write_json("programmes.json", programme)
    write_json("courses.json", courses)
    write_json("prerequisites.json", prerequisites)
    write_json("skills.json", skills)
    write_json("course_skills.json", list(course_skills.values()))
    write_json("modules.json", modules)
    write_json("exercises.json", exercises)
    write_json("resources.json", resources)
    write_json("goal_templates.json", goal_templates)
    write_json("academic_rules.json", academic_rules)
    write_json("student_profiles.json", profiles)
    write_json("synthetic_profiles.json", synthetic)

    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    review.extend([
        {"item_type": "source_discrepancy", "item_id": "SL302/CSL302", "issue": "The semester table on PDF p. 21 prints SL302; p. 22 and catalogue p. 84 print CSL302.", "source_page": "21,22,84"},
        {"item_type": "prerequisite_code", "item_id": "CSP352:IC100", "issue": "Prerequisite printed as IC100 on PDF p. 86; no matching course entry was located in the 208-page PDF.", "source_page": 86},
        {"item_type": "policy_gap", "item_id": "CS-minor", "issue": "No CS-minor eligibility, curriculum, or credit pathway is stated in the supplied PDF.", "source_page": "full PDF"},
        {"item_type": "policy_gap", "item_id": "semester-credit-limits", "issue": "No minimum/maximum semester credits or overload rule was found; current values remain assumptions pending ordinance.", "source_page": "full PDF"},
        {"item_type": "policy_gap", "item_id": "course-offering-and-elective-eligibility", "issue": "Catalogue-only courses have no BTech CSE semester slot; annual availability and elective eligibility remain assumptions.", "source_page": "9,22,83-95"},
    ])
    with REVIEW_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["item_type", "item_id", "issue", "source_page"])
        writer.writeheader()
        writer.writerows(review)

    print(f"Built {len(courses)} courses, {len(skills)} skills, {len(modules)} modules, {len(exercises)} original exercises, {len(resources)} OERs.")
    print(f"Built {len(profiles)} hero personas and {len(synthetic)} synthetic profiles.")
    print(f"Review queue contains {len(review)} unresolved item(s).")


if __name__ == "__main__":
    build_seed()
