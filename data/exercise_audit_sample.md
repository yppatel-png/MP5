# Human Review Audit: 20 Random Assessment Items

This audit sample presents 20 randomly selected exercises across skills and difficulty tiers for human spot-checking.

| # | Exercise ID | Skill | Module | Type | Diff | Source Page | Prompt | Correct Answer |
|---|-------------|-------|--------|------|------|-------------|--------|----------------|
| 1 | `ex_comm_04` | `communication` | `mod_csq401_3` | `mcq` | 2 | p. 87 | During collaborative software code reviews, how should actio... | Objective, respectful, and focused  |
| 2 | `ex_dm_09` | `discrete_mathematics` | `mod_csl201_4` | `mcq` | 4 | p. 83 | What is the coefficient of x^3 in the expansion of (2x - 1)^... | 80 |
| 3 | `ex_prog_07` | `programming_fundamentals` | `mod_csl100_4` | `mcq` | 3 | p. 83 | In C memory layout, dynamically allocated memory via malloc(... | Heap |
| 4 | `ex_macro_10` | `macroeconomics` | `mod_lal200_2` | `mcq` | 4 | p. 137 | According to the Classical Quantity Theory of Money (M * V =... | The price level P exactly doubles,  |
| 5 | `ex_os_01` | `operating_systems` | `mod_csl301_1` | `mcq` | 1 | p. 84 | What state does a running process enter when it executes a b... | Waiting / Blocked state |
| 6 | `ex_toc_03` | `theory_computation` | `mod_csl253_2` | `mcq` | 2 | p. 84 | What is the computational equivalence between Non-determinis... | NFAs and DFAs recognize the exact s |
| 7 | `ex_arch_08` | `computer_architecture` | `mod_ecl101_3` | `mcq` | 3 | p. 21 | Which cache replacement policy evicts the block that has rem... | Least Recently Used (LRU) |
| 8 | `ex_ds_06` | `data_structures` | `mod_csl202_2` | `mcq` | 3 | p. 83 | What is the permitted balance factor range for every node in... | {-1, 0, 1} |
| 9 | `ex_macro_09` | `macroeconomics` | `mod_lal200_3` | `mcq` | 4 | p. 137 | What economic phenomenon occurs when massive government defi... | Crowding-out effect |
| 10 | `ex_dm_07` | `discrete_mathematics` | `mod_csl201_3` | `mcq` | 3 | p. 83 | How many edges does a connected tree with 50 vertices have? | 49 |
| 11 | `ex_fin_04` | `finance` | `mod_lal101_2` | `mcq` | 2 | p. 136 | In corporate capital budgeting, what is the decision rule fo... | Accept the capital investment proje |
| 12 | `ex_lit_09` | `literary_analysis` | `mod_lal221_3` | `mcq` | 4 | p. 138 | In literary theorist Mikhail Bakhtin's analysis of the novel... | A plurality of independent and unme |
| 13 | `ex_llm_10` | `llm_software` | `mod_csp352_4` | `mcq` | 4 | p. 86 | How does Low-Rank Adaptation (LoRA) enable parameter-efficie... | Constrains weight updates to a low- |
| 14 | `ex_dm_03` | `discrete_mathematics` | `mod_csl201_2` | `mcq` | 2 | p. 83 | A binary relation R on set A is an equivalence relation if a... | Reflexive, symmetric, and transitiv |
| 15 | `ex_prob_02` | `probability_statistics` | `mod_mal403_1` | `mcq` | 1 | p. 21 | What is the sum of probabilities across all mutually exclusi... | 1.0 |
| 16 | `ex_ai_09` | `artificial_intelligence` | `mod_csl304_2` | `mcq` | 4 | p. 85 | In Constraint Satisfaction Problems (CSPs), what constraint ... | AC-3 (Arc Consistency Algorithm #3) |
| 17 | `ex_prog_09` | `programming_fundamentals` | `mod_csl100_3` | `mcq` | 4 | p. 83 | What happens when free(ptr) is called twice on the same allo... | Double free vulnerability / runtime |
| 18 | `ex_prog_08` | `programming_fundamentals` | `mod_csl100_4` | `code` | 3 | p. 83 | Write a function is_palindrome(s) that returns 1 if string s... | palindrome checker |
| 19 | `ex_dm_04` | `discrete_mathematics` | `mod_csl201_2` | `short` | 2 | p. 83 | In how many distinct ways can 4 books be arranged on a shelf... | 840 |
| 20 | `ex_arch_06` | `computer_architecture` | `mod_ecl101_3` | `mcq` | 3 | p. 21 | In a direct-mapped cache, how is a memory address partitione... | Tag, Index, and Block Offset |

## Detailed Item Inspector

### Item 1: `ex_comm_04` (communication)
- **Module**: `mod_csq401_3` (Courses of Study p. 87)
- **Type**: `mcq` | **Difficulty**: 2 / 4
- **Prompt**:
  > During collaborative software code reviews, how should actionable technical feedback be framed?
- **Options**:
  - [x] Objective, respectful, and focused on code artifacts, maintainability, and standards rather than personal critique
  - [ ] Demanding immediate rewriting without providing rationale
  - [ ] Focusing exclusively on stylistic preferences
  - [ ] Rejecting pull requests without explanatory commentary
- **Correct Answer**: `Objective, respectful, and focused on code artifacts, maintainability, and standards rather than personal critique`
- **Explanation**: Constructive code reviews critique implementation decisions with explanatory rationale and suggestions, fostering team growth.

### Item 2: `ex_dm_09` (discrete_mathematics)
- **Module**: `mod_csl201_4` (Courses of Study p. 83)
- **Type**: `mcq` | **Difficulty**: 4 / 4
- **Prompt**:
  > What is the coefficient of x^3 in the expansion of (2x - 1)^5 using the Binomial Theorem?
- **Options**:
  - [x] 80
  - [ ] -80
  - [ ] 40
  - [ ] -40
- **Correct Answer**: `80`
- **Explanation**: The term is C(5, 3) * (2x)^3 * (-1)^(5-3) = 10 * 8x^3 * 1 = 80x^3. So coefficient is 80.

### Item 3: `ex_prog_07` (programming_fundamentals)
- **Module**: `mod_csl100_4` (Courses of Study p. 83)
- **Type**: `mcq` | **Difficulty**: 3 / 4
- **Prompt**:
  > In C memory layout, dynamically allocated memory via malloc() resides in which memory segment?
- **Options**:
  - [ ] Stack
  - [x] Heap
  - [ ] BSS segment
  - [ ] Text segment
- **Correct Answer**: `Heap`
- **Explanation**: malloc() allocates memory from the process heap segment; local variables reside on the call stack.

### Item 4: `ex_macro_10` (macroeconomics)
- **Module**: `mod_lal200_2` (Courses of Study p. 137)
- **Type**: `mcq` | **Difficulty**: 4 / 4
- **Prompt**:
  > According to the Classical Quantity Theory of Money (M * V = P * Y), what consequence occurs if the money supply M doubles while velocity V and real output Y remain constant?
- **Options**:
  - [x] The price level P exactly doubles, causing 100% inflation
  - [ ] Real output Y doubles
  - [ ] Velocity V drops to zero
  - [ ] Interest rates turn negative
- **Correct Answer**: `The price level P exactly doubles, causing 100% inflation`
- **Explanation**: With constant transaction velocity and real production capacity, money supply growth translates directly into proportional price inflation.

### Item 5: `ex_os_01` (operating_systems)
- **Module**: `mod_csl301_1` (Courses of Study p. 84)
- **Type**: `mcq` | **Difficulty**: 1 / 4
- **Prompt**:
  > What state does a running process enter when it executes a blocking read() system call?
- **Options**:
  - [x] Waiting / Blocked state
  - [ ] Ready state
  - [ ] Terminated state
  - [ ] Zombie state
- **Correct Answer**: `Waiting / Blocked state`
- **Explanation**: When awaiting an I/O event or resource, the kernel transitions the process to the Waiting/Blocked queue.

### Item 6: `ex_toc_03` (theory_computation)
- **Module**: `mod_csl253_2` (Courses of Study p. 84)
- **Type**: `mcq` | **Difficulty**: 2 / 4
- **Prompt**:
  > What is the computational equivalence between Non-deterministic Finite Automata (NFA) and Deterministic Finite Automata (DFA)?
- **Options**:
  - [x] NFAs and DFAs recognize the exact same class of regular languages
  - [ ] NFAs can recognize non-regular languages that DFAs cannot
  - [ ] DFAs are strictly more powerful than NFAs
  - [ ] NFAs can recognize context-free languages
- **Correct Answer**: `NFAs and DFAs recognize the exact same class of regular languages`
- **Explanation**: Via the subset construction algorithm, any NFA with n states can be converted into an equivalent DFA with at most 2^n states.

### Item 7: `ex_arch_08` (computer_architecture)
- **Module**: `mod_ecl101_3` (Courses of Study p. 21)
- **Type**: `mcq` | **Difficulty**: 3 / 4
- **Prompt**:
  > Which cache replacement policy evicts the block that has remained unreferenced for the longest elapsed time?
- **Options**:
  - [x] Least Recently Used (LRU)
  - [ ] First-In-First-Out (FIFO)
  - [ ] Random Replacement
  - [ ] Most Recently Used (MRU)
- **Correct Answer**: `Least Recently Used (LRU)`
- **Explanation**: LRU exploits temporal locality by discarding items not accessed for the longest period.

### Item 8: `ex_ds_06` (data_structures)
- **Module**: `mod_csl202_2` (Courses of Study p. 83)
- **Type**: `mcq` | **Difficulty**: 3 / 4
- **Prompt**:
  > What is the permitted balance factor range for every node in an AVL tree?
- **Options**:
  - [x] {-1, 0, 1}
  - [ ] {-2, -1, 0, 1, 2}
  - [ ] {0, 1}
  - [ ] {-1, 1}
- **Correct Answer**: `{-1, 0, 1}`
- **Explanation**: An AVL tree maintains height balance such that height(left) - height(right) is in {-1, 0, 1} for every node.

### Item 9: `ex_macro_09` (macroeconomics)
- **Module**: `mod_lal200_3` (Courses of Study p. 137)
- **Type**: `mcq` | **Difficulty**: 4 / 4
- **Prompt**:
  > What economic phenomenon occurs when massive government deficit borrowing increases market interest rates, dampening private capital investment?
- **Options**:
  - [x] Crowding-out effect
  - [ ] Ricardian equivalence
  - [ ] Paradox of thrift
  - [ ] Balance sheet recession
- **Correct Answer**: `Crowding-out effect`
- **Explanation**: Heavy government bond issuance absorbs loanable funds, bidding up interest rates and crowding out private sector borrowers.

### Item 10: `ex_dm_07` (discrete_mathematics)
- **Module**: `mod_csl201_3` (Courses of Study p. 83)
- **Type**: `mcq` | **Difficulty**: 3 / 4
- **Prompt**:
  > How many edges does a connected tree with 50 vertices have?
- **Options**:
  - [x] 49
  - [ ] 50
  - [ ] 25
  - [ ] 100
- **Correct Answer**: `49`
- **Explanation**: Every tree with V vertices has exactly V - 1 edges. 50 - 1 = 49.

### Item 11: `ex_fin_04` (finance)
- **Module**: `mod_lal101_2` (Courses of Study p. 136)
- **Type**: `mcq` | **Difficulty**: 2 / 4
- **Prompt**:
  > In corporate capital budgeting, what is the decision rule for the Net Present Value (NPV) criterion?
- **Options**:
  - [x] Accept the capital investment project if NPV > 0
  - [ ] Accept only projects with NPV < 0
  - [ ] Accept projects where NPV equals initial cost
  - [ ] Reject projects with positive cash flows
- **Correct Answer**: `Accept the capital investment project if NPV > 0`
- **Explanation**: An NPV > 0 signifies that the project generates discounted cash flows exceeding the cost of capital, adding value to the firm.

### Item 12: `ex_lit_09` (literary_analysis)
- **Module**: `mod_lal221_3` (Courses of Study p. 138)
- **Type**: `mcq` | **Difficulty**: 4 / 4
- **Prompt**:
  > In literary theorist Mikhail Bakhtin's analysis of the novel, what does 'Polyphony' (Dialogism) signify?
- **Options**:
  - [x] A plurality of independent and unmerged voices and worldviews interacting democratically without total authorial subordination
  - [ ] The musical accompaniment performed during theatrical readings
  - [ ] Rhyming schemes occurring at the center of poetic lines
  - [ ] The translation of a novel into multiple world languages
- **Correct Answer**: `A plurality of independent and unmerged voices and worldviews interacting democratically without total authorial subordination`
- **Explanation**: Bakhtin identified polyphony (e.g. in Dostoevsky) where characters possess distinct autonomous consciousnesses beyond the author's voice.

### Item 13: `ex_llm_10` (llm_software)
- **Module**: `mod_csp352_4` (Courses of Study p. 86)
- **Type**: `mcq` | **Difficulty**: 4 / 4
- **Prompt**:
  > How does Low-Rank Adaptation (LoRA) enable parameter-efficient fine-tuning of large pre-trained weight matrices W_0 in R^(d x k)?
- **Options**:
  - [x] Constrains weight updates to a low-rank decomposition delta_W = B * A where B in R^(d x r) and A in R^(r x k) with r << min(d, k)
  - [ ] Quantizes all weights to 1-bit integers
  - [ ] Freezes the first half of the layers and prunes the second half
  - [ ] Applies singular value decomposition and truncates input prompts
- **Correct Answer**: `Constrains weight updates to a low-rank decomposition delta_W = B * A where B in R^(d x r) and A in R^(r x k) with r << min(d, k)`
- **Explanation**: LoRA freezes pre-trained weights W_0 and trains small low-rank adapter matrices A and B, drastically reducing trainable parameter counts.

### Item 14: `ex_dm_03` (discrete_mathematics)
- **Module**: `mod_csl201_2` (Courses of Study p. 83)
- **Type**: `mcq` | **Difficulty**: 2 / 4
- **Prompt**:
  > A binary relation R on set A is an equivalence relation if and only if it satisfies which three properties?
- **Options**:
  - [x] Reflexive, symmetric, and transitive
  - [ ] Reflexive, antisymmetric, and transitive
  - [ ] Irreflexive, symmetric, and transitive
  - [ ] Reflexive, symmetric, and total
- **Correct Answer**: `Reflexive, symmetric, and transitive`
- **Explanation**: By definition, an equivalence relation must be reflexive (aRa), symmetric (aRb => bRa), and transitive (aRb and bRc => aRc).

### Item 15: `ex_prob_02` (probability_statistics)
- **Module**: `mod_mal403_1` (Courses of Study p. 21)
- **Type**: `mcq` | **Difficulty**: 1 / 4
- **Prompt**:
  > What is the sum of probabilities across all mutually exclusive and collectively exhaustive outcomes in a valid sample space?
- **Options**:
  - [x] 1.0
  - [ ] 0.0
  - [ ] 100.0
  - [ ] Infinity
- **Correct Answer**: `1.0`
- **Explanation**: By Kolmogorov's second probability axiom, the total measure of the entire sample space S equals 1.0.

### Item 16: `ex_ai_09` (artificial_intelligence)
- **Module**: `mod_csl304_2` (Courses of Study p. 85)
- **Type**: `mcq` | **Difficulty**: 4 / 4
- **Prompt**:
  > In Constraint Satisfaction Problems (CSPs), what constraint propagation algorithm maintains directional consistency across all variable arcs?
- **Options**:
  - [x] AC-3 (Arc Consistency Algorithm #3)
  - [ ] Dijkstra's algorithm
  - [ ] Minimax with alpha-beta
  - [ ] K-means clustering
- **Correct Answer**: `AC-3 (Arc Consistency Algorithm #3)`
- **Explanation**: AC-3 iteratively prunes values from variable domains that have no valid supporting assignment in adjacent constrained variable domains.

### Item 17: `ex_prog_09` (programming_fundamentals)
- **Module**: `mod_csl100_3` (Courses of Study p. 83)
- **Type**: `mcq` | **Difficulty**: 4 / 4
- **Prompt**:
  > What happens when free(ptr) is called twice on the same allocated pointer without reallocation?
- **Options**:
  - [ ] Memory is reallocated
  - [x] Double free vulnerability / runtime crash
  - [ ] Safe no-op
  - [ ] Stack overflow
- **Correct Answer**: `Double free vulnerability / runtime crash`
- **Explanation**: Invoking free() twice on the same pointer is undefined behavior leading to heap corruption or abort.

### Item 18: `ex_prog_08` (programming_fundamentals)
- **Module**: `mod_csl100_4` (Courses of Study p. 83)
- **Type**: `code` | **Difficulty**: 3 / 4
- **Prompt**:
  > Write a function is_palindrome(s) that returns 1 if string s is a palindrome, otherwise 0.
- **Correct Answer**: `palindrome checker`
- **Explanation**: Compares characters from both ends inwards towards the middle.

### Item 19: `ex_dm_04` (discrete_mathematics)
- **Module**: `mod_csl201_2` (Courses of Study p. 83)
- **Type**: `short` | **Difficulty**: 2 / 4
- **Prompt**:
  > In how many distinct ways can 4 books be arranged on a shelf from a collection of 7 distinct books?
- **Correct Answer**: `840`
- **Explanation**: P(7, 4) = 7 * 6 * 5 * 4 = 840 distinct arrangements.

### Item 20: `ex_arch_06` (computer_architecture)
- **Module**: `mod_ecl101_3` (Courses of Study p. 21)
- **Type**: `mcq` | **Difficulty**: 3 / 4
- **Prompt**:
  > In a direct-mapped cache, how is a memory address partitioned into fields?
- **Options**:
  - [x] Tag, Index, and Block Offset
  - [ ] Tag and Offset only
  - [ ] Set, Page, and Offset
  - [ ] Base, Limit, and Offset
- **Correct Answer**: `Tag, Index, and Block Offset`
- **Explanation**: A direct-mapped cache address splits into Block Offset (within line), Index (selects line), and Tag (confirms identity).
