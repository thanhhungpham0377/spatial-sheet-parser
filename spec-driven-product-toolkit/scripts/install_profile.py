"""Install a non-overlapping Spec-Driven Product Toolkit profile."""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path

CATALOG = {
    "matt-pocock": ("workflow", "https://github.com/mattpocock/skills", None),
    "spec-kit": ("durable-spec", "https://github.com/github/spec-kit", "specify"),
    "pre-commit": ("pre-commit", "https://github.com/pre-commit/pre-commit", "pre-commit"),
    "playwright": ("browser-e2e", "https://github.com/microsoft/playwright", "npx"),
    "axe-core": ("accessibility", "https://github.com/dequelabs/axe-core", "npx"),
    "lighthouse": ("performance", "https://github.com/GoogleChrome/lighthouse", "npx"),
    "semgrep": ("sast", "https://github.com/semgrep/semgrep", "semgrep"),
    "gitleaks": ("secrets", "https://github.com/gitleaks/gitleaks", "gitleaks"),
    "osv-scanner": ("dependencies", "https://github.com/google/osv-scanner", "osv-scanner"),
    "trivy": ("containers-iac", "https://github.com/aquasecurity/trivy", "trivy"),
    "codeql": ("deep-security", "https://github.com/github/codeql", "codeql"),
    "zizmor": ("actions-security", "https://github.com/woodruffw/zizmor", "zizmor"),
    "sqlfluff": ("sql-quality", "https://github.com/sqlfluff/sqlfluff", "sqlfluff"),
    "atlas": ("migration-authority", "https://github.com/ariga/atlas", "atlas"),
    "reviewdog": ("pr-feedback", "https://github.com/reviewdog/reviewdog", "reviewdog"),
}
PROFILES = {
    "prototype": ["matt-pocock", "playwright"],
    "balanced": ["matt-pocock", "pre-commit", "playwright", "axe-core", "lighthouse", "semgrep", "gitleaks", "osv-scanner", "sqlfluff", "reviewdog"],
    "production": ["matt-pocock", "spec-kit", "pre-commit", "playwright", "axe-core", "lighthouse", "semgrep", "gitleaks", "osv-scanner", "trivy", "codeql", "zizmor", "sqlfluff", "atlas", "reviewdog"],
}
PROFILE_INFO = {
    "prototype": {"size": "personal prototype or small MVP", "risk": "no sensitive data; no merge blocking", "method": "fast feedback with low ceremony", "stages": "grill -> plan -> implement -> smoke test -> review"},
    "balanced": {"size": "real application for a small or medium team", "risk": "UI/API/dependencies/database with moderate risk", "method": "Matt Pocock workflow plus executable quality gates", "stages": "discover -> design -> plan -> implement -> test -> security/UI audit -> PR review"},
    "production": {"size": "deployed product with multiple contributors", "risk": "auth, payment, PII, migrations, CI/CD or compliance", "method": "balanced plus durable specs and protected security gates", "stages": "spec -> design -> plan -> implement -> full audit -> protected PR -> release/retro"},
}

def present(command: str | None) -> bool:
    return command is None or shutil.which(command) is not None

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", required=True, type=Path)
    ap.add_argument("--profile", choices=sorted(PROFILES), help="Omit to run the decision interview")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--install-tools", action="store_true", help="Reserved for explicit package-manager installation after profile selection")
    ap.add_argument("--list-profiles", action="store_true")
    args = ap.parse_args()
    if args.list_profiles:
        for name, info in PROFILE_INFO.items():
            print(f"\n{name}: {info['size']}\n  Risk: {info['risk']}\n  Method: {info['method']}\n  Stages: {info['stages']}")
        return 0
    if not args.profile:
        print("Chọn profile phù hợp:\n")
        for i, (name, info) in enumerate(PROFILE_INFO.items(), 1):
            print(f"{i}. {name} — {info['size']} — {info['risk']}")
        choice = input("Nhập 1, 2 hoặc 3: ").strip()
        if choice not in {"1", "2", "3"}:
            ap.error("profile selection must be 1, 2, or 3")
        args.profile = list(PROFILES)[int(choice) - 1]
    target = args.target.resolve()
    if not target.is_dir():
        ap.error(f"target is not a directory: {target}")
    selected = PROFILES[args.profile]
    missing = [name for name in selected if not present(CATALOG[name][2])]
    kit = target / ".spec-product"
    manifest = {
        "profile": args.profile,
        "components": [{"name": n, "role": CATALOG[n][0], "upstream": CATALOG[n][1], "command": CATALOG[n][2]} for n in selected],
        "non_overlap": True,
        "missing_commands": [f"Install or enable: {n} ({CATALOG[n][1]})" for n in missing],
    }
    print(json.dumps({"target": str(target), "profile": args.profile, "missing": missing}, indent=2))
    if args.check_only:
        return 2 if missing else 0
    kit.mkdir(exist_ok=True)
    (kit / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (kit / "source-catalog.md").write_text("# Installed source catalog\n\n" + "\n".join(f"- **{n}** — {CATALOG[n][0]} — {CATALOG[n][1]}" for n in selected) + "\n", encoding="utf-8")
    info = PROFILE_INFO[args.profile]
    readme = f"""# Spec-Driven Product Toolkit\n\nProfile: `{args.profile}`\n\n- Phù hợp: {info['size']}\n- Rủi ro: {info['risk']}\n- Phương pháp: {info['method']}\n- Giai đoạn: {info['stages']}\n\nSelected components are recorded in `manifest.json`. Missing tools are not silently ignored: see `missing_commands` and install them before treating a gate as passing.\n\nGenerated by `spec-driven-product-toolkit`.\n"""
    (kit / "README.md").write_text(readme, encoding="utf-8")
    if missing:
        print("Profile files created, but verification is incomplete. Missing:")
        for name in missing:
            print(f"- {name}: {CATALOG[name][1]}")
        return 2
    print(f"Installed {args.profile} profile at {kit}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
