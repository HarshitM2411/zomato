# Google Stitch — Frontend Design Prompt

Copy everything inside the **PROMPT START** / **PROMPT END** block below into Google Stitch.

---

## PROMPT START

Design a complete, production-quality web UI for a mobile-first and desktop-responsive web application called **Restaurant Recommender**.

### Product summary

An AI-powered restaurant discovery app for India. Users enter dining preferences (location, budget, cuisine, minimum rating, and free-text extras). The backend filters a real Zomato dataset (~51,000 restaurants) and uses an LLM (Groq) to return **3–5 ranked recommendations**, each with a short personalized explanation — like advice from a knowledgeable friend, not a generic search list.

**Tagline:** “Personalized picks from real restaurant data, explained by AI.”

**Audience:** Urban diners in India (e.g. Bangalore, Delhi) deciding where to eat tonight.

---

### Brand & visual direction

- **Mood:** Warm, trustworthy, modern food-discovery — not corporate, not childish.
- **Primary color:** `#2563eb` (blue) for CTAs, links, active states.
- **Background:** Soft off-white `#f4f6f8`; cards on white `#ffffff`.
- **Text:** Near-black `#1a1a1a` for headings; `#555555` for secondary text.
- **Semantic colors:**
  - Success / results summary: green tint
  - Warning / no results: amber
  - Error: red `#c0392b` with light red background panel
  - Info: blue tint (loading, “no matches in dataset”)
- **Typography:** Clean sans-serif (Inter, system-ui, or similar). Clear hierarchy: hero title → section titles → labels → body.
- **Corners:** 10–12px on cards and inputs; subtle shadows (`0 2px 8px rgba(0,0,0,0.06)`).
- **Currency:** Indian Rupees — label as “Rs.” or “₹” for cost-for-two.
- **Icons:** Simple line icons for location, budget, cuisine, star rating, and sparkles/AI for recommendations (optional).

---

### Screens to design

#### Screen 1 — Home / Preferences (main screen)

**Header**
- App name: “Restaurant Recommender”
- Subtitle: “Get AI-ranked recommendations from the Zomato dataset based on your preferences.”

**Preferences card** (single white panel, form layout)

| Field | Control | Details |
|-------|---------|---------|
| Location * | Text input | Required. Placeholder: “e.g. Bangalore”. Show red asterisk on label. |
| Budget | Dropdown / segmented control | Options: **Low** (up to Rs. 300), **Medium** (Rs. 301–700), **High** (above Rs. 700). Default: Medium. |
| Cuisine | Text input | Optional. Placeholder: “e.g. Italian (leave blank for any)” |
| Minimum rating | Slider 0.0–5.0 | Default 3.5; show current value (e.g. “3.5”) beside slider; star metaphor optional. |
| Extra preferences | Textarea (2–3 rows) | Optional. Placeholder: “e.g. family-friendly, outdoor seating” |

**Primary CTA:** Full-width or prominent button — **“Get Recommendations”** (primary blue, white text).

**Footer note (small, muted):** “Powered by Zomato data & Groq AI” — optional, subtle.

---

#### Screen 2 — Loading states (overlay or inline)

Show as variants or a dedicated loading section below the form:

1. **“Finding matching restaurants…”** — after submit, dataset filter in progress (skeleton or spinner).
2. **“Getting AI recommendations…”** — LLM call in progress.

Use a centered spinner or progress indicator; disable the submit button while loading.

---

#### Screen 3 — Results (recommendations list)

Shown below the form (same page scroll) after successful response.

**Status banner (success):**  
“Found 4 candidates; showing 3 recommendations.” — green or blue success strip.

**Section title:** “Recommendations”

**Recommendation cards** (stacked vertically, 3–5 cards max):

Each card includes:
- **Rank badge:** `#1`, `#2`, … in primary blue or accent pill
- **Restaurant name** — bold, large (H3)
- **Three metrics in a row** (equal columns on desktop, stacked on mobile):
  - Cuisine (label + value)
  - Rating (e.g. `4.2 / 5` with small star icon)
  - Cost for two (e.g. `Rs. 600`)
- **“Why this?”** section — label bold, 1–2 sentence explanation in regular body text (this is the AI differentiator; give it comfortable line height)

Card style: white background, light border `#e5e7eb`, padding 16–20px, spacing between cards 16px.

**Example card content (for mockup):**
- #1 Truffles | Italian | 4.5/5 | Rs. 600 | “Excellent Italian with high ratings and a cozy ambiance — ideal for your medium budget in Bangalore.”

---

#### Screen 4 — Empty & error states

Design distinct UI blocks (not modals unless mobile):

| State | Message | Style |
|-------|---------|-------|
| Validation error | “Location is required.” | Red left border panel |
| No dataset matches | “No restaurants found matching the given preferences. Try broadening your location, cuisine, or budget filters.” | Blue/info panel |
| No AI recommendations | “No recommendations could be generated. Try broadening your preferences.” | Amber warning panel |
| API key missing | “GROQ_API_KEY is not set. Add it to your environment.” | Red error panel |
| Generic error | “Something went wrong: …” | Red error panel |

---

### Layout & responsiveness

- **Desktop (≥768px):** Centered max-width container ~720px; form and results same column; metrics in 3 columns inside cards.
- **Mobile:** Full-width padding 16px; form fields full width; card metrics stack vertically; CTA thumb-friendly (min 44px height).
- **Tablet:** Same as desktop with slightly narrower max-width.

---

### Interaction & UX details

- Form persists user input after submit (don’t clear fields on error).
- Submit triggers scroll-to-results or smooth scroll to recommendations section.
- Disabled submit + loading indicator during 10–30 second wait (dataset + AI).
- Empty cuisine = “Any” in summary chips optional (e.g. show selected filters as chips above results: `Bangalore · Medium · Italian · ≥3.5`).
- Accessibility: visible focus rings, label-input association, sufficient contrast (WCAG AA).

---

### Optional enhancements (if Stitch supports variants)

- **Filter summary chips** above results showing active preferences.
- **Hero illustration** — minimal line art of dining/map (subtle, top of page).
- **Dark mode variant** — same structure, inverted backgrounds.

---

### Deliverables expected from Stitch

1. High-fidelity mockup of **Home + Results** (desktop and mobile frames).
2. Component library snippets: buttons, inputs, select, slider, cards, alert banners.
3. HTML/CSS or design tokens export if available (colors, spacing, font sizes as variables).

**Do not** include backend code. Frontend only. The form POSTs to `/recommend` or calls an API — show the UI as a static interactive prototype with sample data filled in on the results screen.

---

## PROMPT END
