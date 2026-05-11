---
name: tf-diagram
description: >
  Generates professional enterprise-grade architecture diagrams from Terraform projects
  (.tf / .hcl files). Parses the entire project recursively, detects every resource,
  module, variable, output, data source and provider. Produces:
    1. An editable .drawio file (open at app.diagrams.net or VS Code draw.io extension)
    2. A PNG preview image with real cloud icons (AWS, GCP, Azure, Kubernetes, Databricks)

  Uses company/enterprise style: horizontal left-to-right layout, white zones with thin
  borders, official cloud icons without wrappers, orthogonal connection lines with labels,
  swimlanes by cloud provider and tier, compliance badges for resources missing tags.

  ALWAYS trigger this skill when the user says any of:
  "grafica mi terraform", "diagrama de arquitectura", "visualiza infraestructura",
  "genera draw.io", "architecture diagram", "tf diagram", "map my terraform",
  "diagramar", "documento arquitectura", "exportar terraform", or mentions .tf + diagram.

  Supports: AWS (100+ services), GCP, Azure, Kubernetes, Helm, Databricks, multi-cloud,
  Terragrunt multi-account (detects account/region from directory structure).
  Multi-page drawio: one page per region/account + Legend page.
---

# Terraform → Architecture Diagram Skill

## Quick start

```bash
# 1. Install dependency (once)
pip install python-hcl2 --break-system-packages

# 2. Download icons (once, ~34MB)
python3 scripts/download_icons.py

# 3. Generate diagram
python3 scripts/tf_to_diagram.py <terraform_dir> --output my_arch.drawio

# 4. Optional: also export PNG
python3 scripts/tf_to_diagram.py <terraform_dir> --output my_arch.drawio --png my_arch.png
```

## Full workflow

### Step 1 — Confirm inputs
Ask the user for the Terraform project path if not already known.
If they paste .tf code, save it to `/tmp/tf_project/` first.

### Step 2 — Run the parser
```bash
python3 scripts/tf_to_diagram.py <dir> --output arch.drawio --png arch.png --verbose
```

The `--verbose` flag prints a full resource table with providers, tiers, regions, and
tag compliance. Always use it so you can report back to the user.

### Step 3 — Copy output and present
```bash
cp arch.drawio /mnt/user-data/outputs/arch.drawio
cp arch.png    /mnt/user-data/outputs/arch.png
```
Then call `present_files` with both files.

### Step 4 — Report to user
Always tell the user:
- Resource count per provider
- Pages generated (one per account/region + Legend)
- Missing-tags count (compliance)
- How to open: `app.diagrams.net` (drag & drop) or VS Code `Draw.io Integration` extension

---

## What the scripts do

### `scripts/download_icons.py`
Downloads the `diagrams` Python package wheel from PyPI and extracts
~1,500 official PNG icons for AWS, GCP, Azure, and Kubernetes to `scripts/icons/`.
Safe to run multiple times (skips if already downloaded).

### `scripts/tf_to_diagram.py`
Main entrypoint. Orchestrates:
1. `lib/parser.py`   — Parse HCL/YAML, extract resources/modules/deps
2. `lib/drawio.py`   — Build multi-page draw.io XML
3. `lib/renderer.py` — Render PNG preview with real icons (company style)

### `scripts/lib/parser.py`
- Recursively finds all `.tf` and `.hcl` files (skips `.terraform/`)
- Parses with `python-hcl2`, falls back to regex for malformed HCL
- Extracts: resources, modules, data sources, variables, outputs, providers
- Detects provider per resource type prefix (`aws_*`, `google_*`, `azurerm_*`, etc.)
- Extracts network annotations (CIDR, AZ, ports) from resource config
- Infers region/account from Terragrunt directory structure
- Finds implicit dependencies via `${resource.name}` interpolation
- Finds explicit `depends_on` references

### `scripts/lib/drawio.py`
- Generates multi-page draw.io XML (one page per account/region scope + Legend)
- Layout: swimlanes by tier (Networking / Compute / Data / Security / CI-CD)
- Within each tier: color-coded cloud zones (AWS orange, GCP blue, Azure teal, K8s indigo)
- Each resource node: official draw.io shape + hover tooltip with full config
- Red border (3px) on resources missing `tags` or `labels` (compliance)
- Dashed border for Terraform `data` sources
- Dependency arrows: solid=ref, red-dashed=depends_on
- Variables as sticky notes, outputs as exit nodes, Legend page

### `scripts/lib/renderer.py`
- Renders company-style PNG using matplotlib
- White background zones, thin borders, official icons without wrappers
- Horizontal layout: Internet → VPC (Public → Private → EKS → DBs → Async) → GCP/Databricks
- Orthogonal (90°) connection routing
- Color-coded arrows by type (no text on arrows — coloring tells the story)
- Compliance badges (!), missing-tags badges, data-source dashed borders

---

## Edge cases

| Situation | Action |
|-----------|--------|
| No .tf files found | Check path; try `find <dir> -name "*.tf"` |
| Icons not downloaded | Run `python3 scripts/download_icons.py` first |
| Region shows `unknown-region` | Add `region` to provider block or use Terragrunt path convention |
| Pasted code | Save to `/tmp/tf_project/main.tf`, run from there |
| 100+ resources dense layout | Tell user: draw.io → Edit > Select All → Arrange > Auto Layout (Organic) |
| Malformed HCL | Regex fallback runs automatically; partial parse continues |
| Terragrunt multi-account | Path `<account>/<region>/<module>/main.tf` auto-detected for page split |

---

## draw.io tips for the user

1. **Enable shape libraries** if icons appear blank:
   Extras → Edit Diagram → OK → View → Shapes → enable AWS, GCP, Azure, Kubernetes
2. **Navigate pages** via tabs at the bottom
3. **Hover** over any resource to see full Terraform config (tooltip)
4. **Red border** = missing tags → fix in Terraform and regenerate
5. **Auto-layout**: Edit → Select All → Arrange panel → Layout → Organic
6. **Export**: File → Export As → PNG / PDF / SVG

---

## References
- `references/icon_map.md`   — Full icon path map for all supported resource types
- `references/providers.md`  — Provider prefix → cloud mapping, tier classification
