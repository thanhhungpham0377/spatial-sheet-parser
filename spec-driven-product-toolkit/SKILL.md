---
name: spec-driven-product-toolkit
description: Select and install a spec-driven product development profile with workflow, implementation, audit, and release quality gates.
---

# Spec-Driven Product Toolkit

Use this skill when the user wants to develop a product from explicit specifications through implementation, verification, and release. The toolkit supports `prototype`, `balanced`, and `production` profiles.

Ask a short decision interview before installing. Determine project size, whether data/auth/payment is involved, whether UI is user-facing, whether migrations/deployments are involved, and whether CI/PR gates are required. Recommend one profile, explain the trade-off, and wait for confirmation before changing the target repository.

Read [references/profiles.md](references/profiles.md) for the interview, stage behavior, and profile matrix. Read [references/catalog.md](references/catalog.md) when the user asks what a component does or where it came from.

Run `scripts/install_profile.py` from this skill directory. It writes only the selected toolkit under the target repository's `.spec-product/`, creates one non-overlapping manifest, and generates adapters only for tools in the selected profile.

```powershell
python scripts/install_profile.py --target D:\path\to\repo --profile balanced --check-only
python scripts/install_profile.py --target D:\path\to\repo --profile balanced
python scripts/install_profile.py --target D:\path\to\repo --profile production --install-tools
```

`--install-tools` is opt-in because it can invoke package managers and network access. Without it, the installer performs a preflight and emits exact missing-tool commands. Never install two overlapping workflow orchestrators; the manifest chooses Matt Pocock as the workflow layer and uses Spec Kit only in production for large, specification-heavy work.

After installation, use `.spec-product/README.md`, `.spec-product/manifest.json`, and `.spec-product/source-catalog.md` as the source of truth. Report missing tools or failed gates instead of claiming the project is verified.
