---
name: Modern Wealth Horizon
colors:
  surface: '#fcf8ff'
  surface-dim: '#dad7f3'
  surface-bright: '#fcf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f2ff'
  surface-container: '#efecff'
  surface-container-high: '#e8e5ff'
  surface-container-highest: '#e2e0fc'
  on-surface: '#1a1a2e'
  on-surface-variant: '#3c4a43'
  inverse-surface: '#2f2e43'
  inverse-on-surface: '#f2efff'
  outline: '#6b7b72'
  outline-variant: '#bacac1'
  surface-tint: '#006c4f'
  primary: '#006c4f'
  on-primary: '#ffffff'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#2fe0aa'
  secondary: '#0061a5'
  on-secondary: '#ffffff'
  secondary-container: '#6fb2fd'
  on-secondary-container: '#004375'
  tertiary: '#5d3fe0'
  on-tertiary: '#ffffff'
  tertiary-container: '#b9adff'
  on-tertiary-container: '#461fc9'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#d2e4ff'
  secondary-fixed-dim: '#a0caff'
  on-secondary-fixed: '#001c37'
  on-secondary-fixed-variant: '#00497e'
  tertiary-fixed: '#e5deff'
  tertiary-fixed-dim: '#c9bfff'
  on-tertiary-fixed: '#1a0063'
  on-tertiary-fixed-variant: '#441cc8'
  background: '#fcf8ff'
  on-background: '#1a1a2e'
  surface-variant: '#e2e0fc'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
  tabular-nums:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system crafts an accessible, high-trust wealth management and retail investing experience. It balances institutional credibility with retail simplicity, stripping away legacy financial friction in favor of radical transparency, crisp data visualization, and effortless interaction.

The visual style is rooted in modern, high-clarity minimalism with purposeful color-coding for financial metrics. Key interface goals:
- Inspire absolute confidence through stable, disciplined layouts and deep slate typography.
- Make portfolio comprehension immediate through dedicated status accents (positive growth, active positions, warnings, and alerts).
- Deliver tactile, friction-free interactions using clean surface elevations and crisp micro-borders.

## Colors

The palette establishes an immediate semantic hierarchy tailored for portfolio analytics, trading, and asset tracking:

- **Primary Accent (`#00D09C`):** Used for primary conversion triggers, positive market performance, gains, and confirmation states.
- **Secondary Accent (`#4A90D9`):** Represents informational highlights, linked accounts, research indicators, and primary navigation active states.
- **Tertiary Accent (`#7B61FF`):** Reserved for mutual funds, alternative investments, premium insights, and categorical chart segmentation.
- **Warning / Pending (`#F5A623`):** Communicates order holds, neutral movements, watchlist changes, and pending settlements.
- **Negative / Loss (`#E74C3C`):** Applied exclusively to market losses, downward trends, negative cashflow, and critical destructive actions.
- **Background & Canvas (`#F8F9FA`):** An ultra-clean, low-glare neutral surface that prevents eye fatigue across long trading sessions.
- **Surface & Cards (`#FFFFFF`):** High-contrast base for structured financial tables, balance summaries, and action panels.
- **Typography & Neutral (`#1A1A2E`):** Deep slate providing razor-sharp legibility without the harsh contrast of pure black. Secondary text steps down to `#6B7280`, with divider lines calibrated to `#E5E7EB`.

## Typography

Inter serves as the single typographic family across all roles to maximize numerical precision, technical clarity, and tabular consistency.

- **Tabular Figures:** Always apply OpenType tabular numbers (`tnum`) to portfolio yields, ticker quotes, order books, and balance figures to prevent layout shift during realtime market ticks.
- **Hierarchy:** Reserve `display-lg` for total portfolio net worth and prominent onboarding stats. Use `headline-sm` and `body-md` for standard dashboard card headers and data labels.
- **Letter Spacing:** Tighter tracking on headlines creates modern authority; neutral to slight positive tracking on sub-12px badges ensures uncompromised legibility on dense dashboards.

## Layout & Spacing

The layout is structured around an 8pt spatial grid within an adaptive 12-column layout designed for responsive analytical views.

- **Desktop (1024px+):** 12 columns, 24px (`space-lg`) gutters, and 32px (`space-xl`) margins. Supports persistent sidebar navigation, 8-column main analytical charts, and 4-column quick-order/watchlist rails.
- **Tablet (768px – 1023px):** 8 columns, 20px gutters, and 24px margins. Order panels collapse below primary portfolio summaries.
- **Mobile (< 768px):** 4 columns, 16px (`space-md`) gutters, and 16px margins. Complex data tables convert to stacked card lists with horizontal scrolling reserved strictly for granular stock metrics.
- **Internal Spacing:** Components standardize on `space-md` (16px) for inner padding on standard cards and `space-sm` (8px) for tightly grouped transaction items and input controls.

## Elevation & Depth

Visual hierarchy uses a refined dual-layering technique combining crisp hairline borders with soft ambient diffusion:

- **Level 0 (Canvas):** Flat `#F8F9FA`. Background for holding modules, navigation bars, and page canvases.
- **Level 1 (Cards & Data Panels):** Pure `#FFFFFF` fill paired with a subtle structural border (`1px solid #ECEFF2`) and an ambient drop shadow: `0 2px 8px rgba(0, 0, 0, 0.08)`. This keeps surfaces tactile yet lightweight.
- **Level 2 (Hover & Active Cards):** On hover or selection, elevation lifts with `0 6px 16px rgba(0, 0, 0, 0.10)` and border color transitions to `rgba(0, 208, 156, 0.30)` or `#E2E8F0`.
- **Level 3 (Dropdowns & Popovers):** `0 10px 24px rgba(0, 0, 0, 0.12)`, `1px solid #E5E7EB`.
- **Level 4 (Modals & Trade Sliders):** Centered modal overlays paired with a scrim backdrop (`rgba(26, 26, 46, 0.40)`) and a deep elevation shadow: `0 20px 40px rgba(0, 0, 0, 0.16)`.

## Shapes

The design system maintains a consistent geometric shape language centered on modern 12px card architecture.

- **Cards & Data Modules:** Explicitly set to `0.75rem` (12px) border radius to establish a friendly, contemporary financial canvas without feeling toy-like.
- **Input Fields & Buttons:** Standardized to `0.5rem` (8px) for crisp structural input definition.
- **Chips, Badges, & Status Pills:** Fully rounded (`9999px` / pill form) to distinguish state labels from interactive rectangular surfaces.

## Components

### Buttons
- **Primary:** Background `#00D09C`, text `#FFFFFF`, font-weight 600, border-radius 8px. Hover: `#00B887`. Active: `#009E73`.
- **Secondary:** Surface `#FFFFFF`, border `1px solid #E5E7EB`, text `#1A1A2E`. Hover: `#F8F9FA` with border `#D1D5DB`.
- **Destructive / Sell:** Background `#E74C3C`, text `#FFFFFF`. Hover: `#D43F30`.
- **Ghost:** Background transparent, text `#4A90D9`. Hover: `rgba(74, 144, 217, 0.08)`.

### Cards & Panels
- Background `#FFFFFF`, border-radius 12px, border `1px solid #ECEFF2`, shadow `0 2px 8px rgba(0, 0, 0, 0.08)`.
- Internal card padding standardizes to 20px or 24px (`space-lg`), with segmented header rules using `1px solid #F1F3F5`.

### Input Fields
- Height 44px, border-radius 8px, border `1px solid #E2E8F0`, background `#FFFFFF`, text `#1A1A2E`.
- Focus state: border-color `#00D09C`, box-shadow `0 0 0 3px rgba(0, 208, 156, 0.15)`, outline none.
- Currency / Ticker prefix: Locked slate text (`#6B7280`) with internal subtle right border divider.

### Chips & Badges
- **Positive Returns:** Background `rgba(0, 208, 156, 0.12)`, text `#00A37A`, font-weight 600, border-radius 9999px, padding 4px 10px.
- **Negative Returns:** Background `rgba(231, 76, 60, 0.12)`, text `#C0392B`, font-weight 600, border-radius 9999px, padding 4px 10px.
- **Filter Chips:** Unselected has `#F1F3F5` background with `#1A1A2E` text; selected transitions to `#1A1A2E` background with `#FFFFFF` text.

### Checkboxes & Radio Buttons
- 18px x 18px, border `2px solid #D1D5DB`, border-radius 4px (checkbox) or 50% (radio).
- Checked: Background `#00D09C`, border-color `#00D09C`, checkmark or center dot rendered in `#FFFFFF`.

### Financial Data Tables
- Header: Background `#F8F9FA`, text `#6B7280`, uppercase, 11px font size, weight 600, tracking 0.05em.
- Rows: Minimum height 52px, bottom border `1px solid #F3F4F6`, tabular numeric formatting right-aligned for currency and percentages.
- Row hover: Subtle fill transition to `rgba(248, 249, 250, 0.8)`.

### Metrics Stat Callout
- Value display: 24px/28px bold tabular number in `#1A1A2E`.
- Sub-label: 12px medium in `#6B7280` accompanied by an inline directional arrow icon and gain/loss badge.