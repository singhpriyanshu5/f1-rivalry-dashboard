<script>
    import '@evidence-dev/tailwind/fonts.css';
    import { EvidenceDefaultLayout } from '@evidence-dev/core-components';
    export let data;
</script>

<svelte:head>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
    <link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;700;800;900&family=Saira:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet" />
</svelte:head>

<EvidenceDefaultLayout {data} hideHeader={true} hideSidebar={true} hideTOC={true} hideBreadcrumbs={true}>
    <slot slot="content" />
</EvidenceDefaultLayout>

<style>
    /* ═══════════════════════════════════════════════════
       F1 RIVALRY DASHBOARD — DARK TELEMETRY THEME
       Font: Saira (motorsport-inspired geometric sans)
       Palette: F1 Red + Mercedes Teal on carbon dark
       ═══════════════════════════════════════════════════ */

    /* ── Base overrides ── */
    :global(html), :global(body) {
        font-family: 'Saira', system-ui, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        background: #0b0b12 !important;
        color: #c8c8d4 !important;
    }

    :global(main), :global(article), :global([class*="content"]) {
        background: #0b0b12 !important;
    }

    :global(html[data-theme="dark"]) {
        --base-100: #0b0b12;
        --base-200: #12121e;
        --base-300: #1c1c2e;
        --base-heading: #f0f0f5;
        --base-content: #c8c8d4;
        --base-content-muted: #6b6b80;
    }

    /* ── Typography ── */
    :global(h1), :global(h2), :global(h3), :global(h4) {
        font-family: 'Saira Condensed', 'Saira', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase;
    }

    :global(h1) {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.06em !important;
    }

    :global(h2) {
        font-size: 1.5rem !important;
        color: #f0f0f5 !important;
        margin-top: 0.5rem !important;
        margin-bottom: 1rem !important;
    }

    :global(h3) {
        font-size: 1.1rem !important;
        color: #b0b0c4 !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em !important;
    }

    :global(p) {
        font-family: 'Saira', sans-serif !important;
    }

    /* ── Header bar ── */
    :global(header) {
        background: #08080e !important;
        border-bottom-color: #1c1c2e !important;
    }

    /* ── Hide Evidence dev-mode query viewers ── */
    :global(.over-container) {
        display: none !important;
    }

    /* ── Racing stripe accent (top of page) ── */
    :global(body::before) {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #E10600 0%, #E10600 40%, #00D2BE 60%, #00D2BE 100%);
        z-index: 9999;
    }

    /* ── Hero section ── */
    :global(.f1-hero) {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
        position: relative;
        background: #0b0b12;
    }

    :global(.f1-hero-badge) {
        display: inline-block;
        font-family: 'Saira Condensed', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: #E10600;
        background: rgba(225, 6, 0, 0.1);
        border: 1px solid rgba(225, 6, 0, 0.25);
        padding: 0.3rem 1rem;
        border-radius: 2px;
        margin-bottom: 1rem;
    }

    :global(.f1-hero-title) {
        font-family: 'Saira Condensed', sans-serif;
        font-weight: 900;
        font-size: 3.2rem;
        line-height: 1;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #f0f0f5;
        margin-bottom: 0.6rem;
    }

    :global(.f1-hero-title span) {
        color: #E10600;
    }

    :global(.f1-hero-sub) {
        font-family: 'Saira', sans-serif;
        font-size: 0.95rem;
        color: #b8b8cc;
        font-weight: 400;
        max-width: 520px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* ── Controls bar ── */
    :global(.f1-controls) {
        display: flex;
        gap: 1rem;
        align-items: flex-end;
        padding: 1rem 1.5rem;
        background: #12121e;
        border: 1px solid #1c1c2e;
        border-radius: 6px;
        margin: 1rem 0 2rem;
    }

    /* ── Driver legend ── */
    :global(.f1-driver-legend) {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        background: #12121e;
        border: 1px solid #1c1c2e;
        border-radius: 6px;
        margin: -0.5rem 0 1.5rem;
        font-family: 'Saira Condensed', sans-serif;
        font-size: 1.1rem;
        letter-spacing: 0.03em;
    }
    :global(.f1-driver-chip) {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    :global(.f1-driver-chip.red) {
        background: rgba(225, 6, 0, 0.2);
        border: 1px solid #E10600;
        color: #E10600;
    }
    :global(.f1-driver-chip.teal) {
        background: rgba(0, 210, 190, 0.2);
        border: 1px solid #00D2BE;
        color: #00D2BE;
    }
    :global(.f1-driver-fullname) {
        color: #c8c8d4;
        font-weight: 400;
    }
    :global(.f1-driver-vs) {
        color: #666;
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        margin: 0 0.3rem;
    }

    /* ── Section container ── */
    :global(.f1-section) {
        background: #12121e !important;
        border: 1px solid #1c1c2e;
        border-radius: 6px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }

    :global(.f1-section::before) {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: #E10600;
        border-radius: 6px 0 0 6px;
    }

    :global(.f1-section.teal::before) {
        background: #00D2BE;
    }

    :global(.f1-section.blue::before) {
        background: #3671C6;
    }

    :global(.f1-section.orange::before) {
        background: #FF8000;
    }

    :global(.f1-section.green::before) {
        background: #00C853;
    }

    :global(.f1-section.purple::before) {
        background: #9C27B0;
    }

    :global(.f1-section.amber::before) {
        background: #FF6F00;
    }

    :global(.f1-section.cyan::before) {
        background: #00BCD4;
    }

    /* ── Section header ── */
    :global(.f1-section-title) {
        font-family: 'Saira Condensed', sans-serif;
        font-weight: 800;
        font-size: 1.3rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #f0f0f5;
        margin: 0 0 0.3rem 0;
        padding: 0;
    }

    :global(.f1-section-subtitle) {
        font-family: 'Saira', sans-serif;
        font-size: 0.8rem;
        color: #b8b8cc;
        margin: 0 0 1.25rem 0;
        font-weight: 400;
    }

    /* ── Stats grid ── */
    :global(.f1-stats-row) {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1.25rem;
        flex-wrap: wrap;
    }

    :global(.f1-stat-card) {
        flex: 1;
        min-width: 140px;
        background: #0b0b12 !important;
        border: 1px solid #1c1c2e;
        border-radius: 4px;
        padding: 0.9rem 1rem;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    :global(.f1-stat-card:hover) {
        border-color: #2a2a40;
        box-shadow: 0 0 20px rgba(225, 6, 0, 0.06);
    }

    /* Style BigValue components inside stat cards */
    :global(.f1-stat-card > div) {
        padding: 0 !important;
        margin: 0 !important;
    }

    :global(.f1-stat-card p) {
        font-family: 'Saira Condensed', sans-serif !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        color: #b8b8cc !important;
    }

    :global(.f1-stat-card .text-xl) {
        font-family: 'Saira', sans-serif !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #f0f0f5 !important;
        line-height: 1.2 !important;
    }

    :global(.f1-stat-card.accent-red .text-xl) {
        color: #E10600 !important;
    }

    :global(.f1-stat-card.accent-teal .text-xl) {
        color: #00D2BE !important;
    }

    :global(.f1-stat-card.accent-orange .text-xl) {
        color: #FF8000 !important;
    }

    /* ── Chart container ── */
    :global(.f1-chart-wrap) {
        background: #0b0b12 !important;
        border: 1px solid #1c1c2e;
        border-radius: 4px;
        padding: 1rem;
        margin-top: 0.75rem;
    }

    :global(.f1-chart-wrap + .f1-chart-wrap) {
        margin-top: 1rem;
    }

    :global(.f1-chart-label) {
        font-family: 'Saira Condensed', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #b8b8cc;
        margin-bottom: 0.5rem;
    }

    :global(.f1-chart-note) {
        font-family: 'Saira', sans-serif;
        font-size: 0.7rem;
        color: #b8b8cc;
        margin-top: 0.25rem;
        font-style: italic;
    }

    :global(.f1-detail-table) {
        max-height: 320px;
        overflow-y: auto;
    }

    /* ── Season Scorecard ── */
    :global(.f1-scorecard) {
        background: #12121e;
        border: 1px solid #1c1c2e;
        border-radius: 6px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    :global(.f1-scorecard-title) {
        font-family: 'Saira Condensed', sans-serif;
        font-weight: 800;
        font-size: 1.1rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b6b80;
        text-align: center;
        margin-bottom: 1rem;
    }

    :global(.f1-verdict-grid) {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        justify-content: center;
    }

    :global(.f1-verdict-card) {
        flex: 1;
        min-width: 130px;
        max-width: 180px;
        background: #0b0b12;
        border: 1px solid #1c1c2e;
        border-radius: 4px;
        padding: 1rem;
        text-align: center;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    :global(.f1-verdict-card.winner-d1) {
        border-color: rgba(225, 6, 0, 0.4);
        box-shadow: 0 0 16px rgba(225, 6, 0, 0.08);
    }

    :global(.f1-verdict-card.winner-d2) {
        border-color: rgba(0, 210, 190, 0.4);
        box-shadow: 0 0 16px rgba(0, 210, 190, 0.08);
    }

    :global(.f1-verdict-card.winner-tie) {
        border-color: #2a2a40;
    }

    :global(.f1-verdict-label) {
        font-family: 'Saira Condensed', sans-serif;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #6b6b80;
        margin-bottom: 0.4rem;
    }

    :global(.f1-verdict-winner) {
        font-family: 'Saira Condensed', sans-serif;
        font-size: 1.6rem;
        font-weight: 900;
        letter-spacing: 0.06em;
        line-height: 1.2;
    }

    :global(.winner-d1 .f1-verdict-winner) {
        color: #E10600;
    }

    :global(.winner-d2 .f1-verdict-winner) {
        color: #00D2BE;
    }

    :global(.winner-tie .f1-verdict-winner) {
        color: #6b6b80;
    }

    :global(.f1-verdict-detail) {
        font-family: 'Saira', sans-serif;
        font-size: 0.72rem;
        color: #b8b8cc;
        margin-top: 0.25rem;
    }

    /* ── Horizontal rules / dividers ── */
    :global(hr) {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, #1c1c2e 20%, #1c1c2e 80%, transparent) !important;
        margin: 2rem 0 !important;
    }

    /* ── FIX: SVG icon sizing — Evidence uses width="100%" height="100%" on SVGs ── */
    :global(svg[width="100%"][height="100%"]) {
        width: 1rem !important;
        height: 1rem !important;
    }

    :global(button svg),
    :global([data-button-root] svg),
    :global([data-popover-trigger] svg),
    :global(th svg),
    :global(thead svg),
    :global(.table-footer svg),
    :global(span svg) {
        width: 1rem !important;
        height: 1rem !important;
        min-width: 0.75rem;
        min-height: 0.75rem;
        max-width: 1.25rem;
        max-height: 1.25rem;
        flex-shrink: 0;
    }

    /* Don't constrain chart SVGs */
    :global(.f1-chart-wrap svg:not([width="100%"])),
    :global(.echarts svg),
    :global(canvas + svg) {
        width: auto !important;
        height: auto !important;
        max-width: none !important;
        max-height: none !important;
    }

    /* ── Dropdown button overrides (Evidence uses button, not select) ── */
    :global([data-popover-trigger]),
    :global([data-melt-popover-trigger]) {
        font-family: 'Saira', sans-serif !important;
        background: #0b0b12 !important;
        border: 1px solid #2a2a40 !important;
        color: #c8c8d4 !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
        transition: border-color 0.2s ease !important;
    }

    :global([data-popover-trigger]:hover),
    :global([data-melt-popover-trigger]:hover) {
        border-color: #E10600 !important;
        background: #12121e !important;
    }

    /* Evidence popover content (dropdown options) */
    :global([data-popover-content]),
    :global([data-melt-popover-content]) {
        background: #12121e !important;
        border: 1px solid #2a2a40 !important;
        color: #c8c8d4 !important;
    }

    :global([data-popover-content] button),
    :global([data-melt-popover-content] button) {
        color: #c8c8d4 !important;
    }

    :global([data-popover-content] button:hover),
    :global([data-melt-popover-content] button:hover) {
        background: #1c1c2e !important;
    }

    :global([data-popover-content] input),
    :global([data-melt-popover-content] input) {
        background: #0b0b12 !important;
        border-color: #2a2a40 !important;
        color: #c8c8d4 !important;
    }

    /* Also keep native select/input styling */
    :global(select), :global(input) {
        font-family: 'Saira', sans-serif !important;
        background: #0b0b12 !important;
        border: 1px solid #2a2a40 !important;
        color: #c8c8d4 !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
    }

    :global(select:focus), :global(input:focus) {
        border-color: #E10600 !important;
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(225, 6, 0, 0.15) !important;
    }

    /* ── DataTable overrides ── */
    :global(table) {
        font-family: 'Saira', sans-serif !important;
        font-size: 0.82rem !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        width: 100% !important;
        table-layout: fixed !important;
    }

    :global(thead th) {
        font-family: 'Saira Condensed', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        color: #b8b8cc !important;
        background: #0b0b12 !important;
        border-bottom: 2px solid #E10600 !important;
        padding: 0.6rem 0.75rem !important;
        white-space: nowrap !important;
    }

    /* Visual divider between Driver 1 and Driver 2 column groups */
    :global(thead th:nth-child(6)),
    :global(tbody td:nth-child(6)) {
        border-left: 2px solid #2a2a40 !important;
        padding-left: 1rem !important;
    }

    /* Winner column accent */
    :global(thead th:nth-child(10)),
    :global(tbody td:nth-child(10)) {
        border-left: 2px solid #2a2a40 !important;
        padding-left: 1rem !important;
    }

    /* Evidence DataTable doesn't use standard <tbody> — target td directly */
    :global(td) {
        padding: 0.5rem 0.75rem !important;
        border-bottom: 1px solid #1c1c2e !important;
        color: #c8c8d4 !important;
    }

    :global(tr:hover td) {
        background: rgba(225, 6, 0, 0.04) !important;
    }

    :global(tr:nth-child(even) td) {
        background: rgba(18, 18, 30, 0.5) !important;
    }

    :global(tr:nth-child(even):hover td) {
        background: rgba(225, 6, 0, 0.06) !important;
    }

    /* ── Lap pace controls ── */
    :global(.f1-inline-control) {
        display: inline-flex;
        align-items: flex-end;
        gap: 0.75rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }

    /* ── Section Navigation ── */
    :global(.f1-section-nav) {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        justify-content: center;
        padding: 0.6rem 1rem;
        background: #12121e;
        border: 1px solid #1c1c2e;
        border-radius: 6px;
        margin-bottom: 1.5rem;
        position: sticky;
        top: 6px;
        z-index: 100;
        backdrop-filter: blur(12px);
        background: rgba(18, 18, 30, 0.92);
    }

    :global(.f1-nav-pill) {
        font-family: 'Saira Condensed', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        text-decoration: none;
        padding: 0.3rem 0.7rem;
        border-radius: 3px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }

    :global(.f1-nav-pill.red) {
        color: #E10600;
        background: rgba(225, 6, 0, 0.08);
    }
    :global(.f1-nav-pill.red:hover) {
        background: rgba(225, 6, 0, 0.2);
        border-color: rgba(225, 6, 0, 0.3);
    }

    :global(.f1-nav-pill.teal) {
        color: #00D2BE;
        background: rgba(0, 210, 190, 0.08);
    }
    :global(.f1-nav-pill.teal:hover) {
        background: rgba(0, 210, 190, 0.2);
        border-color: rgba(0, 210, 190, 0.3);
    }

    :global(.f1-nav-pill.blue) {
        color: #3671C6;
        background: rgba(54, 113, 198, 0.08);
    }
    :global(.f1-nav-pill.blue:hover) {
        background: rgba(54, 113, 198, 0.2);
        border-color: rgba(54, 113, 198, 0.3);
    }

    :global(.f1-nav-pill.green) {
        color: #00C853;
        background: rgba(0, 200, 83, 0.08);
    }
    :global(.f1-nav-pill.green:hover) {
        background: rgba(0, 200, 83, 0.2);
        border-color: rgba(0, 200, 83, 0.3);
    }

    :global(.f1-nav-pill.purple) {
        color: #9C27B0;
        background: rgba(156, 39, 176, 0.08);
    }
    :global(.f1-nav-pill.purple:hover) {
        background: rgba(156, 39, 176, 0.2);
        border-color: rgba(156, 39, 176, 0.3);
    }

    :global(.f1-nav-pill.amber) {
        color: #FF6F00;
        background: rgba(255, 111, 0, 0.08);
    }
    :global(.f1-nav-pill.amber:hover) {
        background: rgba(255, 111, 0, 0.2);
        border-color: rgba(255, 111, 0, 0.3);
    }

    :global(.f1-nav-pill.cyan) {
        color: #00BCD4;
        background: rgba(0, 188, 212, 0.08);
    }
    :global(.f1-nav-pill.cyan:hover) {
        background: rgba(0, 188, 212, 0.2);
        border-color: rgba(0, 188, 212, 0.3);
    }

    :global(.f1-nav-pill.orange) {
        color: #FF8000;
        background: rgba(255, 128, 0, 0.08);
    }
    :global(.f1-nav-pill.orange:hover) {
        background: rgba(255, 128, 0, 0.2);
        border-color: rgba(255, 128, 0, 0.3);
    }

    /* Smooth scroll for anchor links */
    :global(html) {
        scroll-behavior: smooth;
        scroll-padding-top: 60px;
    }

    /* ── Fade-in animation ── */
    :global(.f1-section) {
        animation: f1FadeUp 0.5s ease-out both;
    }

    :global(.f1-section:nth-child(2)) { animation-delay: 0.08s; }
    :global(.f1-section:nth-child(3)) { animation-delay: 0.16s; }
    :global(.f1-section:nth-child(4)) { animation-delay: 0.24s; }
    :global(.f1-section:nth-child(5)) { animation-delay: 0.32s; }
    :global(.f1-section:nth-child(6)) { animation-delay: 0.40s; }
    :global(.f1-section:nth-child(7)) { animation-delay: 0.48s; }
    :global(.f1-section:nth-child(8)) { animation-delay: 0.56s; }
    :global(.f1-section:nth-child(9)) { animation-delay: 0.64s; }
    :global(.f1-section:nth-child(10)) { animation-delay: 0.72s; }

    @keyframes -global-f1FadeUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* ── Responsive ── */
    @media (max-width: 640px) {
        :global(.f1-hero-title) {
            font-size: 2.2rem;
        }
        :global(.f1-controls) {
            flex-direction: column;
        }
        :global(.f1-stats-row) {
            flex-direction: column;
        }
    }
</style>
