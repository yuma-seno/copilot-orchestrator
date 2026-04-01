# プロジェクト概要

本リポジトリは **VS Code GitHub Copilot Chat のカスタムエージェント機能** を活用したオーケストレーション開発テンプレートです。  
オーケストレーター (`orchestrator`) が複数のサブエージェントを自律的に呼び出し、要件定義・設計・実装・テスト・レビュー・コミットの一連のフローを自動化します。

---

## ディレクトリ構成と歩き方

```
.
├── src/                        # ← エージェント定義の編集はここ
│   ├── config.yaml             # 全サブエージェント共通のボイラープレートテキスト
│   ├── schema.json             # definitions/*.yaml の JSON Schema
│   ├── template.md             # Jinja2 テンプレート（.agent.md の雛形）
│   └── definitions/            # 生成対象エージェント 16 本の YAML 定義
│       ├── impl.yaml
│       ├── requirements.yaml
│       └── ...
│
├── sub-agents/                 # 手動管理の特殊サブエージェント（ビルドでコピーのみ）
│   ├── session-manager.agent.md
│   ├── judge.agent.md
│   └── external-reviewer.agent.md
│
├── orchestrator/               # 手動管理のオーケストレーター（ビルドでコピーのみ）
│   └── orchestrator.agent.md
│
├── agents/                     # ← ビルド出力（手動編集禁止・自動生成）
│   └── *.agent.md × 20
│
├── build-agents.py             # ビルドスクリプト（YAML → .agent.md）
├── .githooks/
│   └── pre-commit              # ソース変更時に自動ビルド＆ステージング
└── README.md
```

### 重要なルール
- `agents/` は **手動編集禁止**。必ずソースを編集してビルドすること。
- `agents/` を直接コミットしようとすると `.githooks/pre-commit` がブロックする。

---

## エージェントの種類と役割

### オーケストレーター（`orchestrator/orchestrator.agent.md`）

- VS Code のエージェントとしてユーザが直接起動する唯一のエントリーポイント
- 自らはコード・ファイル操作を一切行わず、**サブエージェントへの委譲と次アクションの判断**に専念する
- 複雑な判断は `judge` に委譲し、自身のコンテキストを汚さない設計

### 特殊サブエージェント（`sub-agents/`）

| エージェント | 役割 |
|---|---|
| `session-manager` | ワークフロー開始時にタイムスタンプ付き `SESSION_DIR` を作成し、`session-info.md` を初期化する |
| `judge` | オーケストレーターに代わりファイルを読んで状況分析・次アクション判断を行う |
| `external-reviewer` | フロー全体の第三者レビューを実施する |

### 生成エージェント（`src/definitions/*.yaml` で定義）

| ファイル名 | エージェント名 | 役割 |
|---|---|---|
| `requirements.yaml` | `requirements` | 要件定義 |
| `architect.yaml` | `architect` | アーキテクチャ設計 |
| `impl-plan.yaml` | `impl-plan` | 実装計画策定 |
| `impl.yaml` | `impl` | コード実装 |
| `test.yaml` | `test` | テスト作成・実行 |
| `review.yaml` | `review` | コードレビュー |
| `test-review.yaml` | `test-review` | テストレビュー |
| `debug.yaml` | `debug` | デバッグ調査 |
| `refactor.yaml` | `refactor` | リファクタリング |
| `commit.yaml` | `commit` | コミット実行 |
| `docs.yaml` | `docs` | ドキュメント作成 |
| `docs-review.yaml` | `docs-review` | ドキュメントレビュー |
| `scan.yaml` | `scan` | コードベーススキャン |
| `security-review.yaml` | `security-review` | セキュリティレビュー |
| `research.yaml` | `research` | 技術調査 |
| `impact-analysis.yaml` | `impact-analysis` | 影響分析 |

---

## ビルドシステム

### ビルドスクリプト（`build-agents.py`）

`src/definitions/*.yaml` を `src/template.md`（Jinja2）に流し込み、`src/config.yaml` のボイラープレートを埋め込んで `agents/` に `.agent.md` を生成する。

```bash
# 全エージェントを再生成（agents/ をクリア → 生成 → sub-agents/ と orchestrator/ をコピー）
python3 build-agents.py

# 特定ファイルのみ再生成（agents/ はクリアしない、コピーも行わない）
python3 build-agents.py src/definitions/impl.yaml

# 内容確認のみ（ファイル書き込みなし）
python3 build-agents.py --dry-run
```

依存ライブラリ（初回のみ）:
```bash
pip install pyyaml jinja2
```

### pre-commit フック（`.githooks/pre-commit`）

`src/`・`sub-agents/`・`orchestrator/` 配下の変更がステージされていると自動的にビルドを実行し、生成された `agents/` をコミットに自動追加する。初回セットアップ:

```bash
git config core.hooksPath .githooks
```

---

## エージェント定義ファイルの構造

### YAML 定義（`src/definitions/*.yaml`）

```yaml
name: <string>            # 出力: agents/{name}.agent.md
description: <string>     # フロントマター description
tools: [<string>, ...]    # フロントマター tools
argument-hint: <string>   # フロントマター argument-hint（オーケストレーターがサブ呼び出し時に参照）

role: |                   # 「あなたの役割」セクション
  ...

steps: |                  # 「手順 (#tool:todo)」セクション
  1. ...

sections:                 # 追加セクション（省略可）
  - title: "..."
    content: |
      ...

summary-hint: |           # 「1行サマリの内容」セクション（何を返すか）
  ...
```

スキーマは `src/schema.json` で定義済み。必須フィールドは `name`, `description`, `tools`, `argument-hint`, `role`, `steps`, `summary-hint`。

### ボイラープレート（`src/config.yaml`）

全サブエージェントに共通で挿入されるテキストを管理：
- `disclaimer`: 冒頭の免責文（オーケストレーション自動化システムの一員である旨）
- `file_communication`: 「ファイル経由通信」セクション全体（`SESSION_DIR` の読み書き規約）

### テンプレート（`src/template.md`）

Jinja2 テンプレート。出力される `.agent.md` のレイアウトを定義する。セクション順序の変更やフロントマターの追加はここで行う。

---

## セッション管理とファイル経由通信

オーケストレーターとサブエージェントは **ファイル経由** で情報を共有する。

### セッションディレクトリ

- パス: `.copilot/orchestrator/<yyMMddHHmmssfff>/`（例: `.copilot/orchestrator/260401123456789/`）
- ワークフロー開始時に `session-manager` が作成する
- `.gitignore` により Git からは除外される

### ファイル命名規則

| ファイル | 用途 |
|---|---|
| `SESSION_DIR/session-info.md` | ユーザ指示・ワークスペースパス・セッション全体のルール |
| `SESSION_DIR/<NN>-<agent>-output.md` | 各エージェントの出力（NN は 01, 02, … の連番） |

### 通信の原則

- オーケストレーターはファイルの中身を**一切読まない**
- サブエージェントから受け取るのは **1行サマリのみ**
- 内容の読み取りや思考を要する判断は `judge` に委譲する

---

## 実プロジェクトへの適用方法

本リポジトリの `agents/` 配下を対象プロジェクトの `.github/agents/` に配置する。VS Code は `.github/agents/` を自動的にカスタムエージェントとして認識する。

```
your-project/
  .github/
    agents/      ← agents/*.agent.md をここに配置
```