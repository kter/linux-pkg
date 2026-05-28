# トラブルシューティング

実際に遭遇した問題と対処の記録。

---

## dnf install 時の問題

### `nothing provides ffmpeg needed by auto-brightness`

**症状:**
```
Failed to resolve the transaction:
Problem: conflicting requests
  - nothing provides ffmpeg needed by auto-brightness-1.0-1.fc42.noarch from kter-linux-pkg
```

**原因:**  
Fedora の標準リポジトリには `ffmpeg` という名前のパッケージが存在しない。`ffmpeg-free`（標準）または `ffmpeg`（RPM Fusion）がコマンドを提供している。spec で `Requires: ffmpeg` と書くと依存解決に失敗する。

**対処:**  
spec の Requires を `Requires: /usr/bin/ffmpeg` に変更する。パッケージ名ではなくファイルパスで指定すると、`ffmpeg-free` でも `ffmpeg`（RPM Fusion）でも解決される。

**現在の設定:** `packages/auto-brightness/auto-brightness.spec` では `Requires: /usr/bin/ffmpeg` を使用済み。

---

### `repomd.xml GPG signature verification error: Signing key not found`

**症状:**
```
>>> repomd.xml GPG signature verification error: Signing key not found
```
その後、鍵のインポートが行われ、インストール自体は続行される。

**原因:**  
`repo_gpgcheck=1` が設定されているが、初回インストール時はまだ GPG 鍵がローカルの RPM データベースにインポートされていない。

**対処:**  
初回は警告のみで処理が続行される（鍵は自動インポートされる）。2回目以降は警告が出なくなる。実害はないが気になる場合は `.repo` ファイルの `repo_gpgcheck=0` にすることで抑制できる（ただしセキュリティが下がる）。

---

### 古いバージョンしか表示されない / インストールされない

**症状:**  
新バージョンをリリースしたのに `dnf install` で古いバージョンが対象になる。

**原因:**  
- クライアント側の `dnf` キャッシュが古い repodata を参照している
- CloudFront が古い repodata をキャッシュしている（どちらか、または両方）

**対処:**

CloudFront キャッシュを無効化する:
```bash
aws cloudfront create-invalidation \
  --distribution-id ES4NVQ58B8G82 \
  --profile prd \
  --paths "/rpm/noarch/repodata/*"
```

クライアント側のキャッシュをクリアする:
```bash
sudo dnf clean metadata
```

その後再度 `dnf install` を試みる。

---

## CI（GitHub Actions）の問題

### GPG 署名ステップが失敗する

**症状:**
```
rpmsign: error: ...
```

**確認ポイント:**
1. GitHub Secret `GPG_PRIVATE_KEY` が正しくセットされているか
   ```bash
   gh secret list --repo kter/linux-pkg
   ```
2. `GPG_PASSPHRASE` が一致しているか（`%no-protection` で生成した鍵は空文字が正しい）
3. `~/.rpmmacros` の `%__gpg_sign_cmd` の `passphrase-fd` 指定が正しいか
4. `pinentry-mode loopback` が指定されているか（非インタラクティブ環境で必要）

---

### OIDC 認証が失敗する

**症状:**
```
Error: Could not assume role with OIDC: ...
```

**確認ポイント:**
1. IAM ロールの信頼ポリシーで `repo:kter/linux-pkg:*` が設定されているか
   ```bash
   aws iam get-role --role-name rpm-publisher-linux-pkg --profile prd \
     --query 'Role.AssumeRolePolicyDocument'
   ```
2. GitHub Actions ワークフローの `permissions` に `id-token: write` があるか
3. ロール ARN がワークフロー内の `role-to-assume` と一致しているか

---

### `createrepo_c` が見つからない

**症状:**
```
bash: createrepo_c: command not found
```

**対処:**  
CI ワークフローの `dnf install` に `createrepo_c` が含まれているか確認する:

```yaml
- name: Install build dependencies
  run: |
    dnf install -y \
      rpm-build \
      rpm-sign \
      createrepo_c \    # ← これが必要
      awscli2 \
      gnupg2 \
      git \
      rpmdevtools
```

---

## S3 / CloudFront の問題

### CloudFront 経由でファイルが 403 になる

**症状:**
```
curl -I https://repo.devtools.site/rpm/noarch/repodata/repomd.xml
HTTP/2 403
```

**確認ポイント:**
1. S3 バケットポリシーの `AWS:SourceArn` が現在の CloudFront ディストリビューション ARN と一致しているか
   ```bash
   aws s3api get-bucket-policy --bucket repo.devtools.site --profile prd
   ```
2. OAC が CloudFront のオリジン設定に正しく紐付いているか
3. ファイルが S3 に実際に存在するか
   ```bash
   aws s3 ls s3://repo.devtools.site/rpm/noarch/ --profile prd
   ```

---

### S3 にファイルはあるが CloudFront で古い内容が返る

`repodata/*` のキャッシュ TTL はほぼ 0 に設定しているが、まれにキャッシュが残る場合:

```bash
aws cloudfront create-invalidation \
  --distribution-id ES4NVQ58B8G82 \
  --profile prd \
  --paths "/*"
```

`"/*"` で全ファイルを無効化する（コスト: 月 1000 パスまで無料）。

---

## ローカル開発の問題

### `make sync-sources` で Permission denied

**症状:**
```
cp: cannot open '~/.config/bin/auto-brightness' for reading: Permission denied
```

**対処:**  
パスが `~` 展開されていない可能性がある。Makefile の `$(HOME)` 変数を確認:
```makefile
LINUX_CONFIG := $(HOME)/.config
```

`$(HOME)` は `make` 実行時に正しく展開される。`~` は Makefile では展開されないため使わないこと。

---

### `rpmbuild` がソースファイルを見つけられない

**症状:**
```
error: File not found: /home/ttakahashi/rpmbuild/SOURCES/auto-brightness
```

**対処:**  
`make build-local` を実行する前に `rpmdev-setuptree` でディレクトリ構造を作成し、ソースを `~/rpmbuild/SOURCES/` にコピーする:

```bash
rpmdev-setuptree
cp packages/auto-brightness/sources/* ~/rpmbuild/SOURCES/
rpmbuild -bb --define "_version 1.0" --define "dist .local" \
  packages/auto-brightness/auto-brightness.spec
```
