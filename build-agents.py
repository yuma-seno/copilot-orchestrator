#!/usr/bin/env python3
"""
Build .agent.md files from YAML source files in src/definitions/.

Usage:
    python3 build-agents.py [--dry-run] [file.yaml ...]

Without file arguments, performs a full rebuild:
  1. Clear agents/
  2. Generate from src/definitions/*.yaml
  3. Copy sub-agents/*.agent.md          (session-manager, judge, external-reviewer)
  4. Copy orchestrator/*.agent.md

With file arguments, generates only the specified YAML files (no clear, no copy).
--dry-run prints generated content without writing any files.

Configuration files (edit these, not this script):
  src/config.yaml      -- boilerplate text (disclaimer, file_communication)
  src/template.md      -- Jinja2 template for .agent.md output

YAML source schema (src/definitions/*.yaml):
  name:           str        Output filename: agents/{name}.agent.md
  description:    str        YAML frontmatter description
  tools:          [str]      YAML frontmatter tools list
  argument-hint:  str        YAML frontmatter argument-hint
  role:           str        "あなたの役割" section body
  steps:          str        "手順 (#tool:todo)" section body
  sections:       (optional) Additional sections
    - title:   str
      content: str
  summary-hint:   str        "1行サマリの内容" section body

Manually managed agents (do NOT add to src/definitions/):
  orchestrator/          orchestrator.agent.md
  sub-agents/            session-manager.agent.md, judge.agent.md, external-reviewer.agent.md
"""

import sys
import shutil
import yaml

try:
    import jinja2
except ImportError:
    print("jinja2 が必要です: pip install jinja2", file=sys.stderr)
    sys.exit(1)

from pathlib import Path


# ─── Key normalizer ──────────────────────────────────────────────────────────


def normalize_keys(d: dict) -> dict:
    """ハイフン区切りのキーをアンダースコアに変換する（Jinja2 変数名対応）"""
    return {k.replace("-", "_"): v for k, v in d.items()}


# ─── Build ───────────────────────────────────────────────────────────────────


def load_config(script_dir: Path) -> dict:
    config_path = script_dir / "src" / "config.yaml"
    if not config_path.exists():
        print(f"設定ファイルが見つかりません: {config_path}", file=sys.stderr)
        sys.exit(1)
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def load_template(script_dir: Path) -> "jinja2.Template":
    template_path = script_dir / "src" / "template.md"
    if not template_path.exists():
        print(f"テンプレートファイルが見つかりません: {template_path}", file=sys.stderr)
        sys.exit(1)
    env = jinja2.Environment(
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=jinja2.StrictUndefined,
    )
    return env.from_string(template_path.read_text(encoding="utf-8"))


def generate(src: Path, agents_dir: Path, template: "jinja2.Template", config: dict, *, dry_run: bool) -> None:
    raw = yaml.safe_load(src.read_text(encoding="utf-8"))
    data = normalize_keys(raw)
    content = template.render(**data, **config)
    dest = agents_dir / f"{data['name']}.agent.md"
    if dry_run:
        print(f"=== {dest.name} ===")
        print(content)
        print()
    else:
        dest.write_text(content, encoding="utf-8")
        print(f"  Generated: {dest.name}")


def copy_agents(src_dir: Path, agents_dir: Path) -> int:
    count = 0
    if src_dir.exists():
        for src in sorted(src_dir.glob("*.agent.md")):
            shutil.copy2(src, agents_dir / src.name)
            print(f"  Copied:    {src.name}")
            count += 1
    return count


def main() -> None:
    script_dir = Path(__file__).parent
    sources_dir = script_dir / "src" / "definitions"
    agents_dir = script_dir / "agents"
    manual_dir = script_dir / "sub-agents"
    orchestrator_dir = script_dir / "orchestrator"

    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    positional = [a for a in args if a != "--dry-run"]

    config = load_config(script_dir)
    template = load_template(script_dir)

    full_rebuild = not positional

    if positional:
        sources = [Path(p) for p in positional]
    else:
        sources = sorted(sources_dir.glob("*.yaml"))

    if not sources and full_rebuild:
        print("src/definitions/ に *.yaml が見つかりません。", file=sys.stderr)
        sys.exit(1)

    # Full rebuild: clear agents/ first
    if full_rebuild and not dry_run:
        if agents_dir.exists():
            shutil.rmtree(agents_dir)
        agents_dir.mkdir()

    if not dry_run:
        agents_dir.mkdir(exist_ok=True)

    # Generate from YAML sources
    for src in sources:
        generate(src, agents_dir, template, config, dry_run=dry_run)

    if full_rebuild and not dry_run:
        # Copy manually managed agents
        count_manual = copy_agents(manual_dir, agents_dir)
        count_orch = copy_agents(orchestrator_dir, agents_dir)

        total = len(sources) + count_manual + count_orch
        print(f"\n✓ agents/ に {total} 個のファイルを出力しました。")
        print(f"  生成: {len(sources)} 個  コピー(sub-agents): {count_manual} 個  コピー(orchestrator): {count_orch} 個")
    elif not dry_run:
        print(f"\n✓ {len(sources)} 個のファイルを生成しました（部分ビルド）。")


if __name__ == "__main__":
    main()
