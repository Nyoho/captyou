#!/usr/bin/env python3
"""
Core MLモデルセットアップスクリプト

MediaPipeモデルをダウンロードしてCore MLに変換し、Neural Engine最適化します。

使用方法:
    python scripts/setup_coreml_models.py
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
from src.coreml.converter import setup_models, CoreMLConverter

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def main():
    print("=" * 70)
    print("CaptyOU - Core ML Model Setup")
    print("=" * 70)
    print("\nMediaPipeモデルをダウンロードしてCore MLに変換します。")
    print("Neural Engineで高速化されたモデルを生成します。\n")
    print("=" * 70)

    # モデルディレクトリ
    models_dir = "models"

    # モデルをセットアップ
    converted_models = setup_models(models_dir)

    print("\n" + "=" * 70)
    print("セットアップ完了!")
    print("=" * 70)

    if converted_models:
        print("\n変換されたモデル:")
        for model_type, model_path in converted_models.items():
            print(f"  {model_type}: {model_path}")

            # ベンチマーク実行
            print(f"\n{model_type}モデルのベンチマーク中...")
            results = CoreMLConverter.benchmark_model(model_path, num_iterations=50)
            if results:
                print(f"  平均推論時間: {results['avg_time_ms']:.2f} ms")
                print(f"  推定FPS: {results['fps']:.1f}")

        print("\n" + "=" * 70)
        print("使用方法:")
        print("=" * 70)
        print("\nPython APIで使用:")
        print("""
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
""")

        print("\nデモプログラムで使用:")
        print("  python examples/basic_demo.py --use-coreml")

    else:
        print("\n警告: モデルの変換に失敗しました")
        print("\nトラブルシューティング:")
        print("  1. インターネット接続を確認")
        print("  2. coremltools がインストールされているか確認")
        print("     pip install coremltools")
        print("  3. macOS 13 以降を使用しているか確認")

    print("\n")


if __name__ == "__main__":
    main()
