# CaptyOU - リアルタイムポーズ・表情キャプチャシステム

MacBook Proの内蔵カメラとNeural Engineを活用した、リアルタイムポーズ・表情キャプチャシステムです。3Dアバターに反映して生配信に利用できます。

## 特徴

- **リアルタイム処理**: MacBook ProのNeural Engine（Core ML）で高速化
- **ポーズ推定**: MediaPipe Poseで全身のポーズをキャプチャ
- **表情認識**: MediaPipe Face Meshで顔の表情を詳細にキャプチャ
- **3Dアバター統合**: BlenderまたはUnityに対応
- **配信対応**: Virtual Camera経由でOBSなどの配信ソフトに統合

## システム要件

- macOS 11.0 (Big Sur) 以降
- MacBook Pro with M1/M2/M3チップ（Neural Engine搭載）
- Python 3.9以降
- Blender 3.0以降 または Unity 2021.3以降（オプション）

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/captyou.git
cd captyou

# 仮想環境を作成
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

## クイックスタート

### 基本的な使用方法

```python
from captyou import CameraCapture, PoseEstimator, FaceExpression

# カメラを初期化
camera = CameraCapture()

# ポーズ推定器と表情認識器を初期化
pose_estimator = PoseEstimator(use_coreml=True)
face_estimator = FaceExpression(use_coreml=True)

# リアルタイムキャプチャ開始
for frame in camera.capture():
    pose_data = pose_estimator.process(frame)
    face_data = face_estimator.process(frame)

    # データを3Dアバターに送信
    # ...
```

### Blenderとの統合

```python
from captyou.avatar import BlenderAvatar

avatar = BlenderAvatar()
avatar.connect()
avatar.update_pose(pose_data)
avatar.update_expression(face_data)
```

### Unityとの統合（OSC経由）

```python
from captyou.avatar import UnityAvatar

avatar = UnityAvatar(host="localhost", port=8000)
avatar.connect()
avatar.send_pose(pose_data)
avatar.send_expression(face_data)
```

## アーキテクチャ

```
┌─────────────────┐
│  MacBook Pro    │
│  内蔵カメラ      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Camera Capture │
│  (AVFoundation) │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Pose   │ │ Face   │
│Estimator│ │Expresn│
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
┌─────────────────┐
│   Core ML       │
│ (Neural Engine) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Avatar System  │
│ Blender / Unity │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Virtual Camera  │
│  → OBS配信      │
└─────────────────┘
```

## プロジェクト構造

```
captyou/
├── src/
│   ├── camera/          # カメラキャプチャ
│   ├── pose/            # ポーズ推定
│   ├── face/            # 表情認識
│   ├── coreml/          # Core ML変換・最適化
│   ├── avatar/          # 3Dアバター統合
│   └── streaming/       # 配信統合
├── examples/            # サンプルコード
├── models/              # 機械学習モデル
└── tests/               # テストコード
```

## パフォーマンス

Neural Engine活用により、以下のパフォーマンスを実現：

- ポーズ推定: 30+ FPS
- 表情認識: 30+ FPS
- 総合レイテンシ: < 50ms

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します！

## 参考資料

- [MediaPipe](https://google.github.io/mediapipe/)
- [Core ML](https://developer.apple.com/documentation/coreml)
- [Blender Python API](https://docs.blender.org/api/current/)
