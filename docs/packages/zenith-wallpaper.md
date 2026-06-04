# パッケージ仕様: zenith-wallpaper

## 概要

現在地と現在時刻から天文計算した**実際の夜空**を sway/Wayland デスクトップ壁紙として表示する Go バイナリ。Lambert 等積方位投影（天頂中心）で「真上を見上げた全天ドーム」を描画し、1時間ごとに自動更新される。天の川・8400 星・惑星・月をリアルタイムで描画する。

## インストール済みファイル

| ファイル | パス | パーミッション |
|---|---|---|
| バイナリ | `/usr/bin/zenith-wallpaper` | 0755 |
| systemd サービス | `/usr/lib/systemd/user/zenith-wallpaper.service` | 0644 |
| systemd タイマー | `/usr/lib/systemd/user/zenith-wallpaper.timer` | 0644 |

## 依存パッケージ

| パッケージ | 用途 | 種別 |
|---|---|---|
| `sway` | `swaymsg` コマンド（壁紙適用） | 必須 |
| `geoclue2` | D-Bus 経由の位置情報取得 | 推奨（省略時 ipinfo.io または固定フォールバック） |

## バイナリの特徴

- **~38 MB のセルフコンテインドバイナリ**: NASA Deep Star Maps 2020（16384×8192 JPEG、28 MB）と Yale Bright Star Catalogue（200 KB CSV）を `go:embed` でバイナリに内包しているため、初回ダウンロード不要。
- **CGO 無効**: `CGO_ENABLED=0 go build -trimpath` でビルド。外部共有ライブラリ依存なし（godbus は D-Bus ソケット通信のみ）。
- 実行ごとに `~/.cache/zenith-wallpaper/<出力名>.png` を生成し `swaymsg output <name> bg <path> fill` で適用。複数ディスプレイ対応。

## インストール後の手動設定（必須）

インストールのみで timer は自動有効化されない（sway セッションへの依存があるため）。ユーザーが以下を手動で実行する:

```bash
# timer を有効化
systemctl --user enable --now zenith-wallpaper.timer

# sway 起動時に即時実行するよう設定（~/.config/sway/config に追記）
output * bg #000000 solid_color
exec /usr/bin/zenith-wallpaper
```

## 位置情報の取得順

1. GeoClue2（D-Bus、`geoclue2` インストール時）
2. ipinfo.io（HTTP、インターネット接続時）
3. `~/.cache/zenith-wallpaper/location.json`（前回キャッシュ）
4. フォールバック: グリニッジ（51.48°N, 0.00°E）

## ローカル版とパッケージ版の差分

| 項目 | ローカル版（`make install`） | パッケージ版（RPM インストール） |
|---|---|---|
| バイナリパス | `~/.local/bin/zenith-wallpaper` | `/usr/bin/zenith-wallpaper` |
| サービスの ExecStart | `%h/.local/bin/zenith-wallpaper` | `/usr/bin/zenith-wallpaper` |
| サービス優先度 | `~/.config/systemd/user/` が優先 | `/usr/lib/systemd/user/`（低優先） |

同じマシンに両方が存在する場合、`~/.config/systemd/user/zenith-wallpaper.service` が優先して使われる。

## ソースの管理

**原本:** `~/workspace/zenith-wallpaper`（upstream リポジトリ）  
**tarball:** `packages/zenith-wallpaper/sources/zenith-wallpaper-<version>.tar.gz`  
**パッケージ版 unit:** `packages/zenith-wallpaper/sources/` 配下（`ExecStart` のパスが異なる）

更新時は `make sync-sources` で tarball を再生成してから新バージョンをリリースする。tarball には `go mod vendor` 済みの依存が含まれるため、CI ビルドはネットワーク不要。

## ビルド方法

```bash
# tarball 生成（upstream に vendor が必要）
make sync-sources

# ローカル RPM ビルド
make build-local-zenith-wallpaper
# → ~/rpmbuild/RPMS/x86_64/zenith-wallpaper-1.0-1.local.x86_64.rpm
```

## データクレジット（バイナリ内包）

| データ | 出典 | ライセンス |
|---|---|---|
| Milky Way panorama | NASA/GSFC SVS, Deep Star Maps 2020 | Public domain |
| Yale Bright Star Catalogue (BSC5) | Hoffleit & Warren (1991), CDS Strasbourg | Public domain |
| 天文計算ライブラリ | soniakeys/meeus | MIT |

## バージョン履歴

| バージョン | 変更内容 |
|---|---|
| 1.0 | 初回リリース |
