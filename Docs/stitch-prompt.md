# Google Stitch Prompt — Weekly App Review Pulse Dashboard

## Prompt

Build a single-page, light-themed dashboard web app called **"Weekly App Review Pulse"** for the Groww fintech platform. This dashboard visualizes weekly Play Store review analysis results. Use a clean, modern, professional design with a white/light gray background, soft card shadows, and the Groww brand green (#00D09C) as the primary accent color.

---

### Page Layout

**Top Navigation Bar**
- White background with a subtle bottom border
- Left: App name "Weekly App Review Pulse" in bold, with a small green pulse/chart icon
- Right: "Groww" logo text in green, and a "Period: Aug 8 – Oct 16, 2026" date badge

**Summary Stats Row** (4 stat cards in a horizontal row below the nav)
- Card 1: "380" large number, "Reviews Analyzed" label below, with a document icon
- Card 2: "5" large number, "Themes Found" label, with a tag/category icon
- Card 3: "2.6" large number, "Avg Rating" label, with a star icon — show 2.6 out of 5 as partially filled stars
- Card 4: "10 weeks" large number, "Analysis Window" label, with a calendar icon
- Each card: white background, rounded corners (12px), light shadow, icon in green accent

---

### Main Content (Two-Column Layout)

**Left Column (60% width)**

**Section 1: Top Themes (Card)**
- Section heading: "Top Themes" with a tag icon
- Display 3 theme cards stacked vertically, each containing:
  - Theme 1: "Feature Gaps & Trading Tools" — 109 reviews — avg 3.0 stars — green progress bar showing 109/380 (29%)
    - One-line summary: "Traders demand advanced indicators and chart-based trading parity with competitors."
  - Theme 2: "UI/UX & Navigation Issues" — 101 reviews — avg 3.5 stars — progress bar at 101/380 (27%)
    - Summary: "Users report confusing navigation, accidental triggers, and missing data displays."
  - Theme 3: "Customer Support & Responsiveness" — 72 reviews — avg 1.6 stars — progress bar at 72/380 (19%)
    - Summary: "Users cite unreachable teams and unresolved critical account issues."
- Each theme card has a colored left border (green for theme 1, blue for theme 2, orange for theme 3)
- Star ratings displayed as filled/empty star icons inline
- Review count shown as a pill/badge

**Section 2: Suggested Actions (Card)**
- Section heading: "Suggested Actions" with a lightbulb icon
- 3 action items displayed as a checklist-style list:
  1. "Implement trailing stop-loss orders and expand technical indicator libraries to match competitor features." — tagged with "Feature Gaps" pill in green
  2. "Redesign chart navigation to prevent accidental scalper mode triggers and ensure back buttons remain visible." — tagged with "UI/UX" pill in blue
  3. "Audit support workflows to reduce automated responses and improve resolution times for critical account errors." — tagged with "Support" pill in orange
- Each action has a numbered circle icon (1, 2, 3) on the left

---

**Right Column (40% width)**

**Section 3: User Voices (Card)**
- Section heading: "User Voices" with a quote/chat icon
- Display 3 quote cards stacked vertically:
  - Quote 1: "Customer care is not easy to reach nor is able to solve the issues properly." — star rating: 2 stars — show in a speech bubble style card with light gray background
  - Quote 2: "Scalper button placement is terrible; whenever I hit back from a chart, it accidentally triggers scalping." — 2 stars
  - Quote 3: "I'm talking about Trade directly from charts i.e., like Dhan you can simply drag drop SL and target levels." — 3 stars
- Each quote card: italic text, opening/closing quotation marks as a large decorative element, star rating below, thin left border matching the theme color

**Section 4: Theme Distribution (Card)**
- Section heading: "Review Distribution" with a pie chart icon
- A horizontal stacked bar chart (or donut chart) showing the 5 theme proportions:
  - Feature Gaps & Trading Tools: 109 (28.7%) — green
  - UI/UX & Navigation Issues: 101 (26.6%) — blue
  - Customer Support: 72 (18.9%) — orange
  - App Performance & Stability: 58 (15.3%) — purple
  - Order Execution & Reliability: 40 (10.5%) — red
- Legend below the chart with colored dots and theme names
- Each segment shows the percentage on hover or as inline labels

**Section 5: Rating Breakdown (Small Card)**
- Section heading: "Rating Breakdown"
- 5 horizontal bars (one per star level, 1-star through 5-star):
  - 5-star: 107 reviews (28.2%) — green bar
  - 4-star: 30 reviews (7.9%) — light green bar
  - 3-star: 44 reviews (11.6%) — yellow bar
  - 2-star: 25 reviews (6.6%) — orange bar
  - 1-star: 174 reviews (45.8%) — red bar
- Star icon + count + percentage label on each row

---

### Design Specifications

- **Theme**: Light mode only — white (#FFFFFF) background, light gray (#F8F9FA) for section backgrounds, dark text (#1A1A2E)
- **Primary accent**: Groww green (#00D09C)
- **Secondary colors**: Blue (#4A90D9), Orange (#F5A623), Purple (#7B61FF), Red (#E74C3C)
- **Typography**: Inter or system sans-serif, headings 20-24px semibold, body 14-16px regular
- **Cards**: White background, border-radius 12px, box-shadow: 0 2px 8px rgba(0,0,0,0.08)
- **Spacing**: 24px padding inside cards, 16px gap between cards
- **Responsive**: Two columns on desktop (>1024px), single column stacked on mobile
- **No dark mode toggle** — light theme only
- **Animations**: Subtle fade-in on card load, smooth progress bar fill animations
- **No backend connection needed** — all data is hardcoded/static for this prototype
