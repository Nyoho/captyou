# インストールガイド

## 必要要件

### システム要件
- macOS 11.0 (Big Sur) 以降
- MacBook Pro with M1/M2/M3チップ推奨（Neural Engine搭載）
- Python 3.9～3.12（3.13は未対応）
- 8GB RAM以上推奨

### ソフトウェア要件
- Python 3.9～3.12
- uv（推奨）または pip
- Homebrew（推奨）

## インストール手順

### 方法A: uv を使う（推奨・最も簡単）

#### 1. uv のインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. リポジトリのクローン

```bash
git clone https://github.com/yourusername/captyou.git
cd captyou
```

#### 3. 完了！

依存関係は`uv run`を実行した際に自動的にインストールされます。
仮想環境の作成も不要です。

```bash
# そのまま実行できます
uv run examples/basic_demo.py
```

### 方法B: pip を使う（従来の方法）

#### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/captyou.git
cd captyou
```

#### 2. 仮想環境の作成

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. 依存関係のインストール

```bash
# 基本的な依存関係
pip install -r requirements.txt

# オプション: 配信機能を使う場合
pip install pyvirtualcam

# オプション: 開発ツール
pip install -e ".[dev]"
```

## 追加ソフトウェアのインストール

### OBS Studio のインストール（Virtual Camera用）

Virtual Cameraを使用する場合は、OBS Studioが必要です。

```bash
# Homebrewでインストール
brew install --cask obs

# または公式サイトからダウンロード
# https://obsproject.com/
```

### BlackHole のインストール（声質変換用）

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

### カメラ・マイクアクセス許可の設定

macOSのプライバシー設定で、カメラとマイクへのアクセスを許可してください：

1. システム環境設定 → セキュリティとプライバシー → カメラ
   - ターミナル（またはPythonアプリ）にチェックを入れる
2. システム環境設定 → セキュリティとプライバシー → マイク
   - ターミナル（またはPythonアプリ）にチェックを入れる

## 動作確認

### 基本デモの実行

#### uvを使う場合

```bash
uv run examples/basic_demo.py
```

#### pipを使う場合

```bash
python examples/basic_demo.py
```

カメラ映像が表示され、ポーズと表情がリアルタイムで検出されれば成功です。

### 声質変換デモの実行

#### uvを使う場合

```bash
# オーディオデバイス一覧を表示
uv run examples/voice_conversion_demo.py --list-devices

# 声質変換を実行（男性→女性）
uv run examples/voice_conversion_demo.py --mode world_vocoder --pitch 5.0
```

#### pipを使う場合

```bash
# オーディオデバイス一覧を表示
python examples/voice_conversion_demo.py --list-devices

# 声質変換を実行（男性→女性）
python examples/voice_conversion_demo.py --mode world_vocoder --pitch 5.0
```

マイクに向かって話すと、変換された音声がBlackHoleに出力されます。
OBSなどの配信ソフトで音声入力としてBlackHoleを選択すると、変換された声を配信できます。

### 統合デモの実行（映像+音声）

#### uvを使う場合

```bash
uv run examples/full_avatar_demo.py \
  --unity-host localhost --unity-port 9000 \
  --enable-voice --voice-pitch 5.0 \
  --virtual-camera --show-preview
```

#### pipを使う場合

```bash
python examples/full_avatar_demo.py \
  --unity-host localhost --unity-port 9000 \
  --enable-voice --voice-pitch 5.0 \
  --virtual-camera --show-preview
```

## Neural Engine対応（オプション）

MacBook ProのNeural Engineで高速化したい場合は、Core MLモデルをセットアップします。

### モデルのダウンロードと変換

```bash
python scripts/setup_coreml_models.py
```

このスクリプトは以下を実行します：
1. MediaPipe公式モデルをダウンロード
2. TFLite → Core ML形式に変換
3. Neural Engine最適化
4. ベンチマーク実行

### 結果

変換が成功すると、`models/`ディレクトリに以下のファイルが生成されます：

```
models/
├── pose_landmarker.mlmodel   # ポーズ推定（Neural Engine対応）
└── face_landmarker.mlmodel   # 表情認識（Neural Engine対応）
```

### パフォーマンス向上

- **2-3倍高速化**: 30-60 FPS
- **レイテンシ削減**: ~20ms
- **省電力**: バッテリー寿命向上

詳細は [NEURAL_ENGINE.md](NEURAL_ENGINE.md) を参照してください。

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
