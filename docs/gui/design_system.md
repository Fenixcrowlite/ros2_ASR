# GUI Design System

## Visual Direction
- Style: clean engineering console, calm and legible.
- Emphasis: readability, status clarity, action confidence.
- No decorative dashboard noise.

## Typography
- Primary: `Space Grotesk` for UI text.
- Monospace: `IBM Plex Mono` for IDs, logs, raw payload snippets.
- Hierarchy:
  - H1: page/product title
  - H2: section title
  - H3: card title
  - body + helper text

## Color Tokens
- `--bg`: soft neutral background
- `--panel`: card surface
- `--text`: primary text
- `--text-muted`: secondary text
- `--border`: structural separators
- `--accent`: interactive primary
- `--ok`: healthy/success
- `--warn`: warning
- `--error`: error/failure
- `--info`: informational status

## Layout System
- App shell:
  - topbar (title + system pulse)
  - left navigation rail
  - content panel
- Grid:
  - cards in responsive columns (minmax)
  - tables with sticky headers where useful

## Component Primitives
- Buttons: primary/secondary/ghost/danger
- Inputs: text/select/textarea/checkbox group
- Cards: title + helper + content + actions
- Badges: status and capability labels
- Alerts: info/warn/error with remediation hint
- Tables: sortable-ready baseline + empty states
- Tabs/stepper: benchmark run builder flow

## Interaction States
- Loading: inline spinner + disabled action
- Empty: explanatory copy + next action button
- Error: explicit message + suggested fix
- Success: short confirmation in-page toast banner

## Validation Pattern
- Inline validation under field.
- Summary validation panel before critical submit.
- Warning vs blocking error distinction.

## Accessibility Baseline
- Color contrast suitable for long sessions.
- Keyboard-focus visible.
- Form labels always explicit.
- Status not color-only (text labels included).

## Motion Rules
- Minimal purposeful motion:
  - fade/slide for section transitions
  - subtle pulse for live status
- Avoid heavy animation loops.

## Mobile Behavior
- Sidebar collapses into horizontal nav chips.
- Cards become single-column.
- Tables keep readable overflow handling.

## Security UX Rules
- Never echo stored secret values.
- Mask sensitive fields in summary.
- Keep credential operations explicit and auditable.
