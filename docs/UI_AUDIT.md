# Comprehensive Frontend UI / UX Audit
**Standard:** "Quiet Academic Instrument" (Linear / Stripe / Vercel / Apple Health aesthetic)  
**Evaluated Codebase:** `frontend/index.html`, `frontend/static/css/style.css`, `frontend/static/js/app.js`  
**Date:** November 2026

---

## Executive Summary

The existing frontend suffers from prominent "AI-generated demo" tropes: heavy card wrappers on every element, high-saturation red/orange gradients, glassmorphism (`backdrop-filter`), excessive font weights (up to 900), inconsistent spacing and border radii (up to 16px), Title Case action verbs, unicode symbol decoration (`&bull;`, `&rarr;`, `&#9888;`), and a top tab navigation bar instead of an institutional, high-density left sidebar layout.

This audit catalogues every violation against Sections 1 through 8 of the design brief, grouped by severity.

---

## 1. Critical Violations (AI-Generated "Vibe-Coded" Tells)

### 1.1 Gradients, Glowing Elements & Glassmorphism
* **Violation:** Saturated multi-stop gradients and backdrop blur on panels.
* **Code References:**
  * `frontend/static/css/style.css:101`: `background: linear-gradient(135deg, #ef4444, #f97316);` on `.brand-badge`.
  * `frontend/static/css/style.css:91`: `backdrop-filter: blur(12px);` on `header.app-header`.
  * `frontend/index.html:67`: `box-shadow: 0 0 12px rgba(239, 68, 68, 0.5);` glowing colored drop shadow on active step dot.
* **Prescription:** Remove all gradients. Use flat `--accent` (`#C8341E`) with high-contrast text. Eliminate all backdrop blur filters; replace with solid `--surface` and 1px `--border` hairlines.

### 1.2 "Cards Everywhere" Pattern
* **Violation:** Almost every piece of information is wrapped inside an elevated `.card` container with border and drop-shadow, creating visual clutter and artificial visual weight.
* **Code References:**
  * `frontend/index.html:161, 194, 221, 249, 275, 296, 376, 380, 384, 388, 468, 504, 526, 564, 573, 601, 626, 670, 704`.
  * `frontend/static/css/style.css:151-163`: `.card { background-color: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); }`.
* **Prescription:** Replace arbitrary cards with clean typographic hierarchy, horizontal hairlines (`border-bottom: 1px solid var(--border)`), table structures, and generous whitespace. Reserve boxed containers only for distinct modal dialogs, slide-out panels, and interactive code sandboxes.

### 1.3 Rainbow Badges & Unsemantic Palette
* **Violation:** Badges and buttons use arbitrary colors across 6+ bright hues without strict semantic justification.
* **Code References:**
  * `frontend/index.html:653`: `style="color:#a855f7;"` (purple).
  * `frontend/index.html:657`: `style="color:#ec4899;"` (hot pink).
  * `frontend/index.html:661`: `style="color:#f97316;"` (orange).
  * `frontend/static/css/style.css:24-34`: Cyan, Amber, Sky Blue, and Emerald defined concurrently.
* **Prescription:** Enforce the 14-token strict palette: Single accent `--accent` (`#C8341E`), `--success` (`#2F7D4F`), `--warn` (`#B7791F`), `--danger` (`#B42318`), `--info` (`#2B5C8A`). Neutral grays for all non-status elements.

### 1.4 Ad-hoc Unicode Glyphs Used as Pseudo-Icons
* **Violation:** Extensive reliance on unicode entities (`&bull;`, `&rarr;`, `&#9888;`, `&check;`, `&#8634;`, `&times;`) instead of an engineering-grade, consistent icon set.
* **Code References:**
  * `frontend/index.html:127, 145, 150, 165-168, 172, 178, 215, 269, 278, 352, 353, 367, 368, 398, 399, 424, 425, 440, 441, 460, 464, 471, 474-482, 509, 520, 629, 630, 631, 633, 637, 641, 645, 649, 653, 657, 661, 742, 750, 752`.
* **Prescription:** Bundle an inlined SVG Lucide icon set (16px dense, 20px default, 1.5px stroke, `currentColor`). Every icon must have an accompanying text label or accessible tooltip.

---

## 2. High Severity Violations (Typography & Layout Architecture)

### 2.1 Absence of Left-Nav Institutional Shell
* **Violation:** The application uses a generic website-style horizontal top navigation bar (`<nav class="nav-tab-bar">`), forcing cramped tab switching and wasting vertical real estate.
* **Code References:**
  * `frontend/index.html:132-140`.
  * `frontend/static/css/style.css:80-92`.
* **Prescription:** Re-architect layout to the standard research instrument shell:
  * Left collapsible sidebar (240px wide) containing institutional branding, primary navigation, student profile switcher, and theme toggle.
  * Sticky top bar displaying academic context: Active Student, Current Semester, Target Goal, and Quick Command button (`Cmd+K`).
  * Dedicated reading/prose viewport capped at `68ch`.
  * Right drawer for "Why this?" course explainer and Conversational Buddy.

### 2.2 Typographic Hierarchy & Extreme Weights
* **Violation:** Extensive use of `font-weight: 700`, `800`, and `900`. Default system font stack lacks tabular numerals (`tnum`) and stylistic alternates (`cv11`).
* **Code References:**
  * `frontend/static/css/style.css:103`: `font-weight: 900;` on `.brand-badge`.
  * `frontend/static/css/style.css:112`: `font-weight: 800;` on `.brand-name`.
  * `frontend/index.html:59, 111, 163, 180, 211, 305, 453, 495, 549, 593, 619, 749, 775, 786`: Hardcoded `font-weight: 800`.
  * `frontend/static/css/style.css:45`: `--font-sans: system-ui, -apple-system, BlinkMacSystemFont...`
* **Prescription:**
  * Use local editorial serif (*Source Serif 4 / Fraunces*) for page titles, section headings, and key metric numerals (`font-weight: 600`).
  * Use clean modern sans (*Geist / Inter Tight*) for body and UI with `font-feature-settings: "tnum", "cv11"`.
  * Maximum weight is 600. Normal text is 400; interactive labels are 500. Never exceed 600.
  * Letter-spacing: `-0.01em` on headings $\ge 20\text{px}$; `0` on body.

### 2.3 Exclamation Marks, Title Case & Vibe Copy
* **Violation:** Informal, hype-filled copy and Title Case on action buttons.
* **Code References:**
  * `frontend/static/js/app.js:403`: `"All test assertions executed and passed successfully! BKT Mastery Updated (+0.12 posterior gain)."`
  * `frontend/static/js/app.js:409`: `"Some assertions failed. Check your logic and retry!"`
  * `frontend/static/js/app.js:752`: `"Profile updated & curriculum re-solved dynamically!"`
  * `frontend/index.html:172`: `"View Verified Roadmap &rarr;"`
  * `frontend/index.html:509`: `"&bull; Run & Test Code"`
* **Prescription:** Re-write all microcopy into calm, terse, factual statements. Use sentence case for all buttons (`Run test assertions`, `Review roadmap`, `Save profile changes`). Remove all exclamation marks.

---

## 3. Medium Severity Violations (Components & State Management)

### 3.1 Radar Chart Gimmick
* **Violation:** The mastery view includes an arbitrary SVG radar polygon chart (`#mastery-radar-svg`). Section 5 explicitly warns: *"A skill map as a grouped matrix or heatmap (not a radar chart gimmick)"*.
* **Code References:**
  * `frontend/index.html:9-24, 564-570`.
  * `frontend/static/js/app.js:495-555`: `renderRadarChart()`.
* **Prescription:** Replace the radar chart with a high-density, categorized skill matrix / heatmap. Clearly distinguish **Not Started**, **Course Completed**, and **Demonstrated Proficiency** using distinct geometric glyphs and text labels (not color alone).

### 3.2 Inconsistent Radius and Elevation Scale
* **Violation:** Border radii range from 6px, 8px, 12px, to 16px. Shadows range up to `0 10px 30px rgba(0, 0, 0, 0.5)`.
* **Code References:**
  * `frontend/static/css/style.css:36-44`.
* **Prescription:** Restrict border radii strictly to:
  * `6px`: Buttons, inputs, small tags, chips.
  * `10px`: Modals, dialogs, drawers, major view panels.
  * `999px`: Avatars and status indicator pips only.
  * Elevation: 0px shadow on base surfaces; exactly one subtle shadow for popovers/menus: `0 8px 24px rgba(27,26,23,.08), 0 1px 2px rgba(27,26,23,.06)`.

### 3.3 Missing State Treatments (Empty, Loading, Error, Offline)
* **Violation:** Many views assume pre-existing student data and lack consistent skeleton loaders, explanatory empty states, or error retry affordances.
* **Prescription:** Every list, table, and data container must have 4 formal states:
  1. *Loading*: Low-contrast neutral skeleton matching the shape of target content.
  2. *Empty*: Neutral icon, one-line explanation, single verb button.
  3. *Error*: Factual cause statement and "Retry request" button.
  4. *Offline*: Subtle banner indicating deterministic fallback mode.

---

## 4. Low Severity Violations (Micro-interactions & Code Organization)

* **Keyboard Focus Missing**: Elements lack visible, standardized `focus-visible` styling (`2px solid var(--accent)` with `2px offset`).
* **No Command Palette**: Lacks keyboard shortcut launcher (`Cmd/Ctrl+K`) for rapid navigation.
* **Prose Line Length**: Dashboard cards allow reading text to stretch across unconstrained viewport widths instead of capping at `68ch`.

---

## Implementation Roadmap

1. **Foundations (`tokens.css`, `typography.css`, `icons.js`)**:
   * Define the 14 light/dark semantic tokens.
   * Embed local fonts and tabular number styles.
   * Build the reusable component library.
   * Create the hidden `/styleguide` endpoint.
2. **Screens (Plan, Dashboard, Onboarding, Diagnostic, Mastery, Practice, Buddy, Admin)**:
   * Replace ad-hoc HTML structures with the component library.
   * Enforce sentence case and calm academic microcopy.
3. **Visual Verification**:
   * Take 1440px and 390px headless screenshots of `/styleguide` and all screens.
   * Ensure Lighthouse accessibility $\ge 95$ and zero external network requests.

