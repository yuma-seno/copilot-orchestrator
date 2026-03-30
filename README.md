# copilot-orchestrator

VSCode GitHub Copilot 向けのエージェントオーケストレーションシステム

## 概要

サブエージェントを利用したオーケストレーションシステム。オーケストレーターがユーザの指示を分析・計画し、サブエージェントに全ての実作業を移譲する。セッションディレクトリへのファイル経由通信でコンテキストの記録と引き継ぎを行う。

## アーキテクチャ

```
ユーザ
  ↕ (askQuestion)
Orchestrator [tools: askQuestion, todo | agents: sub-agent]
  ↕ (@sub-agent + セッションディレクトリ)
Sub Agent [tools: execute, read, edit, search, web, browser, todo]
  ↕ (skills 参照)
ファイルシステム / .copilot/sessions/[session-id]/
```

### 設計思想

- **オーケストレーターは「何をすべきか」を決め、「どうやるか」はサブエージェントに委ねる** — オーケストレーター自身はファイル操作・技術判断を一切行わない
- **ファイル経由のコンテキスト管理** — サブエージェントの詳細な出力はセッションディレクトリにファイルとして記録され、オーケストレーターには最小限のサマリのみが返される
- **スキルによる精度の底上げ** — LLM が見落としがちなチェック項目（セキュリティ、既存パターン準拠、検証の実行等）を構造化されたチェックリストとして提供する

### エージェント

| エージェント | 役割 | ツール |
|-------------|------|--------|
| **Orchestrator** | セッション管理、ワークフロー選定、タスク移譲、品質判定 | askQuestion, todo, agent |
| **Sub Agent** | 全実作業の実行（実装・テスト・レビュー・調査等） | execute, read, edit, search, web, browser, todo |

### オーケストレーションフロー

```
1. セッション開始（ディレクトリ作成、ルール確認）
2. タスク分析・計画（ワークフロー選定、タスクリスト作成）
3. タスク移譲・実行（@sub-agent に移譲 → サマリ受け取り）
4. 品質判定（通過 / 修正指示 / 差し戻し）
5. セッション完了（サマリ記録）
```

## ディレクトリ構成

```
example.github/
├── agents/
│   ├── orchestrator.agent.md        # オーケストレーター
│   └── sub-agent.agent.md           # サブエージェント
└── skills/
    ├── code-review/SKILL.md         # 構造化コードレビュー
    ├── context-analysis/SKILL.md    # タスク完了後の改善分析
    ├── debugging/SKILL.md           # 体系的デバッグ
    ├── design/SKILL.md              # アーキテクチャ・コンポーネント設計
    ├── implementation/SKILL.md      # コーディング品質・セキュリティ
    ├── refactoring/SKILL.md         # 安全なリファクタリング
    ├── requirements-analysis/SKILL.md # 要件定義・受け入れ基準
    ├── test-strategy/SKILL.md       # テスト戦略・TDD
    └── verification/SKILL.md        # 完了前の検証強制
```

### スキル一覧

| スキル | description（LLMに常時渡される） | 主な効果 |
|--------|------------------------------|---------|
| **debugging** | バグ・テスト失敗・予期しない動作の調査と修正。修正の前に根本原因の体系的調査を強制する | HARD-GATE: 調査なしの修正禁止 |
| **code-review** | コード品質の評価・変更レビュー。品質・セキュリティ・パフォーマンス・保守性の観点で構造化レビューを実施する | 5観点、CRITICAL/WARNING/INFO分類 |
| **refactoring** | 外部の振る舞いを変えずにコードの内部構造を改善する。機能変更との混在禁止・テスト必須を強制する | HARD-GATE: スコープ制御 |
| **test-strategy** | テストの作成・計画・カバレッジ改善。テストファースト開発と構造化されたテスト設計パターンを適用する | TDD強制、Good/Bad比較 |
| **implementation** | コードの新規実装・修正。既存規約の準拠・セキュリティ・品質のチェックリストを適用する | セキュリティチェック、規約準拠 |
| **requirements-analysis** | ユーザ指示からの要件定義。計測可能な受け入れ基準の定義とエッジケースの網羅を強制する | Good/Bad受け入れ基準、エッジケース網羅 |
| **design** | アーキテクチャ・コンポーネントの設計判断。既存パターン尊重・最小構造・テスタビリティを強制する | HARD-GATE: 既存パターン調査必須 |
| **verification** | タスク完了報告の前に実施する検証。検証コマンドの実行と結果確認なしに完了を主張することを禁止する | HARD-GATE: 証拠なしの完了報告禁止 |
| **context-analysis** | タスク完了後に実施する振り返り分析。作業内容からコードベースとプロセスの具体的な改善提案を導出する | サブエージェントの作業フロー最終ステップ |

## セッションディレクトリ

オーケストレーション実行時に自動作成される：

```
.copilot/sessions/[sessionId]/
├── session.json     # セッション情報（id, status, rules, tasks）
├── summary.md       # セッション完了時の最終サマリ
├── logs/            # タスク実行ログ（判断記録・改善提案を含む）
│   ├── [timestamp]-[task-name].md
│   └── ...
└── artifacts/       # 成果物（設計書、レビューレポート等）
```

### session.json

```json
{
  "id": "yyyymmddhhmmssfff",
  "createdAt": "ISO8601",
  "status": "active | completed",
  "rules": {
    "questionGranularity": "high | medium | low",
    "reviewPolicy": "auto | manual | skip"
  },
  "tasks": [
    {"id": "task-001", "name": "...", "status": "pending | in-progress | done | failed"}
  ]
}
```

## 使い方

### 1. セットアップ

`example.github/` の内容をプロジェクトの `.github/` にコピーする：

```bash
cp -r example.github/agents/ .github/agents/
cp -r example.github/skills/ .github/skills/
```

### 2. オーケストレーターの起動

```
@orchestrator [開発タスクの指示]
```

オーケストレーターが質問粒度とレビュー方針を確認した後、ワークフローを選定してサブエージェントに作業を移譲します。

## ライセンス

MIT
