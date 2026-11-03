# Design System: BPS Data Workbench

## Identity & Purpose
- **System**: BPS Dalam Angka Web Parser & Visualizer
- **Purpose**: Fast extraction, visualization, and export of BPS statistical publications into standardized Excel format.
- **Audience**: Analysts, researchers, government staff, and students needing rapid tabular extraction without waiting for slow CLI batch jobs.

## Visual Direction: Clean Data Workbench
- **Theme**: Utilitarian, data-dense, crisp and professional.
- **Palette**:
  - Background Base: `#F8FAFC` (Slate 50)
  - Card & Surface: `#FFFFFF`
  - Text Primary: `#0F172A` (Slate 900) - high contrast, WCAG AAA
  - Text Muted: `#475569` (Slate 600)
  - Border & Dividers: `#CBD5E1` (Slate 300) / `#E2E8F0` (Slate 200)
  - Brand & Accent: `#1E3A8A` (Deep BPS Navy)
  - Accent Secondary: `#0284C7` (Sky 600 for interactive states)
  - Success: `#059669` (Emerald 600)
  - Warning: `#D97706` (Amber 600)
  - Danger / Error: `#DC2626` (Red 600)
- **Typography**:
  - System font stack: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
  - Tabular data: `ui-monospace, SFMono-Regular, "Cascadia Code", Consolas, monospace`
- **Component Rules**:
  - No decorative gradients or floating backdrop blobs.
  - Clear visual hierarchy: Stepper header (1. Upload -> 2. Select Tables -> 3. Preview -> 4. Export).
  - Tables: Sticky header, bordered cells, zebra alternate row background (`#F8FAFC`), right-aligned numeric data.
  - Accessible tap targets (minimum 40px), focus rings (`focus:ring-2 focus:ring-sky-500`).

