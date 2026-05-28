# パッケージ仕様: auto-brightness

## 概要

webcam で撮影したフレームの平均輝度を測定し、それに基づいてモニターのバックライト輝度を自動調整するスクリプト。30 秒間隔で実行される systemd ユーザータイマーとして動作する。ユーザーが手動でキーボードや waybar から輝度を変更した場合、その「オフセット」を次回以降も保持する。

## インストール済みファイル

| ファイル | パス | パーミッション |
|---|---|---|
| メインスクリプト | `/usr/local/bin/auto-brightness` | 0755 |
| systemd サービス | `/usr/lib/systemd/user/auto-brightness.service` | 0644 |
| systemd タイマー | `/usr/lib/systemd/user/auto-brightness.timer` | 0644 |

## 依存パッケージ

| パッケージ | 用途 |
|---|---|
| `brightnessctl` | バックライト輝度の読み取り・設定 |
| `/usr/bin/ffmpeg`（`ffmpeg-free` または `ffmpeg`） | webcam からフレームをキャプチャ |
| `ImageMagick`（`convert` コマンド） | フレームのグレースケール変換と平均輝度計算 |

`/usr/bin/ffmpeg` はパスで依存指定しているため、Fedora 標準の `ffmpeg-free` でも RPM Fusion の `ffmpeg` でも解決される。

## 設定可能な環境変数

| 変数名 | デフォルト値 | 説明 |
|---|---|---|
| `BRIGHTNESS_DEVICE` | `intel_backlight` | `brightnessctl -d` に渡すデバイス名 |
| `BRIGHTNESS_VIDEO` | `/dev/video0` | webcam デバイスパス |

例: `/dev/video2` を使う場合:
```bash
# ~/.config/environment.d/auto-brightness.conf
BRIGHTNESS_VIDEO=/dev/video2
```

## 定数（スクリプト内ハードコード）

| 定数 | 値 | 説明 |
|---|---|---|
| `MAX_BRIGHTNESS` | `7500` | システムの絶対最大値（手動オフセット込みでもこれを超えない） |
| `AUTO_MAX_BRIGHTNESS` | `3200` | 自動調整の上限。室内で明るすぎず暗すぎない値に設定 |
| `MIN_BRIGHTNESS` | `300` | 輝度の下限（0にすると画面が真っ暗になるため） |

変更したい場合はスクリプトを直接編集して新バージョンをリリースする。

## 輝度計算ロジック

```
webcam フレーム（320x240）
        ↓  ffmpeg でキャプチャ（JPEG）
        ↓  ImageMagick でグレースケール変換
        ↓  mean * 255 で平均輝度（0〜255）を得る
        ↓  ratio = mean / 255.0
        ↓  curved = sqrt(ratio)  ← sqrt カーブで低輝度域を自然に
        ↓  NEW_AUTO = MIN_BRIGHTNESS + (AUTO_MAX_BRIGHTNESS - MIN_BRIGHTNESS) * curved
        ↓  FINAL = NEW_AUTO + OFFSET
        ↓  FINAL をクランプ（MIN_BRIGHTNESS〜MAX_BRIGHTNESS）
        ↓  brightnessctl set FINAL
```

**sqrt カーブを使う理由:**  
線形マッピングだと低照度環境（夜間など）での輝度変化が急すぎる。sqrt により、暗い環境では輝度変化がゆっくりになり、自然な見た目になる。

## オフセット機構

ユーザーが手動でキーボードや waybar のスクロールで輝度を変更した場合、その差分を「オフセット」として記録する。次回以降の自動調整でもこのオフセットを加算し、好みの明るさを維持する。

```
OFFSET = CURRENT_BRIGHTNESS - LAST_AUTO
```

状態ファイル: `~/.local/state/auto-brightness/last-auto`

オフセットをリセットしたい場合:
```bash
rm ~/.local/state/auto-brightness/last-auto
```

## systemd ユニットの動作

### タイマー（`auto-brightness.timer`）

```ini
[Timer]
OnBootSec=10       # ログイン後 10 秒で初回実行
OnUnitActiveSec=30 # その後 30 秒間隔で繰り返し
```

### サービス（`auto-brightness.service`）

```ini
[Service]
Type=oneshot        # 実行して終了するタイプ
ExecStart=/usr/local/bin/auto-brightness
```

## インストール時の自動有効化（`%post` スクリプト）

```bash
# 全ユーザー向けに enable（次回ログイン時から自動起動）
systemctl --global enable auto-brightness.timer

# 現在ログイン中のユーザーには即座に start
for u in $(loginctl list-users ...); do
    systemctl --user start auto-brightness.timer
done
```

`systemctl --global enable` は `/etc/systemd/user/timers.target.wants/auto-brightness.timer` にシンボリックリンクを作成する。これにより、新規ユーザーのログイン時にも自動的にタイマーが起動する。

## アンインストール時の挙動（`%preun` スクリプト）

完全削除（`dnf remove`）時のみ:
- `systemctl --global disable auto-brightness.timer`
- 現在ログイン中のユーザーの `auto-brightness.timer` を `systemctl --user stop`

アップグレード（`dnf upgrade`）時は実行されない（`$1` が 1 の場合はスキップ）。

## ソースの管理

**原本:** `~/.config/bin/auto-brightness`（`linux-config` リポジトリ）  
**パッケージ用コピー:** `packages/auto-brightness/sources/auto-brightness`（本リポジトリ）

更新時は `make sync-sources` で原本からコピーを同期してから新バージョンをリリースする。

### ローカル版とパッケージ版の差分

| 項目 | ローカル版（`~/.config/`） | パッケージ版（RPM インストール）|
|---|---|---|
| スクリプトパス | `~/bin/auto-brightness` | `/usr/local/bin/auto-brightness` |
| サービスの ExecStart | `%h/bin/auto-brightness` | `/usr/local/bin/auto-brightness` |
| サービス優先度 | `~/.config/systemd/user/` が優先 | `/usr/lib/systemd/user/`（低優先） |

同じマシンに両方が存在する場合、`~/.config/systemd/user/auto-brightness.service` が優先して使われる。

## バージョン履歴

| バージョン | 変更内容 |
|---|---|
| 1.0 | 初回リリース。`Requires: ffmpeg` で依存解決に失敗するバグあり |
| 1.1 | `Requires: /usr/bin/ffmpeg` に変更。`ffmpeg-free` でも依存解決可能に |
