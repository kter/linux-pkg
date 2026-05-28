# 設計判断の記録

各決定の「なぜそうしたか」を残す。半年後に振り返ったとき、別の選択肢を検討する際の材料にする。

---

## ADR-001: S3 + CloudFront をホスティングに採用

**決定:** RPM リポジトリのホスティングに Amazon S3 + CloudFront を使う。

**検討した代替案:**
- EC2 インスタンスで nginx を立てる → インスタンスの維持・パッチ適用・可用性管理が必要。個人用途に対してコストと運用負荷が過大。
- GitHub Releases に RPM を置き、GitHub Pages を repodata ホストに使う → GitHub Pages は動的な repodata 生成が難しく、`createrepo_c` の出力をそのままホストするには向かない。
- Cloudflare R2 → AWS の他サービス（Route 53、ACM、IAM OIDC）との統合が煩雑になる。

**採用理由:**  
S3 は静的ファイルホスティングとして完結している。CloudFront を組み合わせることで HTTPS とカスタムドメインを低コストで実現できる。月額 $0.01 以下で運用できる。

---

## ADR-002: GitHub Actions の認証に OIDC を採用

**決定:** GitHub Actions から AWS への認証に OIDC（OpenID Connect）を使い、長期クレデンシャル（アクセスキー）は使わない。

**検討した代替案:**
- AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY を GitHub Secret に保存する → 鍵の漏洩リスク、定期的なローテーションが必要、最小権限の管理が煩雑。

**採用理由:**  
OIDC は一時トークンを使うため秘密情報を Secret に保存する必要がない。IAM ロールに `repo:kter/linux-pkg:*` の条件を設定することで、このリポジトリの CI からのみ assume できる。長期クレデンシャルを一切管理しなくてよい点が大きい。

---

## ADR-003: カスタムドメイン `repo.devtools.site` を採用

**決定:** リポジトリの公開 URL を `https://repo.devtools.site/rpm/noarch/` とする。

**検討した代替案:**
- S3 エンドポイントをそのまま使う（`repo.devtools.site.s3.ap-northeast-1.amazonaws.com`）→ S3 はバケット名が変わったりリージョンが変わると URL が変わる。`.repo` ファイルの配布後に URL を変えるとユーザー全員が再設定になる。
- CloudFront のデフォルトドメイン（`*.cloudfront.net`）を使う → 上記と同様の可搬性問題。見た目も悪い。

**採用理由:**  
カスタムドメインを使うことで、将来的に S3 バケットや CloudFront ディストリビューションを変えても `.repo` ファイルの URL は変わらない。`devtools.site` の DNS は Route 53 で管理済みなので追加コストはほぼゼロ。

---

## ADR-004: `rpm/noarch/` の単一フラット構造

**決定:** S3 上のパスを `rpm/noarch/` 単一ディレクトリにし、Fedora バージョンやアーキテクチャで分けない。

**検討した代替案:**
- `rpm/fedora/$releasever/$basearch/` 構造 → Fedora のバージョンアップごとに新ディレクトリが必要。CI が複雑になる。

**採用理由:**  
現在のパッケージ（`auto-brightness`）はすべて `noarch`（bash スクリプト + systemd ユニット）であり、アーキテクチャ依存がない。また、Fedora バージョン間の非互換も今のところない。将来 C のバイナリパッケージ（`rapl-read` など）を追加する必要が出た時点で構造を見直す。今は YAGNI。

---

## ADR-005: `Requires: /usr/bin/ffmpeg` でファイルパス指定

**決定:** spec の依存関係で `Requires: /usr/bin/ffmpeg` とパスで指定する（パッケージ名 `ffmpeg` ではなく）。

**経緯:**  
初回リリース（1.0）では `Requires: ffmpeg` と記述したが、Fedora 標準リポジトリには `ffmpeg` パッケージが存在しないため `dnf install` が失敗した。Fedora は `ffmpeg-free` というパッケージ名で同等のバイナリを提供している。また RPM Fusion を有効にしていれば `ffmpeg` パッケージが存在する。

**採用理由:**  
ファイルパス（`/usr/bin/ffmpeg`）で指定すると、どちらのパッケージがインストールされていても依存が満たされる。バージョン 1.1 で修正済み。

---

## ADR-006: `linux-config` と `linux-pkg` を別リポジトリに分離

**決定:** RPM パッケージング関連ファイルは `~/.config`（`linux-config` リポジトリ）に置かず、専用の `linux-pkg` リポジトリで管理する。

**検討した代替案:**
- `linux-config` 内に `packaging/` ディレクトリを追加する → CI（GitHub Actions）の OIDC 信頼対象がリポジトリ単位のため、設定ファイルと CI パイプラインが混在するのは関心の分離として良くない。`linux-config` は dotfiles 管理、`linux-pkg` はパッケージング、という役割が明確になる。

**採用理由:**  
将来 `linux-pkg` を別のマシン用に流用したり、他人に公開したりしやすい。`linux-config` は個人設定（秘匿情報を含む可能性がある）なので、パッケージング CI と分離する方が安全。

---

## ADR-007: GPG 鍵はパスフレーズなし

**決定:** GPG 鍵を `%no-protection`（パスフレーズなし）で生成し、CI での使用を簡略化する。

**検討した代替案:**
- パスフレーズ付きで生成し、GitHub Secret に保存する → `gpg --batch` での署名時に `--passphrase-fd` で渡せる。セキュリティは上がるが、管理が複雑になる。

**採用理由:**  
秘密鍵は GitHub Secret（暗号化ストレージ）で保護されており、リポジトリのコラボレーター（= 自分のみ）しかアクセスできない。パスフレーズを追加してもセキュリティの実質的な向上が限定的であるのに対し、CI の複雑さが増す。パスフレーズなしの方が `rpmsign` の呼び出しがシンプルになる。

将来、鍵を他者と共有する可能性が出た場合はパスフレーズ付きに切り替える。
