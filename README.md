# GitHub Copilot Agent Orchestration Template

GitHub Copilot のカスタムエージェント機能を使ったオーケストレーション開発テンプレートです。
オーケストレーターが複数のサブエージェントを自律的に呼び出し、実装・テスト・レビュー・コミットの一連のフローを自動化します。

## フォルダ構成

```
.
├── src/                    # ビルドのソース（編集対象）
│   ├── config.yaml         # ボイラープレート設定（免責文・ファイル経由通信）
│   ├── schema.json         # エージェント定義の JSON Schema
│   ├── template.md         # Jinja2 テンプレート（.agent.md の雛形）
│   └── definitions/        # 生成対象エージェントの YAML 定義
│       ├── impl.yaml
│       ├── requirements.yaml
│       └── ...             # 計 16 ファイル
│
├── sub-agents/             # 特殊サブエージェント（手動管理・ビルドでコピー）
│   ├── session-manager.agent.md
│   ├── judge.agent.md
│   └── external-reviewer.agent.md
│
├── orchestrator/           # オーケストレーター（手動管理・ビルドでコピー）
│   └── orchestrator.agent.md
│
├── agents/                 # ビルド出力（自動生成・手動編集不可）
│   └── *.agent.md × 20
│
├── .githooks/
│   └── pre-commit          # ソース変更時に自動ビルド
└── build-agents.py         # ビルドスクリプト
```

## エージェント一覧

### 生成エージェント（`src/definitions/` で管理）

| エージェント | 役割 |
|---|---|
| `requirements` | 要件定義 |
| `architect` | アーキテクチャ設計 |
| `impl-plan` | 実装計画策定 |
| `impl` | コード実装 |
| `test` | テスト作成・実行 |
| `review` | コードレビュー |
| `debug` | デバッグ調査 |
| `refactor` | リファクタリング |
| `commit` | コミット実行 |
| `docs` | ドキュメント作成 |
| `docs-review` | ドキュメントレビュー |
| `scan` | コードベーススキャン |
| `security-review` | セキュリティレビュー |
| `research` | 技術調査 |
| `impact-analysis` | 影響分析 |
| `test-review` | テストレビュー |

### 手動管理エージェント（`sub-agents/`）

| エージェント | 役割 |
|---|---|
| `session-manager` | セッションディレクトリの作成・初期化 |
| `judge` | 状況分析と次アクション判断 |
| `external-reviewer` | フロー全体の第三者レビュー |

### オーケストレーター（`orchestrator/`）

| エージェント | 役割 |
|---|---|
| `orchestrator` | サブエージェントを統括・委譲 |

## エージェントの編集方法

### 生成エージェント（`src/definitions/*.yaml`）

```yaml
name: impl
description: "..."
tools: [edit, execute, read, search, todo]
argument-hint: "..."

role: |
  あなたは...

steps: |
  1. ...
  2. ...

sections:
  - title: "制約"
    content: |
      - ...

summary-hint: |
  例: `実装完了: ...`
```

編集後にビルドを実行してください。

### 手動管理エージェント・オーケストレーター

`sub-agents/` または `orchestrator/` 内の `.agent.md` を直接編集してください。
ビルド時にそのまま `agents/` へコピーされます。

### ボイラープレートの変更

`src/config.yaml` で全サブエージェント共通のテキストを管理しています。

| キー | 内容 |
|---|---|
| `disclaimer` | 冒頭の免責文（全エージェント共通） |
| `file_communication` | 「ファイル経由通信」セクション全体 |

### テンプレートの変更

`src/template.md` が `.agent.md` の雛形です。
Jinja2 テンプレート構文を使用しています。

## ビルド

```bash
# 全エージェントを再生成（agents/ をクリアして出力）
python3 build-agents.py

# 特定のファイルのみ再生成（agents/ はクリアしない）
python3 build-agents.py src/definitions/impl.yaml

# 内容確認（ファイル書き込みなし）
python3 build-agents.py --dry-run
```

**依存ライブラリ** (初回のみ):
```bash
pip install pyyaml jinja2
```

## Git フックのセットアップ

クローン後に以下を実行してください。

```bash
git config core.hooksPath .githooks
```

設定後は、`src/`・`sub-agents/`・`orchestrator/` 配下のファイルをコミットする際に自動でビルドが走り、生成された `agents/` がコミットに含まれます。

## 使用方法（実プロジェクトへの適用）

このリポジトリの内容を `.github/` フォルダとして配置することを想定しています。

```
your-project/
  .github/
    agents/          ← ここに agents/ の内容を配置
    ...
```

VS Code は `.github/agents/` 配下を自動的にカスタムエージェントとして認識します。
