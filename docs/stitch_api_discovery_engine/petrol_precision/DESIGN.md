# Design System Specification: High-Precision Editorial Tooling

## 1. Overview & Creative North Star
The "Creative North Star" for this design system is **The Precision Architect**. This system moves beyond the generic "SaaS Dashboard" look by combining the surgical accuracy of professional tooling with the sophisticated whitespace and typographic hierarchy of high-end editorial design.

Rather than relying on boxes and borders to organize information, this system utilizes **Tonal Depth** and **Intentional Asymmetry**. It is designed to feel authoritative, calm, and deliberate. Every element is placed with high-precision intent on a strict 8pt grid, creating a layout that breathes through spacious margins while maintaining a dense, information-rich soul.

## 2. Colors & Surface Logic
The palette is rooted in a professional "Deep Petrol" foundation, supported by surgical mint accents and a complex hierarchy of cool-toned neutrals.

### Primary Palette
- **Primary (`#005147`):** The "Deep Petrol" core. Used for high-priority actions and active navigation states.
- **Primary Container (`#006B5F`):** Used for large interactive surfaces or hover states to provide a subtle glow.
- **Secondary (`#006A60`):** A slightly more vibrant teal for secondary accents and system status indicators.
- **Secondary Container (`#7CF7E5`):** "Soft Mint/Cyan" for success states, background chips, and light emphasis.

### Neutral & Surface Hierarchy
To achieve a premium feel, we follow the **"No-Line" Rule**: Physical borders are prohibited for sectioning. Boundaries are defined through background shifts.
- **Background (`#F7F9FB`):** The canvas. A cool, expansive off-white.
- **Surface Container Lowest (`#FFFFFF`):** High-priority "floating" cards. This is the only pure white surface.
- **Surface Container Low (`#F2F4F6`):** Standard content sections that need a slight lift from the background.
- **Surface Container High (`#E6E8EA`):** Deeply nested elements or inactive input backgrounds.

### Signature Polish
- **Glassmorphism:** For floating modals or "always-on-top" elements, use `surface-container-lowest` at 80% opacity with a `20px` backdrop-blur.
- **Tonal Gradients:** For primary CTAs, use a subtle vertical gradient from `primary_container` to `primary` to add "soul" and weight.

## 3. Typography
We utilize **Inter** across the entire system. The hierarchy is driven by dramatic weight shifts rather than just size.

- **Display & Headlines:** Use `Inter Semibold`. Tighten letter-spacing slightly (-0.02em) for headlines to create a compact, "editorial" impact.
- **Body & Labels:** Use `Inter Regular`. For technical data (labels), use `label-md` in `on-surface-variant` to keep the UI from feeling cluttered.
- **The Contrast Principle:** Pair a `headline-lg` title with a `body-sm` description immediately below it. The intentional jump in scale signals professional hierarchy.

## 4. Elevation & Depth
Depth in this system is achieved through **Tonal Layering** rather than heavy drop shadows.

- **The Layering Principle:** Stack `surface-container-lowest` cards on top of a `surface-container-low` background. This creates a natural, soft lift without the visual noise of a border.
- **Ambient Shadows:** When a card requires a floating effect, use a custom shadow: `0px 4px 20px rgba(0, 81, 71, 0.05)`. Note the use of a tinted shadow (using the primary color) to mimic natural ambient light.
- **The Ghost Border:** If a separator is required for high-density data tables, use a `1px` line with `outline-variant` at 20% opacity. Never use 100% opaque lines.

## 5. Components

### Buttons & Inputs
- **Primary Button:** Filled `primary`, `10px` radius, white text. Sizing is generous (40px height minimum).
- **Secondary Button:** Filled `surface-container-high` with `on-surface` text. No border.
- **Inputs:** `10px` radius. Use `surface-container-high` as the background color rather than a white box with a border. This makes the input feel "recessed" into the UI.

### Navigation & Chips
- **Active States:** Indicated by a vertical `4px` bar of `primary` on the left edge of the navigation item, paired with a subtle `surface-container-low` background shift.
- **Status Chips:** Use `secondary-container` (Soft Mint) for positive status. Text should be `on-secondary-container`.

### Cards & Lists
- **The Borderless Rule:** Cards are pure white (`#FFFFFF`) with a `10px` radius and an ambient shadow. 
- **List Items:** Separate list items with `16px` of vertical whitespace (2x 8pt grid steps) rather than divider lines.

### Tooltips & Overlays
- **Styling:** Dark themed using `inverse-surface` with `8px` radius. This provides a sharp, authoritative contrast against the light UI.

## 6. Do’s and Don’ts

### Do:
- **Do** use whitespace as a functional tool. If a section feels crowded, add 8px of padding rather than a line.
- **Do** use `primary` (Petrol) sparingly. It should be a "signal" color that draws the eye to a single point of truth.
- **Do** lean into the 8pt grid. Every margin, padding, and height must be a multiple of 8.

### Don’t:
- **Don’t** use pure black `#000000` for text. Use `on-surface` (`#191C1E`) to maintain a soft, professional tone.
- **Don’t** use standard `1px` solid borders. If a container isn't visible, adjust the background color of the parent or child.
- **Don’t** use "default" blue for links. Everything interactive must be Petrol or Mint.
- **Don’t** mix radii. The `10px` corner is a signature of this system; do not use `4px` or `16px` unless for specific nested elements (like tags).