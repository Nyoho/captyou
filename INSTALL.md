# インストールガイド

## 必要要件

### システム要件
- macOS 11.0 (Big Sur) 以降
- MacBook Pro with M1/M2/M3チップ推奨（Neural Engine搭載）
- Python 3.9以降
- 8GB RAM以上推奨

### ソフトウェア要件
- Python 3.9+
- pip
- Homebrew（推奨）

## インストール手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/captyou.git
cd captyou
```

### 2. 仮想環境の作成

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存関係のインストール

```bash
# 基本的な依存関係
pip install -r requirements.txt

# オプション: 配信機能を使う場合
pip install pyvirtualcam

# オプション: 開発ツール
pip install -e ".[dev]"
```

### 4. OBS Studio のインストール（Virtual Camera用）

Virtual Cameraを使用する場合は、OBS Studioが必要です。

```bash
# Homebrewでインストール
brew install --cask obs

# または公式サイトからダウンロード
# https://obsproject.com/
```

### 5. BlackHole のインストール（声質変換用）

声質変換機能を使用する場合は、BlackHoleが必要です。

```bash
# Homebrewでインストール
brew install blackhole-2ch

# または公式サイトからダウンロード
# https://github.com/ExistentialAudio/BlackHole
```

インストール後、Audio MIDI設定で「複数出力装置」を設定：

1. アプリケーション → ユーティリティ → Audio MIDI設定.app を開く
2. 左下の「+」をクリック → 「複数出力装置を作成」
3. 「BlackHole 2ch」と「内蔵出力」の両方にチェック
4. これでBlackHoleに送った音声を自分でも聞くことができます

### 6. カメラ・マイクアクセス許可の設定

macOSのプライバシー設定で、カメラとマイクへのアクセスを許可してください：

1. システム環境設定 → セキュリティとプライバシー → カメラ
   - ターミナル（またはPythonアプリ）にチェックを入れる
2. システム環境設定 → セキュリティとプライバシー → マイク
   - ターミナル（またはPythonアプリ）にチェックを入れる

## 動作確認

### 基本デモの実行

```bash
python examples/basic_demo.py
```

カメラ映像が表示され、ポーズと表情がリアルタイムで検出されれば成功です。

### 声質変換デモの実行

```bash
# オーディオデバイス一覧を表示
python examples/voice_conversion_demo.py --list-devices

# 声質変換を実行（男性→女性）
python examples/voice_conversion_demo.py --mode world_vocoder --pitch 5.0
```

マイクに向かって話すと、変換された音声がBlackHoleに出力されます。
OBSなどの配信ソフトで音声入力としてBlackHoleを選択すると、変換された声を配信できます。

### 統合デモの実行（映像+音声）

```bash
# 完全統合デモ
python examples/full_avatar_demo.py \
  --unity-host localhost --unity-port 9000 \
  --enable-voice --voice-pitch 5.0 \
  --virtual-camera --show-preview
```

### トラブルシューティング

#### カメラが開けない

```bash
# カメラデバイスを確認
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

Falseの場合：
- カメラのアクセス許可を確認
- 他のアプリがカメラを使用していないか確認
- カメラデバイスIDを変更（0 → 1など）

#### MediaPipeのエラー

```bash
# MediaPipeを再インストール
pip uninstall mediapipe
pip install mediapipe
```

#### Virtual Cameraが使えない

```bash
# OBS Virtual Cameraドライバーを確認
ls /Library/CoreMediaIO/Plug-Ins/DAL/
```

`obs-mac-virtualcam.plugin`が存在するか確認してください。

#### Neural Engine（Core ML）が使えない

Core MLはmacOS 11.0以降、Appleシリコン搭載Macで最適化されます。
Intel Macでも動作しますが、Neural Engineによる高速化はありません。

## オプショナル設定

### Blender統合

Blenderでアバターを制御する場合：

```bash
# Blenderをインストール
brew install --cask blender

# Blender Python環境に依存関係をインストール
# Blender内のPythonコンソールで実行
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
```

### Unity統合

UnityでOSC経由でアバターを制御する場合：

1. UnityにOSC受信スクリプトを追加
2. `examples/streaming_demo.py`の`--unity-port`を設定

## 次のステップ

- [README.md](README.md) - 基本的な使い方
- [examples/](examples/) - サンプルコード
- Core ML最適化を試す（高速化）

## サポート

問題が発生した場合：
1. [Issues](https://github.com/yourusername/captyou/issues)で既存の問題を検索
2. 新しいIssueを作成（エラーメッセージ、環境情報を含める）
