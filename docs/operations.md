# 運用手順

## タグ命名規則

| パッケージ | タグ形式 | 例 |
|---|---|---|
| `auto-brightness` | `auto-brightness-<version>` | `auto-brightness-1.2` |
| `kter-release` | `kter-release-<version>` | `kter-release-2` |

バージョン番号は `<major>.<minor>` 形式。後方互換性のある変更はマイナー、動作変更はメジャーを上げる。

---

## 既存パッケージのアップデート

### 1. ソースを修正する

`linux-config` リポジトリ（`~/.config/`）でスクリプトを修正後、`linux-pkg` に同期:

```bash
cd ~/workspace/linux-pkg
make sync-sources
```

または手動で:

```bash
cp ~/.config/bin/auto-brightness packages/auto-brightness/sources/auto-brightness
cp ~/.config/systemd/user/auto-brightness.timer packages/auto-brightness/sources/auto-brightness.timer
```

`auto-brightness.service`（パッケージ版）は絶対パス版を使っているので、ローカルの `~/.config/systemd/user/auto-brightness.service` と**別管理**になっている。ローカル版の変更は手動で `packages/auto-brightness/sources/auto-brightness.service` に反映すること。

### 2. spec のバージョンを更新する

spec ファイルの `%changelog` を更新する:

```bash
# packages/auto-brightness/auto-brightness.spec の %changelog に追記
* Wed May 28 2026 Tomohiko Takahashi <takahashi@tomohiko.io> - 1.2-1
- 変更内容の説明
```

spec 内の `Version: %{_version}` は CI でタグから自動取得されるため変更不要。

### 3. コミット・タグ・プッシュ

```bash
git add .
git commit -m "feat(auto-brightness): 変更内容の説明"
git push origin main

git tag auto-brightness-1.2
git push origin auto-brightness-1.2
```

タグのプッシュで GitHub Actions が自動起動し、RPM ビルド → 署名 → S3 公開まで完了する。

### 4. CloudFront キャッシュ無効化（新バージョンが即時反映しない場合）

repodata がキャッシュされていると古いバージョンが表示される。以下で強制更新:

```bash
aws cloudfront create-invalidation \
  --distribution-id ES4NVQ58B8G82 \
  --profile prd \
  --paths "/rpm/noarch/repodata/*"
```

クライアント側のキャッシュも合わせてクリア:

```bash
sudo dnf clean metadata
```

---

## 新しいパッケージを追加する

### 1. ディレクトリとソースを配置

```bash
mkdir -p packages/<package-name>/sources
# ソースファイルをコピー
cp ~/.config/bin/<script> packages/<package-name>/sources/
```

### 2. spec ファイルを作成

`packages/<package-name>/<package-name>.spec` を作成。`auto-brightness.spec` を参考にする。

主要なポイント:
- `Version: %{_version}` — CI でタグから自動取得
- `BuildArch: noarch` — スクリプトのみの場合
- `%post` に `systemctl --global enable` を入れる（user timer の場合）
- `%preun` に `systemctl --global disable` を入れる

### 3. GitHub Actions ワークフローに追加

`.github/workflows/build-rpm.yml` の `on.push.tags` と `Determine package and version` ステップにパッケージを追加:

```yaml
on:
  push:
    tags:
      - 'auto-brightness-*'
      - 'kter-release-*'
      - '<new-package>-*'    # ← 追加
```

`Determine package and version` ステップの条件分岐にも追記する。

### 4. 初回タグを打つ

```bash
git add .
git commit -m "feat: add <package-name> package"
git push origin main
git tag <package-name>-1.0
git push origin <package-name>-1.0
```

---

## CI の手動実行

タグを打たずに CI を実行したい場合（テスト用）:

```bash
gh workflow run build-rpm.yml \
  --repo kter/linux-pkg \
  --field package=auto-brightness
```

または GitHub Web UI から「Actions」→「Build and Publish RPM」→「Run workflow」。

---

## CI の失敗確認とデバッグ

```bash
# 直近の CI 実行一覧
gh run list --repo kter/linux-pkg --limit 10

# 特定の実行のログを確認
gh run view <run-id> --repo kter/linux-pkg --log
```

よくある失敗原因は [troubleshooting.md](troubleshooting.md) を参照。

---

## 古いバージョンの RPM を削除する

リポジトリに古いバージョンを残しても問題はないが、削除したい場合:

```bash
# S3 から対象 RPM を削除
aws s3 rm s3://repo.devtools.site/rpm/noarch/auto-brightness-1.0-1.fc42.noarch.rpm \
  --profile prd

# createrepo でメタデータを再生成（CI 経由が安全）
# → 新バージョンのタグを打って CI 経由で再生成するのが確実
# または直接 createrepo_c を実行してアップロード

# CloudFront キャッシュを無効化
aws cloudfront create-invalidation \
  --distribution-id ES4NVQ58B8G82 \
  --profile prd \
  --paths "/rpm/noarch/repodata/*" "/rpm/noarch/auto-brightness-1.0-1.fc42.noarch.rpm"
```

---

## GPG 鍵の更新（4年後）

現在の鍵の有効期限: 2030年頃（発行: 2026-05-28、有効期間: 4年）

更新時の手順:
1. 新しい GPG 鍵を生成（`gpg --batch --gen-key`）
2. 公開鍵を S3 にアップロード（`aws s3 cp RPM-GPG-KEY-kter s3://repo.devtools.site/`）
3. GitHub Secret `GPG_PRIVATE_KEY` を更新
4. 新しい鍵で全 RPM を再署名してアップロード
5. クライアント側で `sudo rpm --import https://repo.devtools.site/RPM-GPG-KEY-kter` を実行

---

## `kter-release` のバージョンアップ

`.repo` ファイルの設定を変更したいとき:

```bash
# kter-release/kter-linux-config.repo を編集
git add kter-release/
git commit -m "chore(kter-release): update repo configuration"
git push origin main
git tag kter-release-2
git push origin kter-release-2
```

ユーザー側でも更新が必要:

```bash
sudo dnf update kter-release
```
