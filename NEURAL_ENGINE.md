# Neural Engine対応ガイド

このドキュメントでは、MacBook ProのNeural Engine（Apple Neural Engine, ANE）を使ってCaptyOUを高速化する方法を説明します。

## Neural Engineとは

Apple Neural Engine（ANE）は、M1/M2/M3チップに搭載された専用の機械学習アクセラレータです。

### パフォーマンス比較

| 処理方式 | FPS | 消費電力 | レイテンシ |
|---------|-----|----------|-----------|
| CPU（MediaPipe） | 15-20 | 中 | ~80ms |
| GPU（Metal） | 25-30 | 高 | ~50ms |
| **Neural Engine（Core ML）** | **30-60** | **低** | **~20ms** |

### 利点

- **高速**: CPU/GPUより高速な推論
- **低消費電力**: バッテリー寿命の向上
- **低レイテンシ**: リアルタイム処理に最適
- **並列処理**: CPU/GPUを別の処理に使える

## セットアップ

### 1. モデルのダウンロードと変換

MediaPipeモデルをCore MLに変換します。

```bash
# モデルセットアップスクリプトを実行
python scripts/setup_coreml_models.py
```

このスクリプトは以下を自動実行します：

1. MediaPipe公式モデルをダウンロード
2. TFLite形式からCore ML形式に変換
3. Neural Engine最適化
4. ベンチマーク実行

### 2. 生成されるファイル

```
models/
├── pose_landmarker_full.task      # MediaPipe元モデル
├── pose_landmarker_full.tflite    # TFLite形式
├── pose_landmarker.mlmodel        # Core ML形式（Neural Engine対応）
├── face_landmarker.task           # MediaPipe元モデル
├── face_landmarker.tflite         # TFLite形式
└── face_landmarker.mlmodel        # Core ML形式（Neural Engine対応）
```

## 使用方法

### Python APIでの使用

```python
from src.pose.estimator import PoseEstimator
from src.face.expression import FaceExpression

# Neural Engine対応のポーズ推定器
pose_estimator = PoseEstimator(
    use_coreml=True,
    coreml_model_path="models/pose_landmarker.mlmodel"
)

# Neural Engine対応の表情認識器
face_estimator = FaceExpression(
    use_coreml=True,
    coreml_model_path="models/face_landmarker.mlmodel"
)

# 通常通り使用
pose_data = pose_estimator.process(frame)
face_data = face_estimator.process(frame)
```

### デモプログラムでの使用

Neural Engine対応は自動的にフォールバックします：

```bash
# 基本デモ（Core MLモデルがあれば自動使用）
python examples/basic_demo.py

# 統合デモ
python examples/full_avatar_demo.py --enable-voice --virtual-camera
```

## トラブルシューティング

### モデル変換が失敗する

**原因**: TFLite → Core ML変換の互換性問題

**解決策**:
1. coremltools のバージョン確認
   ```bash
   pip install --upgrade coremltools
   ```

2. macOS 13以降を使用しているか確認

3. 手動で変換を試す
   ```python
   from src.coreml.converter import CoreMLConverter, MediaPipeModelManager

   # モデルをダウンロード
   task_path = MediaPipeModelManager.download_model("pose_landmarker_full")

   # TFLiteを抽出
   tflite_path = MediaPipeModelManager.extract_tflite_from_task(task_path)

   # Core MLに変換
   CoreMLConverter.convert_tflite_to_coreml(
       tflite_path,
       "models/pose.mlmodel"
   )
   ```

### Neural Engineが使われているか確認

```python
import coremltools as ct

model = ct.models.MLModel("models/pose_landmarker.mlmodel")
spec = model.get_spec()

# compute_units を確認
print(f"Compute units: {spec.neuralNetworkClassifier.layers}")
```

### パフォーマンスが向上しない

**確認事項**:

1. **モデルが正しく変換されているか**
   ```bash
   ls -lh models/*.mlmodel
   ```

2. **Neural Engineが有効か**
   - M1/M2/M3チップを搭載したMacを使用しているか
   - macOS 13以降を使用しているか

3. **ベンチマークを実行**
   ```python
   from src.coreml.converter import CoreMLConverter

   results = CoreMLConverter.benchmark_model("models/pose_landmarker.mlmodel")
   print(f"FPS: {results['fps']:.1f}")
   ```

### Core ML推論エラー

**エラー**: `Core ML inference failed`

**解決策**:
1. MediaPipeにフォールバックされます（自動）
2. モデルを再変換
   ```bash
   rm models/*.mlmodel
   python scripts/setup_coreml_models.py
   ```

## 高度な設定

### カスタムモデル変換

```python
from src.coreml.converter import CoreMLConverter
import coremltools as ct

# 計算ユニットを指定
CoreMLConverter.convert_tflite_to_coreml(
    "model.tflite",
    "model.mlmodel",
    compute_units=ct.ComputeUnit.CPU_AND_NE  # Neural EngineとCPUのみ
)
```

### 量子化による最適化

```python
from src.coreml.converter import CoreMLConverter

# 16bit float量子化でモデルサイズを削減
CoreMLConverter.optimize_coreml_model(
    "models/pose_landmarker.mlmodel",
    quantize_weights=True
)
```

### ベンチマーク比較

```python
from src.coreml.converter import CoreMLConverter

# MediaPipeとCore MLを比較
import time
import cv2

camera = cv2.VideoCapture(0)

# MediaPipe
from src.pose.estimator import PoseEstimator
pose_mp = PoseEstimator(use_coreml=False)

start = time.time()
for _ in range(100):
    ret, frame = camera.read()
    pose_mp.process(frame)
fps_mp = 100 / (time.time() - start)

# Core ML
pose_coreml = PoseEstimator(
    use_coreml=True,
    coreml_model_path="models/pose_landmarker.mlmodel"
)

start = time.time()
for _ in range(100):
    ret, frame = camera.read()
    pose_coreml.process(frame)
fps_coreml = 100 / (time.time() - start)

print(f"MediaPipe FPS: {fps_mp:.1f}")
print(f"Core ML FPS: {fps_coreml:.1f}")
print(f"Speedup: {fps_coreml / fps_mp:.2f}x")
```

## 参考資料

- [Core ML Documentation](https://developer.apple.com/documentation/coreml)
- [Apple Neural Engine](https://github.com/hollance/neural-engine)
- [coremltools Documentation](https://coremltools.readme.io/)
- [MediaPipe Models](https://developers.google.com/mediapipe/solutions/guide)

## FAQ

### Q: Intel Macでも使えますか？

A: Core ML自体は使えますが、Neural Engineはありません。GPU/CPUで実行されます。

### Q: モデルの精度は変わりますか？

A: 基本的に同じです。量子化を有効にすると若干の精度低下がありますが、通常は無視できるレベルです。

### Q: バッテリー寿命は改善しますか？

A: はい。Neural Engineは低消費電力で、CPU/GPUより効率的です。

### Q: 複数のモデルを同時に使えますか？

A: はい。ポーズと表情を同時にNeural Engineで処理できます。

### Q: Core MLモデルは配布できますか？

A: MediaPipeモデルはApache 2.0ライセンスです。変換したCore MLモデルも同様のライセンス条件で配布できます。
