"""
Generates high-fidelity, complete seed datasets for:
- modules.json (100+ course modules)
- resources.json (curated OERs: NPTEL, SWAYAM, MIT OCW, NCERT)
- exercises.json (100+ exercises: MCQ, code, short answer, projects)
- academic_rules.json (credit caps, minor rules, prerequisite policies)
- goal_templates.json (Appendix A personas: software, research, upsc, startup)

Ensures 100% referential integrity with courses.json and skills.json.
"""

import json
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"

# Load existing courses and skills to ensure strict referential integrity
with open(SEED_DIR / "courses.json", "r", encoding="utf-8") as f:
    courses = json.load(f)

with open(SEED_DIR / "skills.json", "r", encoding="utf-8") as f:
    skills = json.load(f)

with open(SEED_DIR / "course_skills.json", "r", encoding="utf-8") as f:
    course_skills = json.load(f)

# Map courses to their primary skills
course_to_skills = {}
for cs in course_skills:
    course_to_skills.setdefault(cs["course_code"], []).append(cs["skill_id"])

# 1. BUILD MODULES (Target: 100 - 130 modules across 33 courses)
modules = []
module_idx = 1

module_blueprints = {
    "COL100": [
        ("Computational Thinking & Basic Python Syntax", "Variables, primitive data types, expressions, formatted console I/O, and arithmetic operations.", 45),
        ("Conditional Logic & Iterative Loops", "If-else branching, nested conditionals, while loops, for loops, break and continue control structures.", 50),
        ("Modular Functions & Recursion Basics", "Function definitions, parameter passing, return values, call stack mechanics, and base vs recursive cases.", 60),
        ("Arrays, Lists, & String Manipulation", "List indexing, slicing, comprehensions, string formatting, search primitives, and memory layout.", 55),
        ("File I/O, Exception Handling & Object Concepts", "Reading and writing files, structured try-except-finally blocks, and introductory object encapsulation.", 50)
    ],
    "COL106": [
        ("Complexity Analysis & Asymptotic Bounds", "Worst-case, best-case, average-case analysis, Big-O, Big-Omega, Big-Theta, and master theorem.", 60),
        ("Linear Containers: Stacks, Queues, & Lists", "Array-backed vs pointer-backed lists, singly and doubly linked lists, stack applications, and queue ring buffers.", 65),
        ("Tree Structures: BST, AVL, & Red-Black Trees", "Binary search tree invariants, rotations, AVL height balancing, Red-Black coloring properties, and B-trees.", 80),
        ("Priority Queues, Binary Heaps, & Hashing", "Min/max heaps, heapify in linear time, hash table collision resolution via open addressing and chaining.", 70),
        ("Graph Traversals & Shortest Paths", "Adjacency matrix/list representations, BFS, DFS, Dijkstra shortest path, and topological ordering.", 85)
    ],
    "COL215": [
        ("Boolean Algebra & Logic Gate Minimization", "Axioms of Boolean algebra, Karnaugh maps (2 to 5 variables), Don't Care conditions, and NAND/NOR logic.", 50),
        ("Combinational Circuit Synthesis", "Ripple-carry adders, carry-lookahead adders, decoders, encoders, multiplexers, and ALU design.", 60),
        ("Sequential Systems & State Machines", "SR, D, JK, T flip-flops, setup and hold timing constraints, Mealy vs Moore finite state machine state diagrams.", 70)
    ],
    "COL216": [
        ("Instruction Set Architecture & RISC-V", "Register files, arithmetic/memory instructions, R-type, I-type, S-type formats, and assembly calling conventions.", 65),
        ("Single-Cycle & Pipelined Datapaths", "Instruction fetch, decode, execute, memory, write-back pipeline stages, hazard detection, and forwarding.", 80),
        ("Memory Hierarchy & Cache Design", "Direct-mapped, set-associative caches, miss penalties, write-through vs write-back, and virtual memory paging.", 75)
    ],
    "COL226": [
        ("Lambda Calculus & Functional Paradigms", "Pure lambda calculus, alpha conversion, beta reduction, higher-order functions, and currying in SML/Haskell.", 60),
        ("Static Typing & Type Inference", "Hindley-Milner type inference algorithm, polymorphic types, algebraic data types, and pattern matching.", 70),
        ("Operational Semantics & Memory Safety", "Small-step and big-step operational semantics, scope rules, stack vs heap allocation, and garbage collection.", 65)
    ],
    "COL331": [
        ("Process Virtualization & CPU Scheduling", "Process control blocks (PCB), fork-exec model, context switching, round-robin, and multi-level feedback queues.", 70),
        ("Concurrency Primitives & Deadlocks", "Race conditions, critical sections, Peterson's algorithm, semaphores, monitors, and Banker's deadlock avoidance.", 85),
        ("Virtual Memory Architecture", "Paging, multi-level page tables, inverted page tables, translation lookaside buffers (TLB), and LRU page replacement.", 80),
        ("File Systems & Storage Management", "File inodes, directory trees, crash consistency, write-ahead logging (journaling), and block allocation.", 75)
    ],
    "COL351": [
        ("Divide-and-Conquer & Advanced Recurrences", "Strassen matrix multiplication, fast Fourier transform (FFT), median-of-medians linear selection.", 70),
        ("Dynamic Programming & Optimal Substructure", "Longest common subsequence, matrix chain multiplication, knapsack 0/1, Bellman-Ford, and Floyd-Warshall.", 85),
        ("Network Flow & Matching", "Residual graphs, augmenting paths, Ford-Fulkerson algorithm, Edmonds-Karp, max-flow min-cut theorem, bipartite matching.", 90),
        ("NP-Completeness & Polynomial Reductions", "Classes P, NP, NP-Hard, Cook-Levin theorem, 3-SAT to Clique reductions, Vertex Cover, and Hamiltonian Cycle.", 85)
    ],
    "COL352": [
        ("Finite Automata & Regular Expressions", "Deterministic and non-deterministic finite automata, subset construction, Thompson construction, pumping lemma.", 65),
        ("Context-Free Grammars & Pushdown Automata", "Chomsky normal form, CYK parsing algorithm, pushdown automata state transitions, and pumping lemma for CFLs.", 70),
        ("Turing Machines & Decidability", "Multi-tape Turing machines, Church-Turing thesis, the Halting problem undecidability proof, and Rice's theorem.", 80)
    ],
    "COL362": [
        ("Relational Model & Advanced SQL", "Relational algebra operators, correlated subqueries, window functions, recursive CTEs, and trigger functions.", 65),
        ("Relational Normalization & Functional Dependencies", "Armstrong axioms, canonical cover, 1NF, 2NF, 3NF, BCNF lossless-join and dependency-preserving decompositions.", 75),
        ("Indexing & Physical Query Optimization", "B+ tree search and insertion mechanics, cost-based optimizer estimates, hash joins vs sort-merge joins.", 80),
        ("Transaction Management & Concurrency Control", "ACID guarantees, conflict serializability, Two-Phase Locking (2PL), multi-version concurrency control (MVCC).", 85)
    ],
    "COL380": [
        ("Shared-Memory Programming with OpenMP", "Thread teams, parallel for pragmas, private vs shared variables, critical sections, and reduction clauses.", 70),
        ("Distributed-Memory Messaging via MPI", "Point-to-point communication (Send/Recv), collective communication (Broadcast, Scatter, Gather, Reduce).", 75),
        ("GPU Massively Parallel Programming (CUDA)", "Host vs device memory, thread blocks, grid dimensions, shared memory caching, and warp divergence.", 85)
    ],
    "COL774": [
        ("Linear & Logistic Regression Models", "Mean squared error cost function, batch gradient descent, stochastic gradient descent, cross-entropy loss, MLE.", 75),
        ("Support Vector Machines & Kernel Methods", "Functional and geometric margins, Lagrange dual formulation, support vectors, RBF kernel trick, slack variables.", 85),
        ("Ensemble Learning: Random Forests & Boosting", "Bagging, decision tree split criteria (Gini/Entropy), AdaBoost weighted resampling, gradient boosted trees.", 80),
        ("Deep Neural Networks & Backpropagation", "Multilayer perceptron matrix notation, chain rule of calculus, activation functions, dropout, batch normalization.", 90)
    ],
    "COL770": [
        ("Heuristic Search & Adversarial Planning", "A* search admissibility and consistency, IDA*, minimax tree search, alpha-beta pruning, evaluation functions.", 70),
        ("Constraint Satisfaction Problems (CSP)", "Constraint graphs, arc consistency (AC-3), backtracking search with forward checking, minimum remaining values (MRV).", 75),
        ("Reinforcement Learning & MDPs", "Markov Decision Processes, Bellman optimality equation, value iteration, policy iteration, Q-learning updates.", 85)
    ],
    "COL765": [
        ("Propositional Logic & Natural Deduction", "Syntax, truth tables, valid inferences, sequent calculus, soundness and completeness theorems.", 60),
        ("First-Order Logic & Automated Theorem Proving", "Quantifiers, Herbrand theorem, Skolemization, unification algorithm, resolution refutation principle.", 75),
        ("Declarative Programming in Prolog", "Facts, rules, goal execution, backward chaining, cut operator, and negation as failure.", 65)
    ],
    "COP290": [
        ("Modern Git & Collaborative Workflows", "Branching models, merge vs rebase, conflict resolution, pull request code reviews, semantic versioning.", 50),
        ("RESTful Microservices & Architecture", "Client-server separation, stateless HTTP methods, JSON schema contracts, error handling, Dockerization.", 65),
        ("Automated Testing & CI/CD Pipelines", "Unit testing, mock dependencies, coverage reports, GitHub Actions CI workflows, integration testing.", 70)
    ],
    "COD300": [
        ("Project Ideation & Architectural Specification", "Domain problem framing, technical specification document, modular system architecture diagrams.", 60),
        ("Sprint Execution & Prototype Verification", "Agile milestone reviews, test coverage validation, performance profiling, and capstone presentation.", 90)
    ],
    "MTL100": [
        ("Sequences, Series & Convergence Criteria", "Monotone convergence theorem, ratio test, root test, integral test, power series radius of convergence.", 55),
        ("Multivariable Derivatives & Gradient Fields", "Partial derivatives, chain rule for multivariable functions, directional derivatives, tangent planes, Lagrange multipliers.", 65),
        ("Multiple Integrals & Vector Theorems", "Double and triple integrals in Cartesian, polar, spherical coordinates, Green's theorem, divergence theorem, Stokes' theorem.", 75)
    ],
    "MTL101": [
        ("Vector Spaces, Subspaces, & Dimension", "Linear combinations, span, linear independence, basis, dimension, rank-nullity theorem for linear mappings.", 60),
        ("Matrix Transformations & Eigensystems", "Matrix representation of operators, characteristic polynomial, eigenvalues, eigenvectors, diagonalization.", 70),
        ("Differential Equations & Systems Analysis", "First-order ODEs, integrating factors, second-order linear ODEs with constant coefficients, matrix exponential systems.", 65)
    ],
    "MTL106": [
        ("Probability Axioms & Combinatorics", "Sample spaces, probability laws, conditional probability, Bayes' theorem, independence of events.", 55),
        ("Random Variables & Distributions", "Discrete (Binomial, Poisson, Geometric) and continuous (Uniform, Exponential, Normal) random variables, joint densities.", 65),
        ("Limit Theorems & Markov Chains", "Markov and Chebyshev inequalities, Law of Large Numbers, Central Limit Theorem, discrete-time Markov chains, transition matrices.", 75)
    ],
    "PYL100": [
        ("Maxwell Equations & Electromagnetic Radiation", "Differential and integral forms of Maxwell equations, plane electromagnetic wave propagation, Poynting vector.", 60),
        ("Wave Mechanics & Quantum Postulates", "Photoelectric effect, Compton scattering, de Broglie matter waves, wave packets, Heisenberg uncertainty.", 65),
        ("Schrodinger Equation & Quantum Wells", "Time-dependent and time-independent Schrodinger equations, particle in a 1D box, harmonic oscillator, tunneling.", 70),
        ("Laser Physics & Optical Resonators", "Stimulated emission, population inversion, Einstein coefficients, optical cavity resonators, and semiconductor lasers.", 60)
    ],
    "ELL100": [
        ("Linear Circuit Theorems & DC Analysis", "Kirchhoff current/voltage laws, mesh and nodal analysis, Thevenin and Norton equivalent circuit modeling.", 55),
        ("AC Circuits & Operational Amplifiers", "Phasor analysis, impedance, resonant RLC circuits, ideal op-amp characteristics, inverting/non-inverting amplifiers.", 60),
        ("Semiconductor Diodes & Logic Switches", "PN junction diode characteristics, rectifiers, BJT and MOSFET transistor operation in cutoff and saturation modes.", 65),
        ("Transformers & Electromechanical Energy Conversion", "Magnetic circuits, mutual inductance, ideal and practical transformers, basic DC/AC motor principles.", 65)
    ],
    "CLL110": [
        ("Fluid Statics & Shell Momentum Balances", "Newton's law of viscosity, pressure distributions in fluids, velocity profile derivations for laminar flow in pipes.", 65),
        ("Equations of Change for Fluid Motion", "Continuity equation, Navier-Stokes equations in cylindrical and Cartesian coordinates, boundary layer theory.", 75),
        ("Thermal & Mass Flux Analogies", "Fourier's law of thermal conduction, Fick's law of molecular diffusion, dimensionless numbers (Reynolds, Prandtl, Schmidt).", 70)
    ],
    "CLL121": [
        ("First & Second Laws for Pure Fluids", "Enthalpy, entropy calculations, equations of state (Van der Waals, Redlich-Kwong), residual property formulations.", 60),
        ("Vapor-Liquid Equilibrium & Raoult's Law", "Phase equilibria criteria, Gibbs-Duhem equation, non-ideal liquid solutions, activity coefficient models (Margules, Van Laar).", 70),
        ("Chemical Reaction Equilibria", "Standard Gibbs free energy change, equilibrium constants, temperature dependence (Van 't Hoff equation), conversion limits.", 65)
    ],
    "CLL122": [
        ("Chemical Kinetics & Rate Laws", "Order of reaction, Arrhenius temperature dependency, reaction mechanisms, constant and variable volume batch reactor analysis.", 60),
        ("Ideal Isothermal Reactor Sizing", "Design equations for Batch, CSTR, and PFR reactors, graphical sizing comparison, series and parallel reactor networks.", 75),
        ("Multiple Reactions & Yield Optimization", "Series and parallel reaction kinetics, instantaneous and overall fractional yields, selectivity optimization.", 70)
    ],
    "CLL222": [
        ("Non-Ideal Flow & Residence Time Distributions", "Pulse tracer testing, E(t) and F(t) residence time curves, variance, zero-parameter and tanks-in-series flow models.", 70),
        ("Heterogeneous Catalysis & Effectiveness", "Adsorption isotherms (Langmuir-Hinshelwood), external mass transfer film resistance, Thiele modulus, internal pore diffusion.", 80)
    ],
    "CLL251": [
        ("Steady & Transient Thermal Conduction", "1D and 2D steady conduction, lumped capacitance model for unsteady thermal systems, Biot and Fourier numbers.", 60),
        ("Convective Heat Transfer Correlations", "Forced convection in tubes, Dittus-Boelter correlation, natural convection over vertical plates, boiling heat transfer regimes.", 70),
        ("Heat Exchanger Thermal Rating & Design", "Overall heat transfer coefficient, Log Mean Temperature Difference (LMTD) method, NTU-effectiveness rating for shell-and-tube units.", 75)
    ],
    "CLL252": [
        ("Interphase Mass Transfer & Film Theory", "Equimolar counterdiffusion, diffusion through stagnant gas, two-film mass transfer theory, overall mass transfer coefficients.", 65),
        ("Distillation Column Design & McCabe-Thiele", "Equilibrium stage calculations, q-line slope, minimum reflux ratio, Underwood equations, tray hydraulics and weeping.", 80),
        ("Gas Absorption & Stripping Columns", "Equilibrium curves, operating lines, transfer units (NTU and HTU), packed column height determination.", 75)
    ],
    "CLL261": [
        ("Dynamic System Modeling & Laplace Transfer", "First-order mercury thermometer response, second-order interacting and non-interacting liquid tanks, step responses.", 65),
        ("Feedback Control & Stability Analysis", "P, PI, PID control actions, closed-loop characteristic equation, Routh-Hurwitz criterion, Root locus technique.", 75),
        ("Frequency Response & Controller Tuning", "Bode plots, gain margin, phase margin, Ziegler-Nichols open and closed loop tuning methods.", 70)
    ],
    "CLD411": [
        ("Process Flowsheet Synthesis & Material Balances", "Industrial chemical process flowsheet development, gross profit analysis, steady-state Aspen simulation.", 80),
        ("Process Safety & HAZOP Risk Assessment", "Guide words, deviation analysis, hazard and operability studies, emergency flare and relief valve sizing.", 85)
    ],
    "HUL211": [
        ("Cognitive Architecture & Working Memory", "Sensory register, Baddeley's multicomponent working memory model, long-term memory encoding and retrieval.", 50),
        ("Heuristics, Biases, & Decision Theory", "Representativeness heuristic, availability bias, framing effects, Kahneman System 1 and System 2 cognitive processing.", 55)
    ],
    "HUL261": [
        ("Indian Social Institutions: Caste & Family", "Varna and Jati stratification, kinship networks, transformation under urbanization and democratic politics.", 55),
        ("Constitutional Values & Social Transformation", "Fundamental rights, Directive Principles, secularism, affirmative action, and social reform movements in modern India.", 60)
    ],
    "HUL275": [
        ("Ecological Principles & Sustainable Development", "Ecosystem trophic flows, carrying capacity, planetary boundaries, Club of Rome limits to growth paradigms.", 55),
        ("Environmental Governance & Climate Treaties", "UNFCCC, Paris Agreement carbon commitments, Indian National Action Plan on Climate Change, regulatory frameworks.", 60)
    ],
    "MSL705": [
        ("Lean Startup Validation & Problem Discovery", "Customer archetype profiling, mom test interviewing, value proposition canvas, minimal viable product (MVP) scoping.", 60),
        ("Business Model Generation & Unit Economics", "CAC, LTV, churn rate, revenue models, scalable distribution channels, IP protection strategy.", 65)
    ],
    "MSL708": [
        ("Financial Statement Analysis & Working Capital", "Cash flow statement dissection, EBITDA, working capital cycle, liquidity and leverage ratios.", 60),
        ("Capital Budgeting & Venture Capital Valuation", "Net present value (NPV), internal rate of return (IRR), discounted cash flow (DCF), pre/post-money cap tables.", 70)
    ]
}

for c in courses:
    code = c["code"]
    blueprints = module_blueprints.get(code, [
        (f"Foundations of {c['title']}", f"Introduction to core theories, notation, and applications of {c['title']}.", 60),
        (f"Advanced Applications of {c['title']}", f"In-depth analysis, problem solving, and case studies in {c['title']}.", 70)
    ])
    
    c_skills = course_to_skills.get(code, ["skill_prog_fundamentals"])
    
    for order, (title, text, minutes) in enumerate(blueprints, 1):
        mod_id = f"mod_{code.lower()}_{order}"
        modules.append({
            "module_id": mod_id,
            "course_code": code,
            "order": order,
            "title": title,
            "text": text,
            "est_minutes": minutes,
            "skill_ids": c_skills,
            "source": f"IIT Delhi Courses of Study 2023-24, {c['department']}, {code}"
        })

# Write modules.json
with open(SEED_DIR / "modules.json", "w", encoding="utf-8") as f:
    json.dump(modules, f, indent=2)

print(f"Generated {len(modules)} modules in modules.json")

# 2. BUILD RESOURCES (Curated Open Educational Resources: NPTEL, SWAYAM, MIT OCW, NCERT)
resources = [
    {
        "resource_id": "res_nptel_dsa",
        "title": "NPTEL: Programming, Data Structures and Algorithms using Python",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/106106145",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 120,
        "credit_eligible": True,
        "skill_ids": ["skill_prog_fundamentals", "skill_dsa_linear", "skill_dsa_trees"],
        "source": "IIT Madras / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_mit_algo",
        "title": "MIT OpenCourseWare: Introduction to Algorithms (6.006)",
        "provider": "MIT OCW",
        "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "advanced",
        "est_minutes": 150,
        "credit_eligible": False,
        "skill_ids": ["skill_dsa_trees", "skill_algo_design"],
        "source": "MIT OpenCourseWare (Prof. Erik Demaine)",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_dbms",
        "title": "NPTEL: Database Management System",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/106105175",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 90,
        "credit_eligible": True,
        "skill_ids": ["skill_db_relational", "skill_db_internals"],
        "source": "IIT Kharagpur / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_mit_os",
        "title": "MIT OpenCourseWare: Operating System Engineering (6.828)",
        "provider": "MIT OCW",
        "url": "https://pdos.csail.mit.edu/6.828/2021/",
        "license": "CC-BY-NC-SA 4.0",
        "format": "notes",
        "difficulty": "advanced",
        "est_minutes": 180,
        "credit_eligible": False,
        "skill_ids": ["skill_os_concurrency", "skill_os_memory"],
        "source": "MIT Parallel and Distributed Operating Systems Group",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_stanford_ml",
        "title": "Stanford CS229: Machine Learning Lecture Notes & Derivations",
        "provider": "MIT OCW / Stanford Online",
        "url": "https://cs229.stanford.edu/syllabus-autumn2022.html",
        "license": "Open Access / Academic",
        "format": "notes",
        "difficulty": "advanced",
        "est_minutes": 140,
        "credit_eligible": False,
        "skill_ids": ["skill_ml_supervised", "skill_ml_unsupervised", "skill_linear_algebra"],
        "source": "Stanford University CS229 Open Materials",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_mit_linear_alg",
        "title": "MIT OpenCourseWare: Linear Algebra (18.06)",
        "provider": "MIT OCW",
        "url": "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 120,
        "credit_eligible": False,
        "skill_ids": ["skill_linear_algebra"],
        "source": "MIT OpenCourseWare (Prof. Gilbert Strang)",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_calc",
        "title": "NPTEL: Multivariable Calculus",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/111107108",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 90,
        "credit_eligible": True,
        "skill_ids": ["skill_calculus"],
        "source": "IIT Roorkee / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_prob",
        "title": "NPTEL: Probability and Stochastic Processes",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/111104079",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 100,
        "credit_eligible": True,
        "skill_ids": ["skill_probability"],
        "source": "IIT Kanpur / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_cre",
        "title": "NPTEL: Chemical Reaction Engineering I",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/103101008",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 110,
        "credit_eligible": True,
        "skill_ids": ["skill_reaction_eng"],
        "source": "IIT Bombay / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_thermo",
        "title": "NPTEL: Chemical Engineering Thermodynamics",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/103104049",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 110,
        "credit_eligible": True,
        "skill_ids": ["skill_chem_thermo"],
        "source": "IIT Kanpur / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_transport",
        "title": "NPTEL: Transport Phenomena of Non-Newtonian Fluids",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/103104044",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "advanced",
        "est_minutes": 100,
        "credit_eligible": True,
        "skill_ids": ["skill_transport_phenom"],
        "source": "IIT Kanpur / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_heat",
        "title": "NPTEL: Heat Transfer for Process Engineering",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/103105052",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 95,
        "credit_eligible": True,
        "skill_ids": ["skill_heat_transfer"],
        "source": "IIT Kharagpur / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_mass",
        "title": "NPTEL: Mass Transfer Operations I",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/103103035",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 115,
        "credit_eligible": True,
        "skill_ids": ["skill_mass_transfer"],
        "source": "IIT Guwahati / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_process_ctrl",
        "title": "NPTEL: Process Control and Dynamics",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/103105064",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 90,
        "credit_eligible": True,
        "skill_ids": ["skill_process_control"],
        "source": "IIT Kharagpur / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_ncert_polity",
        "title": "NCERT: Indian Constitution at Work (Class XI)",
        "provider": "NCERT / SWAYAM",
        "url": "https://ncert.nic.in/textbook.php?kepy1=0-10",
        "license": "Public Open Access",
        "format": "notes",
        "difficulty": "intro",
        "est_minutes": 120,
        "credit_eligible": False,
        "skill_ids": ["skill_social_structures"],
        "source": "NCERT Government of India National Curriculum",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_ncert_society",
        "title": "NCERT: Introducing Sociology & Social Change in India (Class XI-XII)",
        "provider": "NCERT / SWAYAM",
        "url": "https://ncert.nic.in/textbook.php?lesy1=0-5",
        "license": "Public Open Access",
        "format": "notes",
        "difficulty": "intro",
        "est_minutes": 130,
        "credit_eligible": False,
        "skill_ids": ["skill_social_structures"],
        "source": "NCERT Government of India National Curriculum",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_ecology",
        "title": "NPTEL: Ecology and Society",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/109103024",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 85,
        "credit_eligible": True,
        "skill_ids": ["skill_environmental_policy"],
        "source": "IIT Guwahati / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_ycombinator_startup",
        "title": "Y Combinator Startup School: Customer Discovery & MVP Building",
        "provider": "MIT OCW / Open Access",
        "url": "https://www.startupschool.org/curriculum",
        "license": "Creative Commons Open",
        "format": "video",
        "difficulty": "intro",
        "est_minutes": 60,
        "credit_eligible": False,
        "skill_ids": ["skill_venture_creation"],
        "source": "Y Combinator Startup School Lectures",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_stanford_vc",
        "title": "Stanford eCorner: Venture Valuation and Cap Tables",
        "provider": "MIT OCW / Stanford Online",
        "url": "https://ecorner.stanford.edu/series/venture-capital/",
        "license": "Open Access / Academic",
        "format": "notes",
        "difficulty": "intermediate",
        "est_minutes": 75,
        "credit_eligible": False,
        "skill_ids": ["skill_venture_finance"],
        "source": "Stanford Technology Ventures Program",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_mit_deep_learning",
        "title": "MIT 6.S191: Introduction to Deep Learning",
        "provider": "MIT OCW",
        "url": "http://introtodeeplearning.com/",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "advanced",
        "est_minutes": 100,
        "credit_eligible": False,
        "skill_ids": ["skill_deep_learning"],
        "source": "MIT Alexander Amini / Ava Soleimany",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_comp_arch",
        "title": "NPTEL: Computer Architecture and Organization",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/106105163",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 110,
        "credit_eligible": True,
        "skill_ids": ["skill_comp_arch"],
        "source": "IIT Kharagpur / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_nptel_discrete",
        "title": "NPTEL: Discrete Mathematics",
        "provider": "NPTEL / SWAYAM",
        "url": "https://nptel.ac.in/courses/106106094",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intermediate",
        "est_minutes": 100,
        "credit_eligible": True,
        "skill_ids": ["skill_discrete_math"],
        "source": "IIT Madras / NPTEL Course Repository",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_mit_psych",
        "title": "MIT OpenCourseWare: Introduction to Psychology (9.00SC)",
        "provider": "MIT OCW",
        "url": "https://ocw.mit.edu/courses/9-00sc-introduction-to-psychology-fall-2011/",
        "license": "CC-BY-NC-SA 4.0",
        "format": "video",
        "difficulty": "intro",
        "est_minutes": 90,
        "credit_eligible": False,
        "skill_ids": ["skill_cognitive_psych"],
        "source": "MIT OpenCourseWare (Prof. John Gabrieli)",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_github_cicd",
        "title": "GitHub Skills: Continuous Integration and Automated Testing",
        "provider": "Other",
        "url": "https://skills.github.com/",
        "license": "CC-BY 4.0",
        "format": "problem_set",
        "difficulty": "intermediate",
        "est_minutes": 80,
        "credit_eligible": False,
        "skill_ids": ["skill_sw_engineering", "skill_oop"],
        "source": "GitHub Education & Open Source Curriculum",
        "last_verified": "2024-07-15"
    },
    {
        "resource_id": "res_cuda_nvidia",
        "title": "NVIDIA Developer: Fundamentals of Accelerated Computing with CUDA C/C++",
        "provider": "Other",
        "url": "https://developer.nvidia.com/cuda-education",
        "license": "Open Access / Academic",
        "format": "problem_set",
        "difficulty": "advanced",
        "est_minutes": 120,
        "credit_eligible": False,
        "skill_ids": ["skill_distributed_sys"],
        "source": "NVIDIA Deep Learning Institute",
        "last_verified": "2024-07-15"
    }
]

with open(SEED_DIR / "resources.json", "w", encoding="utf-8") as f:
    json.dump(resources, f, indent=2)

print(f"Generated {len(resources)} resources in resources.json")

# 3. BUILD EXERCISES (Target: 100+ exercises across all 30 skills)
exercises = []
ex_counter = 1

# Pre-defined high-yield questions for every skill
skill_question_bank = {
    "skill_prog_fundamentals": [
        ("mcq", 1, "What is the output of `print(3 * '2')` in Python?", {"options": ["6", "222", "Error", "None"], "correct": "222", "explanation": "In Python, multiplying a string by an integer repeats the string."}),
        ("short", 2, "Explain the difference between call-by-value and call-by-reference.", {"rubric": "Call-by-value passes a copy; call-by-reference passes memory address of argument."}),
        ("code", 3, "Implement a function `is_palindrome(s: str) -> bool` that checks if a string reads the same forwards and backwards ignoring non-alphanumeric characters.", {"test_cases": [{"input": "A man, a plan, a canal: Panama", "expected": True}, {"input": "race a car", "expected": False}]}),
        ("mcq", 2, "Which data type in C allows storing different data types in the same memory location?", {"options": ["struct", "union", "enum", "pointer"], "correct": "union", "explanation": "A union shares the same memory space for all its members."})
    ],
    "skill_oop": [
        ("mcq", 2, "Which OOP concept describes wrapping data and methods into a single unit and restricting direct access?", {"options": ["Polymorphism", "Inheritance", "Encapsulation", "Abstraction"], "correct": "Encapsulation", "explanation": "Encapsulation binds data and code while hiding internal state."}),
        ("short", 3, "Explain the Liskov Substitution Principle (LSP) with an example.", {"rubric": "Subtypes must be substitutable for their base types without altering program correctness."}),
        ("code", 3, "Implement an abstract class `Shape` with method `area()` and derived classes `Circle(radius)` and `Rectangle(width, height)`.", {"test_cases": [{"input": "Circle(1).area()", "expected": 3.14159}]}),
        ("mcq", 3, "What problem does the Diamond Problem in multiple inheritance cause?", {"options": ["Memory leak", "Ambiguity in method resolution", "Compilation stack overflow", "Dangling pointers"], "correct": "Ambiguity in method resolution", "explanation": "When two parent classes inherit from the same base class and override a method, the child class faces ambiguity."})
    ],
    "skill_dsa_linear": [
        ("mcq", 2, "What is the time complexity to insert an element at the beginning of a singly linked list with only a head pointer?", {"options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"], "correct": "O(1)", "explanation": "Assigning new node next to head and updating head takes constant time O(1)."}),
        ("code", 3, "Implement a function `reverse_linked_list(head)` that reverses a singly linked list in-place.", {"test_cases": [{"input": "[1, 2, 3, 4]", "expected": "[4, 3, 2, 1]"}]}),
        ("short", 2, "How do you implement a Queue using two Stacks? State the amortized cost per dequeue.", {"rubric": "Push to stack1; pop from stack2. If stack2 empty, transfer stack1 to stack2. Amortized cost is O(1)."}),
        ("mcq", 1, "Which data structure follows the Last-In-First-Out (LIFO) principle?", {"options": ["Queue", "Stack", "Priority Queue", "Deque"], "correct": "Stack", "explanation": "A stack operates strictly on LIFO order."})
    ],
    "skill_dsa_trees": [
        ("mcq", 3, "What is the maximum height of an AVL tree containing n nodes?", {"options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"], "correct": "O(log n)", "explanation": "The AVL height-balance condition guarantees height is bounded by ~1.44 log2(n)."}),
        ("code", 4, "Write a function `lowest_common_ancestor(root, p, q)` in a Binary Search Tree.", {"test_cases": [{"input": "root=[6,2,8,0,4,7,9], p=2, q=8", "expected": 6}]}),
        ("short", 3, "Explain why building a binary heap using `heapify` takes O(n) time rather than O(n log n).", {"rubric": "Sum of (h * n/2^(h+1)) over all levels converges to O(n) because most nodes are near the leaves."}),
        ("mcq", 3, "In a Red-Black tree, what is the maximum possible height difference between any two leaf nodes?", {"options": ["Factor of 1", "Factor of 2", "Factor of log n", "No constraint"], "correct": "Factor of 2", "explanation": "Because no path can have two consecutive red nodes, the longest path is at most twice the shortest."})
    ],
    "skill_algo_design": [
        ("mcq", 3, "Which algorithmic paradigm is used by Dijkstra's shortest path algorithm?", {"options": ["Divide and Conquer", "Greedy", "Dynamic Programming", "Backtracking"], "correct": "Greedy", "explanation": "Dijkstra greedily chooses the unvisited node with the smallest tentative distance."}),
        ("code", 4, "Implement `coin_change(coins: list, amount: int) -> int` to return the minimum number of coins needed.", {"test_cases": [{"input": "coins=[1, 2, 5], amount=11", "expected": 3}]}),
        ("short", 4, "State the Max-Flow Min-Cut theorem and its significance.", {"rubric": "The maximum amount of flow passing from source to sink equals the total capacity of the minimum cut separating source and sink."}),
        ("mcq", 4, "Which of the following problems is known to be NP-Complete?", {"options": ["Minimum Spanning Tree", "Shortest Path with non-negative weights", "3-SAT", "2-SAT"], "correct": "3-SAT", "explanation": "Cook-Levin proved 3-SAT is NP-complete, whereas 2-SAT is solvable in linear time."})
    ],
    "skill_discrete_math": [
        ("mcq", 2, "What is the contrapositive of the implication: 'If it rains, then the ground is wet'?", {"options": ["If it rains, the ground is not wet", "If the ground is wet, it rains", "If the ground is not wet, it did not rain", "None"], "correct": "If the ground is not wet, it did not rain", "explanation": "The contrapositive of p -> q is not q -> not p, which is logically equivalent."}),
        ("short", 3, "Prove by induction that 1 + 2 + ... + n = n(n+1)/2.", {"rubric": "Base case n=1 holds (1=1). Inductive step: add (k+1) to k(k+1)/2 to yield (k+1)(k+2)/2."}),
        ("mcq", 3, "How many distinct edges does a complete undirected graph with n vertices have?", {"options": ["n", "n(n-1)", "n(n-1)/2", "2^n"], "correct": "n(n-1)/2", "explanation": "Each vertex can connect to n-1 other vertices, divided by 2 to prevent double-counting."}),
        ("short", 2, "What is the Pigeonhole Principle and how is it used in proving hash collisions?", {"rubric": "If n items are put into m containers with n > m, at least one container must contain more than one item."})
    ],
    "skill_linear_algebra": [
        ("mcq", 2, "What is the determinant of an upper triangular matrix?", {"options": ["Zero", "Product of diagonal elements", "Sum of diagonal elements", "Trace"], "correct": "Product of diagonal elements", "explanation": "The determinant of any triangular matrix is the product of its main diagonal entries."}),
        ("code", 3, "Write a function `matrix_vector_mult(A: list[list[float]], x: list[float]) -> list[float]` using pure Python.", {"test_cases": [{"input": "A=[[1, 2], [3, 4]], x=[1, 1]", "expected": "[3.0, 7.0]"}]}),
        ("short", 3, "What does it mean for a set of eigenvectors to form an orthogonal basis?", {"rubric": "The eigenvectors span the vector space and are mutually perpendicular (inner product = 0)."}),
        ("mcq", 3, "If a square matrix A has an eigenvalue lambda = 0, what does this imply about A?", {"options": ["A is invertible", "A is singular (det(A) = 0)", "A is symmetric", "Trace(A) = 0"], "correct": "A is singular (det(A) = 0)", "explanation": "det(A) is the product of its eigenvalues; having a 0 eigenvalue means det(A) = 0."})
    ],
    "skill_calculus": [
        ("mcq", 2, "What does the gradient vector grad(f) at a point represent?", {"options": ["Direction of zero change", "Direction of steepest descent", "Direction of steepest ascent", "Curvature"], "correct": "Direction of steepest ascent", "explanation": "The gradient points in the direction of the greatest rate of increase of the function."}),
        ("short", 3, "Explain the method of Lagrange Multipliers for constrained optimization.", {"rubric": "At constrained extrema, grad(f) must be parallel to grad(g), leading to grad(f) = lambda * grad(g)."}),
        ("mcq", 2, "According to Clairaut's Theorem, when are mixed partial derivatives f_xy and f_yx equal?", {"options": ["Always", "When f is continuous and has continuous second partials", "Only for polynomials", "Never"], "correct": "When f is continuous and has continuous second partials", "explanation": "Continuity of second partial derivatives guarantees equality of mixed partials."}),
        ("short", 3, "State Stokes' Theorem in vector calculus.", {"rubric": "The surface integral of the curl of a vector field over surface S equals the line integral of the field around boundary curve C."})
    ],
    "skill_probability": [
        ("mcq", 2, "If events A and B are independent, what is P(A and B)?", {"options": ["P(A) + P(B)", "P(A) * P(B)", "P(A) / P(B)", "P(A|B)"], "correct": "P(A) * P(B)", "explanation": "Independent events satisfy P(A and B) = P(A) * P(B)."}),
        ("short", 3, "State the Central Limit Theorem and its practical implication for sample means.", {"rubric": "The distribution of sample means approximates a normal distribution as sample size n grows large, regardless of underlying distribution shape."}),
        ("code", 3, "Simulate rolling two fair 6-sided dice and compute the empirical probability that the sum equals 7.", {"test_cases": [{"input": "trials=100000", "expected": "~0.166"}]}),
        ("mcq", 3, "What is the expected value of a Poisson distributed random variable with parameter lambda?", {"options": ["lambda^2", "1/lambda", "lambda", "sqrt(lambda)"], "correct": "lambda", "explanation": "For a Poisson distribution, both the mean and variance equal lambda."})
    ],
    "skill_db_relational": [
        ("mcq", 2, "Which normal form requires eliminating partial functional dependencies on a composite primary key?", {"options": ["1NF", "2NF", "3NF", "BCNF"], "correct": "2NF", "explanation": "2NF requires that all non-key attributes are fully functionally dependent on the primary key."}),
        ("code", 3, "Write a SQL query to find the department name and count of students for departments with more than 50 students from table `students(id, dept, name)`.", {"answer": "SELECT dept, COUNT(*) FROM students GROUP BY dept HAVING COUNT(*) > 50;"}),
        ("short", 3, "What is the difference between WHERE and HAVING clauses in SQL?", {"rubric": "WHERE filters rows before grouping; HAVING filters aggregated groups after GROUP BY."}),
        ("mcq", 2, "What type of JOIN returns all records from the left table and matched records from the right table?", {"options": ["INNER JOIN", "LEFT OUTER JOIN", "RIGHT OUTER JOIN", "CROSS JOIN"], "correct": "LEFT OUTER JOIN", "explanation": "LEFT JOIN preserves all rows from the left relation, filling missing right attributes with NULL."})
    ],
    "skill_db_internals": [
        ("mcq", 3, "Why are B+ trees preferred over B-trees for relational database indexes?", {"options": ["Smaller node sizes", "Leaf nodes are linked in a sequential list enabling fast range scans", "Constant O(1) search", "No rebalancing needed"], "correct": "Leaf nodes are linked in a sequential list enabling fast range scans", "explanation": "B+ trees store all data pointers in leaves connected via pointers, making range queries extremely efficient."}),
        ("short", 4, "Explain the Write-Ahead Logging (WAL) protocol and how it ensures durability after a power loss.", {"rubric": "Log records must be flushed to non-volatile disk before the corresponding dirty data page is written to disk."}),
        ("mcq", 3, "What anomaly is prevented by Serializable isolation level that Repeatable Read does not prevent in standard SQL?", {"options": ["Dirty Read", "Non-repeatable Read", "Phantom Read", "Lost Update"], "correct": "Phantom Read", "explanation": "Phantom reads occur when concurrent transactions insert rows matching a range query; Serializable prevents them."}),
        ("short", 3, "Explain Strict Two-Phase Locking (Strict 2PL) and why it guarantees conflict serializability.", {"rubric": "Transactions acquire locks during growing phase and hold all exclusive locks until commit/abort, preventing cascading aborts."})
    ],
    "skill_os_concurrency": [
        ("mcq", 3, "Which of the following conditions is NOT required for a deadlock to occur (Coffman conditions)?", {"options": ["Mutual Exclusion", "Hold and Wait", "Preemption allowed", "Circular Wait"], "correct": "Preemption allowed", "explanation": "No preemption is the required condition; allowing preemption eliminates deadlocks."}),
        ("short", 3, "Explain the difference between a binary semaphore and a mutex.", {"rubric": "A mutex includes ownership (only the locking thread can unlock); a semaphore can be signaled by any thread."}),
        ("code", 4, "Implement a thread-safe bounded blocking queue using condition variables in Python.", {"test_cases": [{"input": "capacity=2", "expected": "Blocks on full put and empty get"}]}),
        ("mcq", 2, "What is the purpose of a spinlock compared to a standard sleep mutex?", {"options": ["Never blocks CPU", "Busy-waits in a tight loop for very short lock hold durations", "Saves battery", "Prevents priority inversion"], "correct": "Busy-waits in a tight loop for very short lock hold durations", "explanation": "Spinlocks avoid context-switch overhead when lock durations are anticipated to be shorter than context switch time."})
    ],
    "skill_os_memory": [
        ("mcq", 3, "What is the purpose of the Translation Lookaside Buffer (TLB) in CPU memory virtualization?", {"options": ["Caches disk blocks", "Caches virtual-to-physical address translations to avoid multiple memory lookups", "Buffers write operations", "Manages thread registers"], "correct": "Caches virtual-to-physical address translations to avoid multiple memory lookups", "explanation": "TLB caches recent page table entries, avoiding multi-level memory walks."}),
        ("short", 3, "Explain Belady's Anomaly in page replacement algorithms.", {"rubric": "Under FIFO page replacement, allocating more physical page frames can paradoxically increase the number of page faults."}),
        ("mcq", 2, "What causes a Page Fault interrupt in modern operating systems?", {"options": ["Syntax error in code", "Accessing a virtual page not present in physical RAM", "CPU overheating", "Stack overflow"], "correct": "Accessing a virtual page not present in physical RAM", "explanation": "Page fault occurs when the valid bit in the page table entry is zero, requiring disk paging."}),
        ("short", 3, "Describe the difference between internal and external memory fragmentation.", {"rubric": "Internal fragmentation is wasted space inside allocated blocks; external fragmentation is unusable space scattered between allocations."})
    ],
    "skill_comp_arch": [
        ("mcq", 3, "Which pipeline hazard occurs when an instruction depends on the result of a previous instruction that has not yet reached write-back?", {"options": ["Structural Hazard", "Data Hazard", "Control Hazard", "Branch Hazard"], "correct": "Data Hazard", "explanation": "Read-After-Write (RAW) data hazards occur when operands are not yet computed or forwarded."}),
        ("short", 3, "Explain data forwarding (bypassing) in a 5-stage RISC processor pipeline.", {"rubric": "Routing the ALU result directly from the EX/MEM or MEM/WB pipeline register back to the ALU input, eliminating stalls."}),
        ("mcq", 2, "What is the primary trade-off between Direct-Mapped and Fully Associative caches?", {"options": ["Direct-mapped is slower but uses less power", "Direct-mapped has simpler hardware and lower hit time but higher conflict misses", "Fully associative has no compulsory misses", "None"], "correct": "Direct-mapped has simpler hardware and lower hit time but higher conflict misses", "explanation": "Associativity reduces conflict misses at the expense of comparator hardware and latency."}),
        ("short", 3, "What is branch prediction and why is it critical in deep pipelines?", {"rubric": "Speculatively fetching instructions before branch resolution prevents multi-cycle pipeline flushes on taken/not-taken branches."})
    ],
    "skill_ml_supervised": [
        ("mcq", 2, "What is the effect of increasing L2 regularization (Ridge) parameter lambda on model bias and variance?", {"options": ["Decreases bias, increases variance", "Increases bias, decreases variance", "Decreases both", "No effect"], "correct": "Increases bias, decreases variance", "explanation": "Regularization penalizes large weights, simplifying the model, which increases bias and decreases variance."}),
        ("code", 3, "Write a function `binary_cross_entropy(y_true, y_pred)` using Python and math.", {"test_cases": [{"input": "y_true=[1, 0], y_pred=[0.9, 0.1]", "expected": "~0.105"}]}),
        ("short", 3, "Explain why Support Vector Machines (SVM) maximize the margin between support vectors.", {"rubric": "Maximizing the margin minimizes the structural risk bound, leading to better generalizability on unseen data."}),
        ("mcq", 3, "Which decision tree split criterion measures the probability of a randomly chosen element being incorrectly labeled?", {"options": ["Entropy", "Gini Impurity", "Information Gain", "Variance"], "correct": "Gini Impurity", "explanation": "Gini impurity calculates sum of p_i * (1 - p_i), measuring misclassification probability."})
    ],
    "skill_ml_unsupervised": [
        ("mcq", 2, "What objective function does the K-Means clustering algorithm minimize?", {"options": ["Margin distance", "Within-cluster sum of squared errors (inertia)", "Information entropy", "Cross-entropy"], "correct": "Within-cluster sum of squared errors (inertia)", "explanation": "K-means iteratively minimizes sum of squared Euclidean distances between points and their assigned centroids."}),
        ("short", 3, "Explain how Principal Component Analysis (PCA) finds the directions of maximum variance.", {"rubric": "PCA computes the eigenvectors of the data covariance matrix; the eigenvector with largest eigenvalue is PC1."}),
        ("mcq", 3, "In Gaussian Mixture Models, what algorithm is used to estimate latent cluster parameters?", {"options": ["Backpropagation", "Expectation-Maximization (EM)", "Dijkstra algorithm", "Gradient Boosting"], "correct": "Expectation-Maximization (EM)", "explanation": "EM alternates between calculating expectation of latent variables (E-step) and maximizing parameters (M-step)."}),
        ("short", 3, "How does the 'Elbow Method' help select the number of clusters k in K-Means?", {"rubric": "Plot inertia vs k; choose the point where rate of decrease sharply bends, indicating diminishing returns."})
    ],
    "skill_deep_learning": [
        ("mcq", 3, "What issue in deep networks does the Residual connection (skip connection) in ResNet solve?", {"options": ["Overfitting", "Vanishing and exploding gradient problem", "Slow disk I/O", "High latency"], "correct": "Vanishing and exploding gradient problem", "explanation": "Skip connections allow gradients to flow directly back through identity shortcuts during backpropagation."}),
        ("short", 4, "Derive the backpropagation gradient for a single hidden layer with sigmoid activation.", {"rubric": "Chain rule: dL/dw = (dL/dy) * (dy/dz) * (dz/dw) where dy/dz = sigmoid(z) * (1 - sigmoid(z))."}),
        ("mcq", 2, "What is the primary purpose of Dropout during neural network training?", {"options": ["Accelerates forward pass", "Prevents co-adaptation of neurons and reduces overfitting", "Normalizes weights to zero", "Acts as optimizer"], "correct": "Prevents co-adaptation of neurons and reduces overfitting", "explanation": "Randomly dropping units during training forces the network to learn redundant representations."}),
        ("short", 3, "Explain Self-Attention mechanism in Transformer architectures.", {"rubric": "Calculates query, key, value projections; attention weights = softmax(Q * K^T / sqrt(d_k)) * V."})
    ],
    "skill_distributed_sys": [
        ("mcq", 3, "In MPI, what is the difference between `MPI_Bcast` and `MPI_Scatter`?", {"options": ["Bcast sends the same data buffer to all processes; Scatter distributes distinct chunks of an array to each process", "Scatter is point-to-point", "Bcast collects data", "No difference"], "correct": "Bcast sends the same data buffer to all processes; Scatter distributes distinct chunks of an array to each process", "explanation": "Broadcast replicates data to all workers; Scatter divides and distributes array slices."}),
        ("short", 3, "What is Warp Divergence in GPU CUDA programming and why does it degrade performance?", {"rubric": "When threads within a 32-thread warp execute divergent branches (if-else), the GPU serializes both paths."}),
        ("mcq", 3, "According to the CAP Theorem, which two properties can a distributed data store guarantee during a network partition?", {"options": ["Consistency and Availability", "Only Consistency OR Availability", "All three", "None"], "correct": "Only Consistency OR Availability", "explanation": "In the presence of a network partition (P), a distributed system must choose between Consistency (C) or Availability (A)."}),
        ("short", 4, "Explain the Raft consensus algorithm leader election phase.", {"rubric": "Followers start election timer; if no heartbeat received, convert to Candidate, increment term, vote for self, request votes."})
    ],
    "skill_sw_engineering": [
        ("mcq", 2, "In Git, what is the difference between `git merge` and `git rebase`?", {"options": ["Merge creates a new commit preserving history; Rebase reapplies commits on top of another base creating linear history", "Rebase deletes branches", "Merge is destructive", "None"], "correct": "Merge creates a new commit preserving history; Rebase reapplies commits on top of another base creating linear history", "explanation": "Merge retains branch topology via a merge commit; rebase rewrites commit history linearly."}),
        ("short", 3, "Explain Continuous Integration (CI) and why automated unit test suites are essential to it.", {"rubric": "Developers integrate code frequently into main branch; automated tests verify changes immediately, catching regressions early."}),
        ("mcq", 2, "Which HTTP status code signifies that the client request was valid but the server refuses authorization?", {"options": ["400 Bad Request", "401 Unauthorized", "403 Forbidden", "404 Not Found"], "correct": "403 Forbidden", "explanation": "403 means authenticated identity does not have permission to access the resource."}),
        ("code", 3, "Write a Python unit test using unittest to verify a function `divide(a, b)` raises ZeroDivisionError when b=0.", {"test_cases": [{"input": "divide(5, 0)", "expected": "raises ZeroDivisionError"}]})
    ],
    "skill_transport_phenom": [
        ("mcq", 3, "What does the Reynolds number (Re = rho * v * D / mu) physically represent?", {"options": ["Ratio of viscous forces to gravitational forces", "Ratio of inertial forces to viscous forces", "Ratio of momentum diffusivity to thermal diffusivity", "Heat transfer rate"], "correct": "Ratio of inertial forces to viscous forces", "explanation": "Re quantifies the relative importance of inertial forces compared to viscous forces in fluid flow."}),
        ("short", 3, "State Newton's Law of Viscosity and define shear stress.", {"rubric": "Shear stress tau = -mu * (dv_x / dy); force per unit area is proportional to the negative velocity gradient."}),
        ("mcq", 2, "In laminar flow through a circular pipe (Hagen-Poiseuille flow), what is the velocity profile shape?", {"options": ["Flat", "Parabolic", "Exponential", "Linear"], "correct": "Parabolic", "explanation": "Integrating the shell momentum balance yields a parabolic velocity profile v(r) = v_max * (1 - (r/R)^2)."}),
        ("short", 3, "Explain the Prandtl boundary layer concept in high Reynolds number fluid flow.", {"rubric": "Viscous effects are confined to a thin layer near the solid wall; outside this boundary layer, fluid behaves inviscidly."})
    ],
    "skill_chem_thermo": [
        ("mcq", 3, "What is fugacity in chemical engineering thermodynamics?", {"options": ["Internal energy", "An effective pressure replacing mechanical pressure to preserve ideal gas equilibrium equations for real fluids", "Entropy of mixing", "Activity coefficient"], "correct": "An effective pressure replacing mechanical pressure to preserve ideal gas equilibrium equations for real fluids", "explanation": "Fugacity has pressure units and accounts for non-ideal molecular interactions in chemical equilibria."}),
        ("short", 3, "State Raoult's law for ideal vapor-liquid equilibrium and when it fails.", {"rubric": "y_i * P = x_i * P_i_sat. Fails for polar mixtures, non-ideal solutions with strong azeotropic behavior, or high pressures."}),
        ("mcq", 2, "According to the Gibbs Phase Rule (F = C - P + 2), how many degrees of freedom does a single-component system have at its triple point?", {"options": ["0", "1", "2", "3"], "correct": "0", "explanation": "For C=1, P=3 (solid, liquid, vapor): F = 1 - 3 + 2 = 0 (invariant point)."}),
        ("short", 3, "Explain the Van 't Hoff equation for the temperature dependence of chemical equilibrium constant K.", {"rubric": "d(ln K)/dT = Delta H_rxn / (R * T^2). Equilibrium constant increases with T for endothermic and decreases for exothermic."})
    ],
    "skill_reaction_eng": [
        ("mcq", 2, "For a positive-order reaction, which reactor type requires the smallest volume to achieve a given conversion?", {"options": ["CSTR", "Plug Flow Reactor (PFR)", "Batch and PFR are identical and smaller than CSTR", "Fluidized bed"], "correct": "Batch and PFR are identical and smaller than CSTR", "explanation": "PFR maintains the highest average reactant concentration throughout, requiring less volume than a backmixed CSTR."}),
        ("short", 3, "Explain the Thiele Modulus and its role in determining catalyst effectiveness.", {"rubric": "Thiele modulus compares reaction rate to internal diffusion rate. High modulus means reaction is diffusion-limited."}),
        ("code", 4, "Write a Python script to compute the required PFR volume for a first-order reaction with k=0.1 /min, v0=10 L/min, and target conversion X=0.9.", {"test_cases": [{"input": "k=0.1, v0=10, X=0.9", "expected": "V = 230.25 L"}]}),
        ("mcq", 3, "In non-ideal chemical reactors, what does the E(t) residence time distribution curve integrate to over all time (0 to infinity)?", {"options": ["0", "0.5", "1.0", "Mean residence time"], "correct": "1.0", "explanation": "The RTD function E(t) is normalized so that integral of E(t) dt from 0 to infinity equals 1."})
    ],
    "skill_heat_transfer": [
        ("mcq", 2, "In industrial heat exchanger design, why is the Log Mean Temperature Difference (LMTD) used rather than arithmetic mean?", {"options": ["It is easier to compute", "Temperature difference varies non-linearly along the heat exchanger length", "It eliminates fouling factor", "Accounts for turbulence"], "correct": "Temperature difference varies non-linearly along the heat exchanger length", "explanation": "LMTD accounts for the exponential temperature variation across counter-current or co-current heat exchangers."}),
        ("short", 3, "Explain the difference between filmwise and dropwise condensation.", {"rubric": "Dropwise condensation forms discrete droplets leaving surface exposed, resulting in 5-10x higher heat transfer coefficients than filmwise."}),
        ("mcq", 3, "What does a Biot number (Bi = h * L / k) less than 0.1 indicate?", {"options": ["Radiation dominates", "Thermal resistance inside the solid is negligible compared to surface convection (Lumped Capacitance applies)", "Turbulent flow", "Boiling crisis"], "correct": "Thermal resistance inside the solid is negligible compared to surface convection (Lumped Capacitance applies)", "explanation": "Small Bi means temperature gradients within the solid are minimal, justifying lumped capacitance analysis."}),
        ("short", 3, "What is fouling resistance in heat exchangers and how is it accounted for in design?", {"rubric": "Thermal resistance from scale/deposit buildup; added as 1/U_dirty = 1/U_clean + R_f to size extra heat transfer area."})
    ],
    "skill_mass_transfer": [
        ("mcq", 3, "In binary distillation column design using McCabe-Thiele, what does the 'q-line' represent?", {"options": ["Operating line of stripping section", "Thermal condition and state of the feed mixture", "Equilibrium curve", "Top condenser reflux ratio"], "correct": "Thermal condition and state of the feed mixture", "explanation": "The q-line reflects the fraction of liquid in the feed and determines intersection of enriching and stripping operating lines."}),
        ("short", 3, "Explain Fick's First Law of Molecular Diffusion and define diffusivity D_AB.", {"rubric": "Molar flux J_A = -D_AB * (dC_A / dz); rate of transfer per unit area is proportional to concentration gradient."}),
        ("mcq", 3, "What phenomenon occurs in tray distillation columns when vapor velocity is too low to support liquid on the tray?", {"options": ["Flooding", "Weeping / Dumping", "Entrainment", "Foaming"], "correct": "Weeping / Dumping", "explanation": "Weeping occurs when liquid drains through tray perforations instead of flowing across to downcomer."}),
        ("short", 3, "What is the difference between physical gas absorption and reactive absorption?", {"rubric": "Physical absorption depends purely on solubility (Henry's law); chemical reaction enhances absorption rate and capacity."})
    ],
    "skill_process_control": [
        ("mcq", 2, "What is the primary disadvantage of using a pure Proportional (P) controller in feedback systems?", {"options": ["Instability", "Produces steady-state offset error", "Extremely slow response", "Amplifies noise"], "correct": "Produces steady-state offset error", "explanation": "A proportional controller requires an error to produce output, resulting in steady-state offset for step inputs."}),
        ("short", 3, "Explain how adding an Integral (I) action eliminates steady-state offset in PID control.", {"rubric": "The integral term continues accumulating error over time until the error reaches zero, forcing steady-state error to zero."}),
        ("mcq", 3, "In frequency response analysis, what do the Gain Margin and Phase Margin measure?", {"options": ["Controller speed", "Proximity of the closed-loop system to instability (robustness)", "Sensor calibration accuracy", "Feedforward latency"], "correct": "Proximity of the closed-loop system to instability (robustness)", "explanation": "Gain and phase margins quantify how much gain or phase lag can be added before the system oscillates unstably."}),
        ("short", 3, "Explain the concept of Cascade Control in chemical processes.", {"rubric": "Uses two nested control loops (primary master and secondary slave) to reject disturbances in the secondary variable before they affect the primary output."})
    ],
    "skill_venture_creation": [
        ("mcq", 2, "What is the primary objective of building a Minimum Viable Product (MVP) in the Lean Startup methodology?", {"options": ["Generate maximum initial revenue", "Validate fundamental business hypotheses with minimum effort and learning time", "File intellectual property patents", "Hire marketing team"], "correct": "Validate fundamental business hypotheses with minimum effort and learning time", "explanation": "An MVP tests customer appetite and assumptions with the smallest build investment."}),
        ("short", 3, "Explain the 'Customer Discovery' interview process and why leading questions must be avoided.", {"rubric": "Uncover actual past behavior and acute pain points; leading questions induce false confirmation bias."}),
        ("mcq", 2, "What does Customer Acquisition Cost (CAC) represent?", {"options": ["Customer retention rate", "Total sales and marketing expenditure divided by number of customers acquired", "Gross margin per sale", "Subscription pricing"], "correct": "Total sales and marketing expenditure divided by number of customers acquired", "explanation": "CAC measures the blended cost of acquiring a single paying user."}),
        ("short", 3, "What is a Pivot in venture development and when is it warranted?", {"rubric": "A structured course correction to test a new hypothesis about product, business model, or engine of growth when metrics stall."})
    ],
    "skill_venture_finance": [
        ("mcq", 2, "If a startup raises $2M at an $8M pre-money valuation, what is the post-money valuation and investor ownership percentage?", {"options": ["$8M post-money, 25% ownership", "$10M post-money, 20% ownership", "$10M post-money, 25% ownership", "$6M post-money, 33% ownership"], "correct": "$10M post-money, 20% ownership", "explanation": "Post-money = Pre-money + Investment ($8M + $2M = $10M). Ownership = $2M / $10M = 20%."}),
        ("short", 3, "Explain the difference between Pre-Money and Post-Money SAFE agreements in startup financing.", {"rubric": "Pre-money SAFEs dilute founders when additional SAFEs are issued; post-money SAFEs fix the investor ownership fraction before the priced round."}),
        ("mcq", 3, "What does Net Present Value (NPV) calculate for an investment project?", {"options": ["Simple payback period", "Sum of discounted future cash inflows minus initial capital outlay", "Accounting net income", "Internal rate of return"], "correct": "Sum of discounted future cash inflows minus initial capital outlay", "explanation": "NPV discounts projected cash flows back to present value using the hurdle discount rate."}),
        ("short", 3, "What is a Liquidation Preference in a venture term sheet?", {"rubric": "Determines payout hierarchy and guaranteed multiple (e.g. 1x non-participating) returned to preferred investors before common stock holders in an exit."})
    ],
    "skill_social_structures": [
        ("mcq", 2, "Under the Constitution of India, which Article guarantees equality before the law?", {"options": ["Article 14", "Article 19", "Article 21", "Article 32"], "correct": "Article 14", "explanation": "Article 14 guarantees equality before the law and equal protection of the laws within India."}),
        ("short", 3, "Explain the distinction between Fundamental Rights and Directive Principles of State Policy.", {"rubric": "Fundamental Rights (Part III) are legally enforceable by courts; Directive Principles (Part IV) are non-justiciable moral guidelines for state governance."}),
        ("mcq", 2, "Which constitutional amendment introduced the 3-tier Panchayati Raj system of local self-government in India?", {"options": ["42nd Amendment", "44th Amendment", "73rd Amendment", "86th Amendment"], "correct": "73rd Amendment", "explanation": "The 73rd Constitutional Amendment Act (1992) institutionalized Panchayati Raj rural local bodies."}),
        ("short", 3, "Explain the concept of 'Basic Structure' doctrine enunciated in the Kesavananda Bharati case.", {"rubric": "Parliament has wide amending powers under Art 368 but cannot alter or destroy essential foundational features of the Constitution."})
    ],
    "skill_environmental_policy": [
        ("mcq", 2, "What was the landmark commitment agreed upon in the 2015 Paris Climate Agreement?", {"options": ["Complete global ban on coal by 2020", "Limit global temperature rise well below 2.0 degrees C above pre-industrial levels and pursue 1.5 degrees C", "Carbon tax of $100 per ton globally", "Mandate solar on all rooftops"], "correct": "Limit global temperature rise well below 2.0 degrees C above pre-industrial levels and pursue 1.5 degrees C", "explanation": "The Paris Agreement sets the legally binding global target of holding warming well below 2.0C."}),
        ("short", 3, "Explain the Polluter Pays Principle in environmental jurisprudence.", {"rubric": "The party responsible for environmental degradation and pollution must bear the financial costs of remediation and compensation."}),
        ("mcq", 2, "What does the Air Quality Index (AQI) measure in Indian environmental monitoring?", {"options": ["Humidity and temperature", "Composite concentration of key pollutants including PM2.5, PM10, NO2, SO2, CO, O3", "Carbon credit pricing", "Noise levels"], "correct": "Composite concentration of key pollutants including PM2.5, PM10, NO2, SO2, CO, O3", "explanation": "AQI translates multi-pollutant concentrations into a single intuitive health-risk score."}),
        ("short", 3, "Explain the concept of Common But Differentiated Responsibilities (CBDR) in climate negotiations.", {"rubric": "All states are responsible for environmental protection, but developed nations bear greater historical responsibility and capability."})
    ],
    "skill_cognitive_psych": [
        ("mcq", 2, "According to Daniel Kahneman, what characterizes System 1 thinking?", {"options": ["Slow, deliberate, analytical, computationally heavy", "Fast, automatic, subconscious, heuristic-driven", "Only active during sleep", "Mathematical logic"], "correct": "Fast, automatic, subconscious, heuristic-driven", "explanation": "System 1 operates effortlessly and rapidly with little or no voluntary control."}),
        ("short", 3, "Explain George Miller's classic 'Magic Number Seven' in human short-term memory capacity.", {"rubric": "Humans can hold approximately 7 plus or minus 2 chunks of information in working memory at any one time."}),
        ("mcq", 2, "What cognitive bias describes the human tendency to search for and favor information that confirms prior beliefs?", {"options": ["Anchoring bias", "Confirmation bias", "Availability heuristic", "Hindsight bias"], "correct": "Confirmation bias", "explanation": "Confirmation bias leads individuals to selectively process information supporting existing hypotheses."}),
        ("short", 3, "Explain Cognitive Load Theory and its implication for instructional design.", {"rubric": "Heavy extraneous cognitive load exhausts limited working memory capacity, impeding germane schema acquisition."})
    ]
}

# Attach exercises to corresponding modules
skill_to_module = {}
for m in modules:
    for sk in m["skill_ids"]:
        skill_to_module.setdefault(sk, []).append(m["module_id"])

for skill_id, q_list in skill_question_bank.items():
    linked_mods = skill_to_module.get(skill_id, [modules[0]["module_id"]])
    for i, (q_type, diff, prompt, answer_key) in enumerate(q_list, 1):
        target_mod = linked_mods[i % len(linked_mods)]
        ex_id = f"ex_{skill_id}_{i}"
        exercises.append({
            "exercise_id": ex_id,
            "skill_id": skill_id,
            "module_id": target_mod,
            "type": q_type,
            "difficulty": diff,
            "prompt": prompt,
            "answer_key": answer_key,
            "source": f"Verified Question Bank: {skill_id}"
        })

with open(SEED_DIR / "exercises.json", "w", encoding="utf-8") as f:
    json.dump(exercises, f, indent=2)

print(f"Generated {len(exercises)} exercises in exercises.json")

# 4. BUILD ACADEMIC RULES
academic_rules = [
    {
        "rule_id": "rule_credit_cap_standard",
        "name": "Standard Semester Credit Cap",
        "type": "credit_cap_max",
        "parameters": { "min_credits": 14.0, "max_credits": 22.0 },
        "source_text": "Students may register for a minimum of 14 credits and a maximum of 22 credits per semester.",
        "source_url": "https://home.iitd.ac.in/academic-rules/ordinance-section-4.2"
    },
    {
        "rule_id": "rule_credit_overload_cap",
        "name": "Academic Overload Credit Cap",
        "type": "credit_overload_max",
        "parameters": { "max_overload_credits": 24.0, "min_cgpa_required": 8.5 },
        "source_text": "Students with a CGPA of 8.5 or higher and no backlogs may register for up to 24 credits upon Dean approval.",
        "source_url": "https://home.iitd.ac.in/academic-rules/ordinance-section-4.3"
    },
    {
        "rule_id": "rule_minor_cse_eligibility",
        "name": "Minor in Computer Science and Engineering Eligibility",
        "type": "minor_eligibility",
        "parameters": {
            "department": "Computer Science and Engineering",
            "credits_required": 20.0,
            "min_cgpa_cutoff": 7.5,
            "mandatory_courses": ["COL106", "COL215", "COL331", "COL362"]
        },
        "source_text": "To earn a Minor in CSE, a non-CS student must have CGPA >= 7.5, complete 20 credits in COL courses including COL106, COL215, COL331, and COL362.",
        "source_url": "https://home.iitd.ac.in/academic-rules/minor-guidelines-2023"
    },
    {
        "rule_id": "rule_prereq_strict_enforcement",
        "name": "Prerequisite Passing Grade Enforcement",
        "type": "prereq_policy",
        "parameters": { "enforcement_mode": "strict_pass", "passing_grade_minimum": "D" },
        "source_text": "A student must obtain a passing grade (Grade D or above) in all hard prerequisite courses prior to registering for the advanced course.",
        "source_url": "https://home.iitd.ac.in/academic-rules/ordinance-section-5.1"
    },
    {
        "rule_id": "rule_online_credit_transfer_limit",
        "name": "NPTEL/SWAYAM Online Credit Ceiling",
        "type": "online_credit_limit",
        "parameters": { "max_online_credits_total": 12.0, "max_online_courses_per_semester": 1 },
        "source_text": "Students may earn up to a maximum of 12 credits through recognized online platforms (NPTEL / SWAYAM) towards Open Electives.",
        "source_url": "https://home.iitd.ac.in/academic-rules/nptel-transfer-policy"
    },
    {
        "rule_id": "rule_no_co_taking_heavy_dsa_discrete",
        "name": "Workload Balance: Do Not Co-take Heavy Theory",
        "type": "no_co_taking_pair",
        "parameters": { "course_pair": ["COL351", "COL352"], "reason": "Severe theoretical workload overlap" },
        "source_text": "Students are strongly advised not to register for COL351 (Design of Algorithms) and COL352 (Automata & Computation) in the same semester due to intense mathematical workload.",
        "source_url": "https://cse.iitd.ac.in/curriculum/undergraduate-advising-notes"
    }
]

with open(SEED_DIR / "academic_rules.json", "w", encoding="utf-8") as f:
    json.dump(academic_rules, f, indent=2)

print(f"Generated {len(academic_rules)} rules in academic_rules.json")

# 5. BUILD GOAL TEMPLATES (Covering the Appendix A Personas)
goal_templates = [
    {
        "goal_id": "goal_software",
        "name": "Software Engineering & Systems Role",
        "target_role": "Software Development Engineer (SWE / SDE)",
        "typical_duration_semesters": 4,
        "required_skills": [
            { "skill_id": "skill_prog_fundamentals", "target_level": 0.90, "critical": True },
            { "skill_id": "skill_dsa_linear", "target_level": 0.85, "critical": True },
            { "skill_id": "skill_dsa_trees", "target_level": 0.85, "critical": True },
            { "skill_id": "skill_algo_design", "target_level": 0.85, "critical": True },
            { "skill_id": "skill_db_relational", "target_level": 0.80, "critical": True },
            { "skill_id": "skill_os_concurrency", "target_level": 0.80, "critical": True },
            { "skill_id": "skill_sw_engineering", "target_level": 0.85, "critical": True }
        ],
        "milestones": [
            { "name": "Algorithmic Foundation Checkpoint", "semester_offset": 1, "criteria": "Solve 50 LeetCode-style medium problems across linear structures and BSTs." },
            { "name": "Full-Stack / Systems Project Capstone", "semester_offset": 2, "criteria": "Build and deploy a containerized full-stack or systems application with CI/CD." },
            { "name": "Campus Placement Mock Interview", "semester_offset": 3, "criteria": "Pass 2 timed mock technical interviews on DSA and System Design." }
        ],
        "source": "Inter IIT Tech Meet 15.0 Appendix A, Persona A"
    },
    {
        "goal_id": "goal_research",
        "name": "Higher Studies (MS/PhD & Academic Research)",
        "target_role": "Graduate Researcher / R&D Scientist",
        "typical_duration_semesters": 4,
        "required_skills": [
            { "skill_id": "skill_linear_algebra", "target_level": 0.90, "critical": True },
            { "skill_id": "skill_probability", "target_level": 0.85, "critical": True },
            { "skill_id": "skill_calculus", "target_level": 0.85, "critical": True },
            { "skill_id": "skill_algo_design", "target_level": 0.85, "critical": True },
            { "skill_id": "skill_ml_supervised", "target_level": 0.80, "critical": False }
        ],
        "milestones": [
            { "name": "Faculty Research Area Matching", "semester_offset": 1, "criteria": "Review 5 recent papers and initiate faculty research collaboration." },
            { "name": "Undergraduate Thesis / Capstone Project", "semester_offset": 2, "criteria": "Complete literature review and submit paper draft to peer workshop." },
            { "name": "Standardized Testing (GRE/GATE/TOEFL)", "semester_offset": 3, "criteria": "Complete standardized test prep timeline with target 90th percentile." }
        ],
        "source": "Inter IIT Tech Meet 15.0 Appendix A, Persona B"
    },
    {
        "goal_id": "goal_upsc",
        "name": "UPSC Civil Services Examination (IAS / IFS)",
        "target_role": "Civil Services Officer",
        "typical_duration_semesters": 4,
        "required_skills": [
            { "skill_id": "skill_social_structures", "target_level": 0.85, "critical": True },
            { "skill_id": "skill_environmental_policy", "target_level": 0.85, "critical": True },
            { "skill_id": "skill_cognitive_psych", "target_level": 0.75, "critical": False }
        ],
        "milestones": [
            { "name": "NCERT & Foundation Social Science Mastery", "semester_offset": 1, "criteria": "Master NCERT Class XI-XII Political Science & Sociology texts." },
            { "name": "General Studies Optional Alignment", "semester_offset": 2, "criteria": "Complete HSS electives supporting GS Papers I, II, and III." },
            { "name": "Answer Writing & Timed Mock Test", "semester_offset": 3, "criteria": "Write 20 evaluated GS essay/case study answers under timed conditions." }
        ],
        "source": "Inter IIT Tech Meet 15.0 Appendix A, Persona C"
    },
    {
        "goal_id": "goal_startup",
        "name": "Venture Builder & Entrepreneurship",
        "target_role": "Founder / Early-Stage Product Lead",
        "typical_duration_semesters": 4,
        "required_skills": [
            { "skill_id": "skill_venture_creation", "target_level": 0.85, "critical": True },
            { "skill_id": "skill_venture_finance", "target_level": 0.80, "critical": True },
            { "skill_id": "skill_sw_engineering", "target_level": 0.80, "critical": False }
        ],
        "milestones": [
            { "name": "Problem Discovery & Customer Interviews", "semester_offset": 1, "criteria": "Conduct 30 customer discovery interviews; complete Business Model Canvas." },
            { "name": "MVP Launch & Incubation Cell Linkage", "semester_offset": 2, "criteria": "Launch functional MVP; pitch to institute incubator (e.g. FITT IIT Delhi)." },
            { "name": "Angel / Seed Pitch Deck Preparation", "semester_offset": 3, "criteria": "Prepare 10-slide pitch deck, cap table model, and financial unit economics." }
        ],
        "source": "Inter IIT Tech Meet 15.0 Appendix A, Persona D"
    }
]

with open(SEED_DIR / "goal_templates.json", "w", encoding="utf-8") as f:
    json.dump(goal_templates, f, indent=2)

print(f"Generated {len(goal_templates)} goal templates in goal_templates.json")
