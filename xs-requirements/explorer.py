#!/usr/bin/env python3
"""xs Requirements Explorer — browse stories, epics, principles, conflicts."""

import http.server
import json
import os
import re
import socketserver
import sys
import webbrowser
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required. Run: uv run --with pyyaml python3 explorer.py")
    sys.exit(1)

BASE_DIR = Path(__file__).parent

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def regex_extract(text, field):
    """Fallback: extract a YAML field value via regex when full parse fails."""
    m = re.search(rf'^{field}:\s*(.+)', text, re.MULTILINE)
    return m.group(1).strip().strip('"').strip("'") if m else None

def load_with_fallback(path, fallback_fields):
    """Try YAML parse; on failure extract key fields via regex."""
    text = path.read_text()
    try:
        return yaml.safe_load(text)
    except Exception as e:
        result = {"_parse_error": str(e).split('\n')[0]}
        for field in fallback_fields:
            val = regex_extract(text, field)
            if val:
                result[field] = val
        return result

def load_all_stories():
    stories = []
    for p in sorted(BASE_DIR.glob("stories/**/*.yaml")):
        data = load_with_fallback(p, ["id", "title", "epic", "theme", "status"])
        if "_parse_error" in data:
            data.setdefault("id", p.stem.split("-", 1)[0] if "-" in p.stem else p.stem)
            data.setdefault("title", f"(YAML parse error)")
            data.setdefault("epic", p.parent.name)

        stories.append(data)
    return stories

def load_all_epics():
    epics = []
    for p in sorted(BASE_DIR.glob("epics/*.yaml")):
        data = load_with_fallback(p, ["id", "name", "description"])
        if "_parse_error" in data:
            data.setdefault("id", p.stem)
            data.setdefault("name", f"(YAML parse error)")
        epics.append(data)
    return epics

def load_all_principles():
    principles = []
    for p in sorted(BASE_DIR.glob("principles/PRIN-*.yaml")):
        data = load_with_fallback(p, ["id", "title", "statement"])
        if "_parse_error" in data:
            data.setdefault("id", p.stem)
            data.setdefault("title", f"(YAML parse error)")
        principles.append(data)
    return principles

def load_all_conflicts():
    conflicts = []
    for p in sorted(BASE_DIR.glob("conflicts/CONF-*.yaml")):
        data = load_with_fallback(p, ["id", "title", "resolution"])
        if "_parse_error" in data:
            data.setdefault("id", p.stem)
            data.setdefault("title", f"(YAML parse error)")
        conflicts.append(data)
    return conflicts

def load_analysis():
    p = BASE_DIR / "synthesis" / "pass6-story-analysis.yaml"
    if p.exists():
        data = load_yaml(p)
        return {s["id"]: s for s in data.get("stories", [])}
    return {}

def load_roadmap():
    p = BASE_DIR / "roadmap.yaml"
    if p.exists():
        return load_yaml(p)
    return {}

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>xs Requirements Explorer</title>
<style>
:root {
  --bg: #1a1a2e;
  --surface: #16213e;
  --surface2: #0f3460;
  --text: #e0e0e0;
  --text-muted: #8a8a9a;
  --accent: #e94560;
  --must: #e94560;
  --should: #f5a623;
  --could: #7ed6df;
  --ready: #2ecc71;
  --beefup: #f39c12;
  --split: #9b59b6;
  --merge: #3498db;
  --reframe: #e67e22;
  --border: #2a2a4a;
  --resolved: #2ecc71;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
}

header h1 {
  font-size: 1.4rem;
  font-weight: 600;
}

.stats {
  display: flex;
  gap: 16px;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.stats .stat-val { color: var(--text); font-weight: 600; }

/* Tabs */
.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 2px solid var(--border);
}

.tab {
  padding: 10px 20px;
  cursor: pointer;
  border: none;
  background: none;
  color: var(--text-muted);
  font-size: 0.95rem;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.15s;
}

.tab:hover { color: var(--text); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }

.tab-badge {
  display: inline-block;
  background: var(--surface2);
  color: var(--text-muted);
  padding: 1px 7px;
  border-radius: 10px;
  font-size: 0.75rem;
  margin-left: 6px;
}

.tab.active .tab-badge { background: var(--accent); color: #fff; }

/* Controls bar */
.controls {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  align-items: center;
}

.search-box {
  flex: 1;
  min-width: 200px;
  padding: 8px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-size: 0.9rem;
  outline: none;
}

.search-box:focus { border-color: var(--accent); }

.filter-pills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.pill {
  padding: 4px 12px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: none;
  color: var(--text-muted);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s;
}

.pill:hover { border-color: var(--text-muted); color: var(--text); }
.pill.active { border-color: var(--accent); color: var(--accent); background: rgba(233,69,96,0.1); }

.pill.readiness-ready.active { border-color: var(--ready); color: var(--ready); background: rgba(46,204,113,0.1); }
.pill.readiness-beefup.active { border-color: var(--beefup); color: var(--beefup); background: rgba(243,156,18,0.1); }
.pill.readiness-split.active { border-color: var(--split); color: var(--split); background: rgba(155,89,182,0.1); }
.pill.readiness-merge.active { border-color: var(--merge); color: var(--merge); background: rgba(52,152,219,0.1); }
.pill.readiness-reframe.active { border-color: var(--reframe); color: var(--reframe); background: rgba(230,126,34,0.1); }

/* Group headers */
.group-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  margin-top: 12px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  user-select: none;
}

.group-header h2 {
  font-size: 1.1rem;
  font-weight: 600;
}

.group-header .count {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.group-header .chevron {
  margin-left: auto;
  color: var(--text-muted);
  transition: transform 0.2s;
}

.group-header.collapsed .chevron { transform: rotate(-90deg); }

/* Cards */
.cards { padding: 4px 0; }
.cards.collapsed { display: none; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin: 6px 0;
  overflow: hidden;
  transition: border-color 0.15s;
}

.card:hover { border-color: var(--text-muted); }

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
}

.card-id {
  font-family: "SF Mono", Monaco, Consolas, monospace;
  font-size: 0.8rem;
  color: var(--accent);
  min-width: 60px;
}

.card-title {
  flex: 1;
  font-size: 0.9rem;
}

.card-badges {
  display: flex;
  gap: 6px;
  align-items: center;
}

.badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.badge-must { background: rgba(233,69,96,0.2); color: var(--must); }
.badge-should { background: rgba(245,166,35,0.2); color: var(--should); }
.badge-could { background: rgba(126,214,223,0.2); color: var(--could); }

.badge-ready { background: rgba(46,204,113,0.15); color: var(--ready); }
.badge-beefup { background: rgba(243,156,18,0.15); color: var(--beefup); }
.badge-split { background: rgba(155,89,182,0.15); color: var(--split); }
.badge-merge { background: rgba(52,152,219,0.15); color: var(--merge); }
.badge-reframe { background: rgba(230,126,34,0.15); color: var(--reframe); }
.badge-resolved { background: rgba(46,204,113,0.15); color: var(--resolved); }

.card-chevron {
  color: var(--text-muted);
  transition: transform 0.2s;
  font-size: 0.8rem;
}

.card.expanded .card-chevron { transform: rotate(90deg); }

.card-body {
  display: none;
  padding: 0 14px 14px;
  border-top: 1px solid var(--border);
}

.card.expanded .card-body { display: block; }

.card-body section {
  margin-top: 12px;
}

.card-body section h4 {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.user-story {
  font-style: italic;
  color: var(--text-muted);
  font-size: 0.9rem;
  padding: 8px 12px;
  background: rgba(255,255,255,0.03);
  border-radius: 4px;
  border-left: 3px solid var(--accent);
}

.ac-list {
  list-style: none;
}

.ac-item {
  padding: 6px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  font-size: 0.85rem;
}

.ac-item:last-child { border-bottom: none; }

.ac-id {
  font-family: "SF Mono", Monaco, Consolas, monospace;
  font-size: 0.75rem;
  color: var(--accent);
  margin-right: 6px;
}

.ac-gwt { color: var(--text-muted); }
.ac-gwt strong { color: var(--text); font-weight: 500; }

.dep-list, .rel-list {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.dep-link {
  font-family: "SF Mono", Monaco, Consolas, monospace;
  font-size: 0.8rem;
  padding: 2px 8px;
  background: var(--surface2);
  border-radius: 4px;
  cursor: pointer;
  color: var(--accent);
}

.dep-link:hover { background: rgba(233,69,96,0.2); }

.source-item {
  font-size: 0.82rem;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.source-item:last-child { border-bottom: none; }

.source-ref {
  font-family: "SF Mono", Monaco, Consolas, monospace;
  color: var(--accent);
  font-size: 0.78rem;
}

.source-quote {
  color: var(--text-muted);
  font-style: italic;
  display: block;
  margin-top: 2px;
}

.source-context {
  color: var(--text-muted);
  font-size: 0.78rem;
  opacity: 0.7;
  display: block;
  margin-top: 1px;
}

/* Statement / rationale blocks */
.statement-block {
  padding: 10px 14px;
  background: rgba(255,255,255,0.03);
  border-radius: 4px;
  border-left: 3px solid var(--accent);
  font-size: 0.9rem;
  white-space: pre-wrap;
}

.impl-list {
  list-style: disc;
  padding-left: 20px;
}

.impl-list li {
  font-size: 0.85rem;
  padding: 3px 0;
}

/* Options (conflicts) */
.option-card {
  background: rgba(255,255,255,0.03);
  border-radius: 4px;
  padding: 10px 14px;
  margin: 6px 0;
  border-left: 3px solid var(--border);
}

.option-card.selected { border-left-color: var(--resolved); }

.option-card h5 {
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.option-card .pros-cons {
  display: flex;
  gap: 16px;
  font-size: 0.8rem;
}

.option-card .pros { color: var(--ready); }
.option-card .cons { color: var(--must); }

.resolution-block {
  padding: 10px 14px;
  background: rgba(46,204,113,0.08);
  border-radius: 4px;
  border-left: 3px solid var(--resolved);
  font-size: 0.9rem;
  white-space: pre-wrap;
}

/* Slice / roadmap view */
.slice-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  margin-top: 16px;
  border-bottom: 2px solid var(--accent);
}

.slice-header h2 {
  font-size: 1.1rem;
}

.slice-header .slice-id {
  font-family: "SF Mono", Monaco, Consolas, monospace;
  font-size: 0.85rem;
  color: var(--accent);
  background: rgba(233,69,96,0.15);
  padding: 2px 8px;
  border-radius: 4px;
}

.validation-notes {
  padding: 8px 12px;
  background: rgba(255,255,255,0.03);
  border-radius: 4px;
  font-size: 0.85rem;
  color: var(--text-muted);
  white-space: pre-wrap;
}

.panel { display: none; }
.panel.active { display: block; }

/* Scrollbar */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* Summary counts */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.summary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px;
  text-align: center;
}

.summary-card .num {
  font-size: 1.8rem;
  font-weight: 700;
}

.summary-card .label {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.epic-capabilities {
  list-style: none;
  padding: 0;
}

.epic-capabilities li {
  font-size: 0.85rem;
  padding: 3px 0;
  color: var(--text-muted);
}

.epic-capabilities li::before {
  content: "\2022 ";
  color: var(--accent);
}

.analysis-note {
  font-size: 0.82rem;
  color: var(--text-muted);
  font-style: italic;
  margin-top: 4px;
}

/* ═══ Story Map ═══ */
.map-container {
  overflow-x: auto;
  padding-bottom: 20px;
}

.map-header-row {
  display: flex;
  gap: 2px;
  padding-left: 100px;
  margin-bottom: 2px;
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--bg);
}

.map-activity-hdr {
  min-width: 130px;
  max-width: 130px;
  background: #c04870;
  color: #fff;
  font-weight: 600;
  font-size: 0.78rem;
  padding: 7px 8px;
  border-radius: 2px;
  text-align: center;
  box-shadow: 1px 2px 3px rgba(0,0,0,0.35);
}

.map-band {
  display: flex;
  align-items: stretch;
  min-height: 40px;
  margin-bottom: 2px;
}

.band-label {
  min-width: 96px;
  max-width: 96px;
  padding: 6px 6px 6px 0;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--accent);
  text-align: right;
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  border-right: 2px solid var(--accent);
  margin-right: 2px;
}

.band-label.skeleton { color: var(--ready); border-right-color: var(--ready); }
.band-label.core { color: var(--should); border-right-color: var(--should); }
.band-label.power { color: var(--could); border-right-color: var(--could); }
.band-label.integration { color: var(--text-muted); border-right-color: var(--text-muted); }

.band-cells {
  display: flex;
  gap: 2px;
  flex: 1;
}

.map-cell {
  min-width: 130px;
  max-width: 130px;
  padding: 3px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.sticky {
  padding: 5px 7px;
  border-radius: 1px;
  font-size: 0.72rem;
  line-height: 1.3;
  cursor: pointer;
  box-shadow: 1px 1px 2px rgba(0,0,0,0.25);
  transition: transform 0.1s, box-shadow 0.1s;
  position: relative;
  color: #2a2a2a;
  min-height: 28px;
  background: #fef3b5;
}

.sticky:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow: 2px 3px 6px rgba(0,0,0,0.35);
  z-index: 5;
}

.sticky .sticky-id {
  font-size: 0.6rem;
  opacity: 0.5;
  font-family: "SF Mono", Monaco, Consolas, monospace;
  display: block;
  margin-bottom: 1px;
}

.sticky .sticky-title {
  display: block;
  font-weight: 500;
}

/* Readiness indicators */
.sticky.r-ready          { border-left: 3px solid #2ecc71; }
.sticky.r-needs-beefing-up { border-left: 3px solid #f39c12; }
.sticky.r-needs-splitting  { border-left: 3px solid #9b59b6; }
.sticky.r-merge-candidate  { border-left: 3px solid #3498db; }
.sticky.r-needs-reframing  { border-left: 3px solid #e67e22; }

/* Detail panel */
.map-detail {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  height: 100vh;
  background: var(--surface);
  border-left: 2px solid var(--accent);
  padding: 16px;
  overflow-y: auto;
  z-index: 100;
  display: none;
  box-shadow: -4px 0 20px rgba(0,0,0,0.4);
}

.map-detail.open { display: block; }

.map-detail-close {
  position: absolute;
  top: 10px;
  right: 12px;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 1.2rem;
  cursor: pointer;
}

.map-detail h3 {
  font-size: 1rem;
  margin-bottom: 4px;
}

.map-detail .detail-id {
  font-family: "SF Mono", Monaco, Consolas, monospace;
  color: var(--accent);
  font-size: 0.85rem;
}

.map-detail section {
  margin-top: 10px;
}

.map-detail section h4 {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-bottom: 4px;
}

.map-legend {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  padding: 8px 0;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--border);
  font-size: 0.75rem;
  color: var(--text-muted);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid transparent;
  transition: all 0.15s;
  user-select: none;
}

.legend-item:hover { border-color: var(--text-muted); }
.legend-item.active { border-color: var(--accent); background: rgba(233,69,96,0.1); }
.legend-item.dimmed { opacity: 0.3; }

.legend-swatch {
  width: 14px;
  height: 14px;
  border-radius: 1px;
  box-shadow: 1px 1px 1px rgba(0,0,0,0.2);
}

.sticky.filtered-out { display: none; }
</style>
</head>
<body>
<div class="app">
  <header>
    <h1>xs Requirements Explorer</h1>
    <div class="stats" id="stats"></div>
  </header>

  <div class="tabs" id="tabs">
    <button class="tab active" data-panel="map">Map</button>
    <button class="tab" data-panel="stories">Stories <span class="tab-badge" id="stories-count"></span></button>
    <button class="tab" data-panel="roadmap">Roadmap <span class="tab-badge" id="roadmap-count"></span></button>
    <button class="tab" data-panel="epics">Epics <span class="tab-badge" id="epics-count"></span></button>
    <button class="tab" data-panel="principles">Principles <span class="tab-badge" id="principles-count"></span></button>
    <button class="tab" data-panel="conflicts">Conflicts <span class="tab-badge" id="conflicts-count"></span></button>
  </div>

  <!-- Map Panel -->
  <div class="panel active" id="panel-map">
    <div class="map-legend" id="map-legend"></div>
    <div class="map-container" id="map-container"></div>
    <div class="map-detail" id="map-detail">
      <button class="map-detail-close" onclick="closeDetail()">&times;</button>
      <div id="map-detail-content"></div>
    </div>
  </div>

  <!-- Stories Panel -->
  <div class="panel" id="panel-stories">
    <div class="controls">
      <input type="text" class="search-box" id="story-search" placeholder="Search stories by ID, title, or content...">
      <div class="filter-pills" id="readiness-filters">
        <button class="pill readiness-ready active" data-readiness="ready">ready</button>
        <button class="pill readiness-beefup active" data-readiness="needs-beefing-up">beef up</button>
        <button class="pill readiness-split active" data-readiness="needs-splitting">split</button>
        <button class="pill readiness-merge active" data-readiness="merge-candidate">merge</button>
        <button class="pill readiness-reframe active" data-readiness="needs-reframing">reframe</button>
      </div>
    </div>
    <div id="stories-container"></div>
  </div>

  <!-- Roadmap Panel -->
  <div class="panel" id="panel-roadmap">
    <div class="controls">
      <input type="text" class="search-box" id="roadmap-search" placeholder="Search roadmap...">
    </div>
    <div id="roadmap-container"></div>
  </div>

  <!-- Epics Panel -->
  <div class="panel" id="panel-epics">
    <div id="epics-container"></div>
  </div>

  <!-- Principles Panel -->
  <div class="panel" id="panel-principles">
    <div id="principles-container"></div>
  </div>

  <!-- Conflicts Panel -->
  <div class="panel" id="panel-conflicts">
    <div id="conflicts-container"></div>
  </div>
</div>

<script>
let DATA = {};

async function loadData() {
  const resp = await fetch('/api/data');
  DATA = await resp.json();

  document.getElementById('stories-count').textContent = DATA.stories.length;
  document.getElementById('epics-count').textContent = DATA.epics.length;
  document.getElementById('principles-count').textContent = DATA.principles.length;
  document.getElementById('conflicts-count').textContent = DATA.conflicts.length;
  document.getElementById('roadmap-count').textContent = DATA.roadmap.slices ? DATA.roadmap.slices.length : 0;

  document.getElementById('stats').innerHTML =
    `<span><span class="stat-val">${DATA.stories.length}</span> stories</span>`;

  renderMap();
  renderStories();
  renderRoadmap();
  renderEpics();
  renderPrinciples();
  renderConflicts();
}

function esc(s) {
  if (s == null) return '';
  const div = document.createElement('div');
  div.textContent = String(s);
  return div.innerHTML;
}

function getAnalysis(id) {
  return DATA.analysis[id] || {};
}

function readinessBadge(readiness) {
  if (!readiness) return '';
  const cls = {
    'ready': 'badge-ready',
    'needs-beefing-up': 'badge-beefup',
    'needs-splitting': 'badge-split',
    'merge-candidate': 'badge-merge',
    'needs-reframing': 'badge-reframe',
  }[readiness] || '';
  const label = {
    'ready': 'ready',
    'needs-beefing-up': 'beef up',
    'needs-splitting': 'split',
    'merge-candidate': 'merge',
    'needs-reframing': 'reframe',
  }[readiness] || readiness;
  return `<span class="badge ${cls}">${esc(label)}</span>`;
}

function renderACs(acs) {
  if (!acs || !acs.length) return '<p style="color:var(--text-muted);font-size:0.85rem;">No acceptance criteria defined.</p>';
  return '<ul class="ac-list">' + acs.map(ac => {
    const given = ac.given ? `<strong>Given</strong> ${esc(ac.given)}` : '';
    const when = ac.when ? ` <strong>when</strong> ${esc(ac.when)}` : '';
    const then = ac.then ? ` <strong>then</strong> ${esc(ac.then)}` : '';
    return `<li class="ac-item"><span class="ac-id">${esc(ac.id)}</span><span class="ac-gwt">${given}${when}${then}</span></li>`;
  }).join('') + '</ul>';
}

function renderSources(sources) {
  if (!sources || !sources.length) return '';
  return '<div>' + sources.map(s => {
    const ref = s.session || s.file || s.source || '';
    return `<div class="source-item"><span class="source-ref">${esc(ref)}</span>` +
      (s.quote ? `<span class="source-quote">"${esc(s.quote)}"</span>` : '') +
      (s.context ? `<span class="source-context">${esc(s.context)}</span>` : '') +
      (s.observation ? `<span class="source-quote">${esc(s.observation)}</span>` : '') +
      `</div>`;
  }).join('') + '</div>';
}

function renderDeps(deps, label) {
  if (!deps || !deps.length) return '';
  return `<section><h4>${label}</h4><div class="dep-list">` +
    deps.map(d => `<span class="dep-link" onclick="navigateTo('${esc(d)}')">${esc(d)}</span>`).join('') +
    '</div></section>';
}

function navigateTo(id) {
  // Switch to appropriate tab and expand the card
  const prefix = id.split('-')[0];
  let panel = 'stories';
  if (prefix === 'PRIN') panel = 'principles';
  else if (prefix === 'CONF') panel = 'conflicts';

  switchTab(panel);

  setTimeout(() => {
    const card = document.querySelector(`[data-card-id="${id}"]`);
    if (card) {
      card.classList.add('expanded');
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, 50);
}

function storyCard(story) {
  const a = getAnalysis(story.id);
  const readiness = a.readiness || '';
  const slice = a.slice || '';
  const acCount = (story.acceptance_criteria || []).length;

  const userStory = (story.as_a && story.i_want && story.so_that)
    ? `<section><h4>User Story</h4><div class="user-story">As a ${esc(story.as_a)}, I want ${esc(story.i_want)}, so that ${esc(story.so_that)}</div></section>`
    : '';

  const analysisNote = a.notes
    ? `<section><h4>Analysis Notes</h4><div class="analysis-note">${esc(a.notes)}</div></section>`
    : '';

  const validationNotes = story.validation_notes
    ? `<section><h4>Validation Notes</h4><div class="validation-notes">${esc(story.validation_notes)}</div></section>`
    : '';

  const parseError = story._parse_error
    ? `<section><h4>YAML Parse Error</h4><div class="validation-notes" style="border-left:3px solid var(--must);color:var(--must)">${esc(story._parse_error)}</div></section>`
    : '';

  return `
    <div class="card" data-card-id="${esc(story.id)}" data-readiness="${esc(readiness)}" data-searchable="${esc((story.id + ' ' + story.title + ' ' + (story.as_a||'') + ' ' + (story.i_want||'') + ' ' + (story.so_that||'')).toLowerCase())}">
      <div class="card-header" onclick="this.parentElement.classList.toggle('expanded')">
        <span class="card-id">${esc(story.id)}</span>
        <span class="card-title">${esc(story.title)}${story._parse_error ? ' <span style="color:var(--must)">[YAML error]</span>' : ''}</span>
        <div class="card-badges">
          ${slice ? `<span class="badge" style="background:var(--surface2);color:var(--text-muted)">${esc(slice)}</span>` : ''}
          ${readinessBadge(readiness)}
          <span style="color:var(--text-muted);font-size:0.75rem;">${acCount} AC</span>
        </div>
        <span class="card-chevron">&#9654;</span>
      </div>
      <div class="card-body">
        ${parseError}
        ${userStory}
        <section><h4>Acceptance Criteria</h4>${renderACs(story.acceptance_criteria)}</section>
        ${renderDeps(story.depends_on, 'Depends On')}
        ${renderDeps(story.related, 'Related')}
        ${story.sources ? `<section><h4>Sources</h4>${renderSources(story.sources)}</section>` : ''}
        ${analysisNote}
        ${validationNotes}
      </div>
    </div>`;
}

// ═══════════════════════════════════════════════
// STORY MAP
// ═══════════════════════════════════════════════

const BACKBONE = [
  { id: 'fetch',     name: 'Fetch from CI',  match: s => s.id?.startsWith('GFH-') },
  { id: 'find',      name: 'Find Session',   match: s => ['PRS-002','PRS-011','CLI-004','CLI-005','CLI-008'].includes(s.id) },
  { id: 'load',      name: 'Load & Parse',   match: s => s.id?.startsWith('PRS-') && !['PRS-002','PRS-011'].includes(s.id) },
  { id: 'summary',   name: 'View Summary',   match: s => s.id?.startsWith('SUM-') || s.id === 'CLI-001' },
  { id: 'browse',    name: 'Browse Timeline', match: s => s.id?.startsWith('DSP-') || s.id?.startsWith('FMT-') || s.id === 'CLI-002' },
  { id: 'filter',    name: 'Filter',         match: s => s.id?.startsWith('FLT-') || ['CLI-003','CLI-006','CLI-009'].includes(s.id) },
  { id: 'range',     name: 'Select Range',   match: s => s.id?.startsWith('RNG-') || s.id === 'CLI-007' },
  { id: 'search',    name: 'Search',         match: s => s.id?.startsWith('SRC-') },
  { id: 'export',    name: 'Export',         match: s => s.id?.startsWith('EXP-') },
  { id: 'sidechain', name: 'Sidechains',     match: s => s.id?.startsWith('SID-') },
  { id: 'recover',   name: 'Recover Context', match: s => s.id?.startsWith('CRH-') },
];

const BANDS = [
  { id: 'skeleton',    name: 'Run xs, see what\u2019s inside',           cls: 'skeleton',    slices: ['walking-skeleton'] },
  { id: 'core',        name: 'Browse, filter, select',                   cls: 'core',        slices: ['summary-mode','compact-timeline','basic-filtering','range-selection','truncated-full-modes'] },
  { id: 'power',       name: 'Search, export, full fidelity',            cls: 'power',       slices: ['search','export','post-filter-head-tail','advanced-display'] },
  { id: 'integration', name: 'Fetch from CI, recover context',           cls: 'integration', slices: ['session-discovery','sidechain','fetch-pipeline','compaction-recovery'] },
];

function renderMap() {
  const container = document.getElementById('map-container');

  // Assign each story to an activity
  const activityMap = {};
  BACKBONE.forEach(a => activityMap[a.id] = []);
  const unmatched = [];

  DATA.stories.forEach(story => {
    const a = getAnalysis(story.id);
    const enriched = { ...story, _readiness: a.readiness || '', _slice: a.slice || '' };
    let placed = false;
    for (const act of BACKBONE) {
      if (act.match(story)) {
        activityMap[act.id].push(enriched);
        placed = true;
        break;
      }
    }
    if (!placed) unmatched.push(enriched);
  });

  // Build legend (clickable filters)
  document.getElementById('map-legend').innerHTML = `
    <span style="font-weight:600;color:var(--text)">Readiness:</span>
    <span class="legend-item" data-filter="readiness" data-value="r-ready" onclick="toggleMapFilter(this)"><span class="legend-swatch" style="background:#fef3b5;border-left:3px solid #2ecc71"></span> ready</span>
    <span class="legend-item" data-filter="readiness" data-value="r-needs-beefing-up" onclick="toggleMapFilter(this)"><span class="legend-swatch" style="background:#fef3b5;border-left:3px solid #f39c12"></span> beef up</span>
    <span class="legend-item" data-filter="readiness" data-value="r-needs-splitting" onclick="toggleMapFilter(this)"><span class="legend-swatch" style="background:#fef3b5;border-left:3px solid #9b59b6"></span> split</span>
    <span class="legend-item" data-filter="readiness" data-value="r-merge-candidate" onclick="toggleMapFilter(this)"><span class="legend-swatch" style="background:#fef3b5;border-left:3px solid #3498db"></span> merge</span>
    <span class="legend-item" data-filter="readiness" data-value="r-needs-reframing" onclick="toggleMapFilter(this)"><span class="legend-swatch" style="background:#fef3b5;border-left:3px solid #e67e22"></span> reframe</span>
    <span style="margin-left:12px"><button onclick="clearMapFilters()" style="background:none;border:1px solid var(--border);color:var(--text-muted);border-radius:3px;padding:1px 8px;font-size:0.7rem;cursor:pointer">clear</button></span>
  `;

  // Activity headers
  let html = '<div class="map-header-row">';
  BACKBONE.forEach(a => {
    const count = activityMap[a.id].length;
    html += `<div class="map-activity-hdr">${esc(a.name)}<br><span style="font-weight:400;font-size:0.65rem;opacity:0.8">${count}</span></div>`;
  });
  html += '</div>';

  // Bands
  BANDS.forEach(band => {
    html += `<div class="map-band"><div class="band-label ${band.cls}">${esc(band.name)}</div><div class="band-cells">`;
    BACKBONE.forEach(act => {
      const stories = activityMap[act.id]
        .filter(s => band.slices.includes(s._slice))
      html += '<div class="map-cell">';
      stories.forEach(s => {
        const rCls = s._readiness ? `r-${s._readiness}` : '';
        html += `<div class="sticky ${rCls}" onclick="showDetail('${esc(s.id)}')" title="${esc(s.id + ': ' + s.title)}">
          <span class="sticky-id">${esc(s.id)}</span>
          <span class="sticky-title">${esc(s.title)}</span>
        </div>`;
      });
      html += '</div>';
    });
    html += '</div></div>';
  });

  // Unmatched stories
  if (unmatched.length) {
    html += `<div class="map-band"><div class="band-label">Unplaced</div><div class="band-cells"><div class="map-cell" style="max-width:none;min-width:auto;flex-wrap:wrap;flex-direction:row">`;
    unmatched.forEach(s => {
      html += `<div class="sticky" onclick="showDetail('${esc(s.id)}')" title="${esc(s.id)}">
        <span class="sticky-id">${esc(s.id)}</span>
        <span class="sticky-title">${esc(s.title)}</span>
      </div>`;
    });
    html += '</div></div></div>';
  }

  container.innerHTML = html;
}

function showDetail(id) {
  const story = DATA.stories.find(s => s.id === id);
  if (!story) return;
  const a = getAnalysis(id);
  const panel = document.getElementById('map-detail');
  const content = document.getElementById('map-detail-content');

  let html = `
    <span class="detail-id">${esc(story.id)}</span>
    <h3>${esc(story.title)}</h3>
    <div class="card-badges" style="margin:6px 0">
      ${readinessBadge(a.readiness)}
      ${a.slice ? `<span class="badge" style="background:var(--surface2);color:var(--text-muted)">${esc(a.slice)}</span>` : ''}
    </div>`;

  if (story.as_a) {
    html += `<section><h4>User Story</h4><div class="user-story">As a ${esc(story.as_a)}, I want ${esc(story.i_want)}, so that ${esc(story.so_that)}</div></section>`;
  }

  html += `<section><h4>Acceptance Criteria</h4>${renderACs(story.acceptance_criteria)}</section>`;

  if (a.notes) {
    html += `<section><h4>Analysis</h4><div class="analysis-note">${esc(a.notes)}</div></section>`;
  }

  if (story.depends_on?.length) {
    html += `<section><h4>Depends On</h4><div class="dep-list">${story.depends_on.map(d => `<span class="dep-link" onclick="showDetail('${esc(d)}')">${esc(d)}</span>`).join('')}</div></section>`;
  }

  if (story.validation_notes) {
    html += `<section><h4>Notes</h4><div class="validation-notes">${esc(story.validation_notes)}</div></section>`;
  }

  content.innerHTML = html;
  panel.classList.add('open');
}

function closeDetail() {
  document.getElementById('map-detail').classList.remove('open');
}

// Close detail on Escape
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDetail(); });

// Map filtering
let activeMapFilter = null; // { type: 'readiness', value: string }

function toggleMapFilter(el) {
  const filterType = el.dataset.filter;
  const filterValue = el.dataset.value;

  // Toggle: if same filter clicked again, clear it
  if (activeMapFilter && activeMapFilter.type === filterType && activeMapFilter.value === filterValue) {
    clearMapFilters();
    return;
  }

  activeMapFilter = { type: filterType, value: filterValue };

  // Update legend item states
  document.querySelectorAll('#map-legend .legend-item').forEach(item => {
    item.classList.remove('active', 'dimmed');
    if (item === el) {
      item.classList.add('active');
    } else {
      item.classList.add('dimmed');
    }
  });

  // Filter stickies
  document.querySelectorAll('#map-container .sticky').forEach(sticky => {
    let match = false;
    if (filterType === 'readiness') {
      match = sticky.classList.contains(filterValue);
    }
    sticky.classList.toggle('filtered-out', !match);
  });

  // Update column counts
  updateMapCounts();
}

function clearMapFilters() {
  activeMapFilter = null;
  document.querySelectorAll('#map-legend .legend-item').forEach(item => {
    item.classList.remove('active', 'dimmed');
  });
  document.querySelectorAll('#map-container .sticky').forEach(sticky => {
    sticky.classList.remove('filtered-out');
  });
  updateMapCounts();
}

function updateMapCounts() {
  document.querySelectorAll('.map-activity-hdr').forEach(hdr => {
    // Count visible stickies in this column
    const idx = Array.from(hdr.parentElement.children).indexOf(hdr);
    let visible = 0;
    document.querySelectorAll('.band-cells').forEach(row => {
      const cell = row.children[idx];
      if (cell) {
        visible += cell.querySelectorAll('.sticky:not(.filtered-out)').length;
      }
    });
    const countEl = hdr.querySelector('span');
    if (countEl) countEl.textContent = visible;
  });
}

function renderStories() {
  const container = document.getElementById('stories-container');
  const epicMap = {};
  const epicOrder = DATA.epics.map(e => e.id);

  DATA.stories.forEach(s => {
    const epic = s.epic || 'unknown';
    if (!epicMap[epic]) epicMap[epic] = [];
    epicMap[epic].push(s);
  });

  let html = '';
  epicOrder.forEach(epicId => {
    const stories = epicMap[epicId];
    if (!stories) return;
    const epicData = DATA.epics.find(e => e.id === epicId);
    const epicName = epicData ? epicData.name : epicId;
    html += `
      <div class="group-header" onclick="toggleGroup(this)">
        <h2>${esc(epicName)}</h2>
        <span class="count">${stories.length} stories</span>
        <span class="chevron">&#9660;</span>
      </div>
      <div class="cards">
        ${stories.map(storyCard).join('')}
      </div>`;
  });

  // Any ungrouped
  Object.keys(epicMap).forEach(epic => {
    if (!epicOrder.includes(epic)) {
      html += `
        <div class="group-header" onclick="toggleGroup(this)">
          <h2>${esc(epic)}</h2>
          <span class="count">${epicMap[epic].length} stories</span>
          <span class="chevron">&#9660;</span>
        </div>
        <div class="cards">
          ${epicMap[epic].map(storyCard).join('')}
        </div>`;
    }
  });

  container.innerHTML = html;
}

function renderRoadmap() {
  const container = document.getElementById('roadmap-container');
  const roadmap = DATA.roadmap;
  if (!roadmap || !roadmap.slices) {
    container.innerHTML = '<p style="color:var(--text-muted)">No roadmap data found.</p>';
    return;
  }

  let html = '';
  roadmap.slices.forEach((slice, idx) => {
    const sliceStories = slice.stories || [];
    const storyCount = sliceStories.length;
    const deps = slice.depends_on || [];

    html += `
      <div class="slice-header">
        <span class="slice-id">${esc(slice.id)}</span>
        <h2>${esc(slice.name)}</h2>
        <span class="count">${storyCount} stories</span>
        ${deps.length ? `<span style="color:var(--text-muted);font-size:0.8rem">depends on: ${deps.map(esc).join(', ')}</span>` : ''}
      </div>`;

    if (slice.description) {
      html += `<div class="statement-block" style="margin:8px 0">${esc(slice.description)}</div>`;
    }

    if (slice.acceptance_test) {
      html += `<div style="margin:8px 0"><h4 style="font-size:0.8rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Acceptance Test</h4><div class="statement-block" style="border-left-color:var(--ready)">${esc(slice.acceptance_test)}</div></div>`;
    }

    // Render stories with roadmap annotations
    html += '<div class="cards">';
    sliceStories.forEach(rs => {
      const sid = typeof rs === 'string' ? rs : rs.id;
      const story = DATA.stories.find(s => s.id === sid);
      if (story) {
        // Merge roadmap annotations into a card
        const a = getAnalysis(story.id);
        const readiness = (rs.readiness || a.readiness || '');
        const acCount = (story.acceptance_criteria || []).length;
        const rmNotes = rs.notes || '';
        const rmRefinement = rs.refinement || '';

        html += `
          <div class="card" data-card-id="${esc(story.id)}-rm" data-readiness="${esc(readiness)}" data-searchable="${esc((story.id + ' ' + story.title).toLowerCase())}">
            <div class="card-header" onclick="this.parentElement.classList.toggle('expanded')">
              <span class="card-id">${esc(story.id)}</span>
              <span class="card-title">${esc(story.title)}</span>
              <div class="card-badges">
                ${readinessBadge(readiness)}
                <span style="color:var(--text-muted);font-size:0.75rem;">${acCount} AC</span>
              </div>
              <span class="card-chevron">&#9654;</span>
            </div>
            <div class="card-body">
              ${rmNotes ? `<section><h4>Roadmap Notes</h4><div class="analysis-note">${esc(rmNotes)}</div></section>` : ''}
              ${rmRefinement ? `<section><h4>Refinement Plan</h4><div class="statement-block" style="border-left-color:var(--beefup)">${esc(rmRefinement)}</div></section>` : ''}
              ${story.as_a ? `<section><h4>User Story</h4><div class="user-story">As a ${esc(story.as_a)}, I want ${esc(story.i_want)}, so that ${esc(story.so_that)}</div></section>` : ''}
              <section><h4>Acceptance Criteria</h4>${renderACs(story.acceptance_criteria)}</section>
            </div>
          </div>`;
      } else {
        html += `<div class="card"><div class="card-header"><span class="card-id">${esc(sid)}</span><span class="card-title" style="color:var(--text-muted)">(story not found)</span></div></div>`;
      }
    });
    html += '</div>';
  });

  container.innerHTML = html;
}

function renderEpics() {
  const container = document.getElementById('epics-container');
  let html = '';

  DATA.epics.forEach(epic => {
    const storyCounts = epic.story_counts || {};
    const capList = (epic.capabilities || []).map(c => `<li>${esc(c)}</li>`).join('');
    const storyList = (epic.stories || []).map(s => {
      const sid = typeof s === 'string' ? s.split(':')[0] : s;
      return `<span class="dep-link" onclick="navigateTo('${esc(sid)}')">${esc(typeof s === 'string' ? s : s)}</span>`;
    }).join('');

    html += `
      <div class="card" data-card-id="${esc(epic.id)}">
        <div class="card-header" onclick="this.parentElement.classList.toggle('expanded')">
          <span class="card-id">${esc(epic.id)}</span>
          <span class="card-title">${esc(epic.name)}</span>
          <div class="card-badges">
            <span style="color:var(--text-muted);font-size:0.75rem;">${storyCounts.total || '?'} stories</span>
            <span style="color:var(--text-muted);font-size:0.75rem;">${storyCounts.must || 0}M ${storyCounts.should || 0}S ${storyCounts.could || 0}C</span>
          </div>
          <span class="card-chevron">&#9654;</span>
        </div>
        <div class="card-body">
          <section><h4>Description</h4><div class="statement-block">${esc(epic.description)}</div></section>
          ${capList ? `<section><h4>Capabilities</h4><ul class="epic-capabilities">${capList}</ul></section>` : ''}
          ${storyList ? `<section><h4>Stories</h4><div class="dep-list">${storyList}</div></section>` : ''}
          ${epic.themes ? `<section><h4>Themes</h4><div class="dep-list">${epic.themes.map(t => `<span class="dep-link" style="cursor:default">${esc(t)}</span>`).join('')}</div></section>` : ''}
        </div>
      </div>`;
  });

  container.innerHTML = html;
}

function renderPrinciples() {
  const container = document.getElementById('principles-container');
  let html = '';

  DATA.principles.forEach(p => {
    const implList = (p.implications || []).map(i => `<li>${esc(i)}</li>`).join('');
    const appliesTo = (p.applies_to || []).map(a =>
      `<span class="dep-link" onclick="navigateTo('${esc(a)}')">${esc(a)}</span>`
    ).join('');

    html += `
      <div class="card" data-card-id="${esc(p.id)}">
        <div class="card-header" onclick="this.parentElement.classList.toggle('expanded')">
          <span class="card-id">${esc(p.id)}</span>
          <span class="card-title">${esc(p.title)}</span>
          <span class="card-chevron">&#9654;</span>
        </div>
        <div class="card-body">
          <section><h4>Statement</h4><div class="statement-block">${esc(p.statement)}</div></section>
          <section><h4>Rationale</h4><div class="statement-block">${esc(p.rationale)}</div></section>
          ${implList ? `<section><h4>Implications</h4><ul class="impl-list">${implList}</ul></section>` : ''}
          ${appliesTo ? `<section><h4>Applies To</h4><div class="dep-list">${appliesTo}</div></section>` : ''}
          ${p.evidence ? `<section><h4>Evidence</h4>${renderSources(p.evidence)}</section>` : ''}
        </div>
      </div>`;
  });

  container.innerHTML = html;
}

function renderConflicts() {
  const container = document.getElementById('conflicts-container');
  let html = '';

  DATA.conflicts.forEach(c => {
    const resolved = c.resolution === 'resolved';
    const optionsHtml = (c.options || []).map(o => {
      const isSelected = resolved && c.decision_rationale && c.decision_rationale.toLowerCase().includes(`option ${o.id.toLowerCase()}`);
      return `
        <div class="option-card ${isSelected ? 'selected' : ''}">
          <h5>${esc(o.id)}: ${esc(o.name)}</h5>
          <div class="pros-cons">
            <div class="pros">+ ${(o.pros || []).map(esc).join(', ')}</div>
            <div class="cons">- ${(o.cons || []).map(esc).join(', ')}</div>
          </div>
        </div>`;
    }).join('');

    const affects = (c.affects || []).map(a =>
      `<span class="dep-link" onclick="navigateTo('${esc(a)}')">${esc(a)}</span>`
    ).join('');

    html += `
      <div class="card" data-card-id="${esc(c.id)}">
        <div class="card-header" onclick="this.parentElement.classList.toggle('expanded')">
          <span class="card-id">${esc(c.id)}</span>
          <span class="card-title">${esc(c.title)}</span>
          <div class="card-badges">
            ${resolved ? '<span class="badge badge-resolved">resolved</span>' : '<span class="badge badge-must">pending</span>'}
          </div>
          <span class="card-chevron">&#9654;</span>
        </div>
        <div class="card-body">
          <section><h4>Description</h4><div class="statement-block">${esc(c.description)}</div></section>
          ${c.evidence ? `<section><h4>Evidence</h4>${renderSources(c.evidence)}</section>` : ''}
          <section><h4>Options</h4>${optionsHtml}</section>
          ${c.decision_rationale ? `<section><h4>Resolution</h4><div class="resolution-block">${esc(c.decision_rationale)}</div></section>` : ''}
          ${affects ? `<section><h4>Affects</h4><div class="dep-list">${affects}</div></section>` : ''}
        </div>
      </div>`;
  });

  container.innerHTML = html;
}

function toggleGroup(header) {
  header.classList.toggle('collapsed');
  const cards = header.nextElementSibling;
  cards.classList.toggle('collapsed');
}

function switchTab(panel) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`[data-panel="${panel}"]`).classList.add('active');
  document.getElementById(`panel-${panel}`).classList.add('active');
}

// Tab switching
document.getElementById('tabs').addEventListener('click', e => {
  const tab = e.target.closest('.tab');
  if (!tab) return;
  switchTab(tab.dataset.panel);
});

// Story filtering
function filterStories() {
  const search = document.getElementById('story-search').value.toLowerCase();
  const activeReadiness = new Set();
  document.querySelectorAll('#readiness-filters .pill.active').forEach(p => activeReadiness.add(p.dataset.readiness));

  document.querySelectorAll('#stories-container .card').forEach(card => {
    const matchesSearch = !search || card.dataset.searchable.includes(search);
    const matchesReadiness = !card.dataset.readiness || activeReadiness.has(card.dataset.readiness);
    card.style.display = (matchesSearch && matchesReadiness) ? '' : 'none';
  });

  // Update group counts
  document.querySelectorAll('#stories-container .group-header').forEach(header => {
    const cards = header.nextElementSibling;
    const visible = cards.querySelectorAll('.card:not([style*="display: none"])').length;
    const total = cards.querySelectorAll('.card').length;
    header.querySelector('.count').textContent = `${visible}/${total} stories`;
  });
}

document.getElementById('story-search').addEventListener('input', filterStories);

document.querySelectorAll('#readiness-filters .pill').forEach(pill => {
  pill.addEventListener('click', () => {
    pill.classList.toggle('active');
    filterStories();
  });
});

// Roadmap filtering
document.getElementById('roadmap-search').addEventListener('input', e => {
  const search = e.target.value.toLowerCase();
  document.querySelectorAll('#roadmap-container .card').forEach(card => {
    const match = !search || card.dataset.searchable?.includes(search);
    card.style.display = match ? '' : 'none';
  });
});

loadData();
</script>
</body>
</html>
"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            data = {
                'stories': load_all_stories(),
                'epics': load_all_epics(),
                'principles': load_all_principles(),
                'conflicts': load_all_conflicts(),
                'analysis': load_analysis(),
                'roadmap': load_roadmap(),
            }
            self.wfile.write(json.dumps(data, default=str).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Silence request logs

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    with socketserver.TCPServer(("", port), Handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"xs Requirements Explorer running at {url}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")

if __name__ == '__main__':
    main()
