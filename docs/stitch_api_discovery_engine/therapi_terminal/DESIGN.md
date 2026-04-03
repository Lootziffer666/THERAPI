# Cyanide Glass Design System

### 1. Overview & Creative North Star
**Creative North Star: The Technical Architect**
Cyanide Glass is a high-density, editorial design system built for complex data orchestration and API discovery. It rejects the "fluff" of modern consumer apps in favor of a "Technical Editorial" aesthetic—combining the precision of a blueprint with the sophisticated layout of a premium journal. 

The system breaks the standard grid through **Intentional Asymmetry**: large, bold headers (2.25rem) are offset by hyper-minimized labels (10px), creating a rhythmic tension that guides the eye toward critical data points. Elements don't just sit on the page; they are categorized into distinct "Panels of Truth" that use background shifts rather than lines to define their domain.

### 2. Colors
The palette is rooted in deep teals (#006B5F) and architectural blues (#1F6FEB), supported by a sophisticated range of neutral greys.

*   **Primary (Teal):** Used for authority, success, and primary actions. It signals "System Ready."
*   **Tertiary (Blue):** Used for interactive triggers, links, and highlighted status states.
*   **The "No-Line" Rule:** 1px borders are prohibited for sectioning. Use `surface-container-low` (#f2f4f6) for primary sections and `surface-container-highest` (#e0e3e5) for nested inputs. Contrast is the boundary.
*   **Surface Hierarchy:**
    *   `background`: Global canvas.
    *   `surface-container-low`: Primary content sections.
    *   `surface-container-highest`: Input fields and secondary interactive zones.
*   **Glass & Gradient Rule:** Use `rgba(247, 249, 251, 0.8)` with a 12px blur for floating panels or sidebars to maintain context of the underlying data. Use the "Primary Gradient" (Linear 135deg, #0057C3 to #1F6FEB) exclusively for high-impact hero elements or primary status indicators.

### 3. Typography
The system utilizes **Inter** across all levels, relying on weight and tracking rather than font switching to establish hierarchy.

*   **Display/Headline:** 2.25rem (36px). Extrabold with tight tracking (-0.025em). This is the "Anchor" of the page.
*   **Sub-Header/Title:** 1.125rem (18px). Bold. Used for section titles.
*   **Body:** 0.875rem (14px). Medium weight for maximum readability in high-density tables.
*   **Label/Caption:** 10px or 0.75rem. Always uppercase with `tracking-widest` (0.1em) and 60% opacity. This "Technical Metadata" style provides context without cluttering the visual field.

### 4. Elevation & Depth
Depth is achieved through **Tonal Layering** rather than elevation.

*   **The Layering Principle:** A white `surface-container-lowest` header sits atop a `background` canvas. Content sections use `surface-container-low` to recede slightly.
*   **Ambient Shadows:** Use the `architect-shadow` (`0px 20px 40px rgba(0, 25, 68, 0.06)`) for primary cards to create a soft, lifted effect that feels integrated into the atmosphere.
*   **The "Ghost Border":** For high-density tables, use `divide-surface-container-high/20` (a very faint horizontal divider) to maintain row alignment without creating visual "noise."

### 5. Components
*   **Signature Breadcrumb:** A large 2.25rem H1 paired horizontally with a 10px uppercase Session ID. This establishes the "Editorial" feel.
*   **Status Pills:** Rounded-full containers using `/10` or `/20` opacity of the functional color (e.g., `bg-tertiary-container/10 text-tertiary`). Must include a pulse animation for "Live" states.
*   **Architecture Inputs:** Inputs use `surface-container-highest` with no borders. On focus, a 2px bottom-border of `primary` emerges, simulating a "filling" effect.
*   **Method Badges:** Hyper-bold 10px badges (GET, POST, PUT, DELETE) using semantic colors with high-contrast backgrounds to allow quick scanning of API logs.

### 6. Do's and Don'ts
*   **Do:** Use horizontal spacing of 32pt+ between major heading elements.
*   **Do:** Use 10px uppercase tracking for all metadata labels.
*   **Don't:** Use solid black (#000) for text; use `on-surface` (#191c1e) to maintain a soft technical feel.
*   **Don't:** Add borders to cards. If the card isn't visible, adjust the background color of the canvas or the card itself.
*   **Do:** Use 10px (0.625rem) corner radius for all primary containers and buttons.