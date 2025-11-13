"""
Core ML変換モジュール

MediaPipeモデルをCore MLに変換し、Neural Engineで最適化します。
"""

import coremltools as ct
import numpy as np
from typing import Optional, Tuple
import logging
import os

logger = logging.getLogger(__name__)


class CoreMLConverter:
    """
    Core ML変換クラス

    MediaPipeなどのモデルをCore MLに変換し、
    Apple Neural Engineで高速実行できるようにします。
    """

    @staticmethod
    def convert_pose_model(
        onnx_path: str,
        output_path: str,
        image_size: Tuple[int, int] = (256, 256),
    ) -> bool:
        """
        ポーズ推定モデルをCore MLに変換

        Args:
            onnx_path: ONNX形式のモデルパス
            output_path: 出力するCore MLモデルパス
            image_size: 入力画像サイズ (width, height)

        Returns:
            変換成功時True
        """
        try:
            logger.info(f"Converting pose model: {onnx_path}")

            # ONNXモデルを読み込み
            model = ct.convert(
                onnx_path,
                inputs=[
                    ct.ImageType(
                        name="input",
                        shape=(1, 3, image_size[1], image_size[0]),
                        scale=1.0 / 255.0,
                        bias=[0, 0, 0],
                    )
                ],
                compute_units=ct.ComputeUnit.ALL,  # Neural Engine + GPU + CPUを使用
                minimum_deployment_target=ct.target.macOS13,
            )

            # メタデータを追加
            model.author = "CaptyOU"
            model.short_description = "Pose estimation model optimized for Neural Engine"
            model.version = "1.0"

            # 保存
            model.save(output_path)
            logger.info(f"Model saved: {output_path}")

            # モデル情報を表示
            spec = model.get_spec()
            logger.info(f"Model inputs: {[i.name for i in spec.description.input]}")
            logger.info(f"Model outputs: {[o.name for o in spec.description.output]}")

            return True

        except Exception as e:
            logger.error(f"Failed to convert pose model: {e}")
            return False

    @staticmethod
    def convert_face_model(
        onnx_path: str,
        output_path: str,
        image_size: Tuple[int, int] = (192, 192),
    ) -> bool:
        """
        顔認識モデルをCore MLに変換

        Args:
            onnx_path: ONNX形式のモデルパス
            output_path: 出力するCore MLモデルパス
            image_size: 入力画像サイズ (width, height)

        Returns:
            変換成功時True
        """
        try:
            logger.info(f"Converting face model: {onnx_path}")

            # ONNXモデルを読み込み
            model = ct.convert(
                onnx_path,
                inputs=[
                    ct.ImageType(
                        name="input",
                        shape=(1, 3, image_size[1], image_size[0]),
                        scale=1.0 / 255.0,
                        bias=[0, 0, 0],
                    )
                ],
                compute_units=ct.ComputeUnit.ALL,  # Neural Engine + GPU + CPUを使用
                minimum_deployment_target=ct.target.macOS13,
            )

            # メタデータを追加
            model.author = "CaptyOU"
            model.short_description = (
                "Face mesh model optimized for Neural Engine"
            )
            model.version = "1.0"

            # 保存
            model.save(output_path)
            logger.info(f"Model saved: {output_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to convert face model: {e}")
            return False

    @staticmethod
    def optimize_model(
        mlmodel_path: str,
        output_path: Optional[str] = None,
        quantize_weights: bool = True,
    ) -> bool:
        """
        Core MLモデルを最適化

        Args:
            mlmodel_path: Core MLモデルパス
            output_path: 出力パス（Noneの場合は上書き）
            quantize_weights: 重みを量子化（16bit float）

        Returns:
            最適化成功時True
        """
        try:
            logger.info(f"Optimizing model: {mlmodel_path}")

            # モデルを読み込み
            model = ct.models.MLModel(mlmodel_path)

            if quantize_weights:
                # 重みを16bit floatに量子化（モデルサイズを削減）
                from coremltools.models.neural_network import quantization_utils

                # 量子化設定
                config = {
                    "mode": "linear_quantization",
                    "dtype": "float16",
                }

                # 量子化を実行
                model_spec = model.get_spec()
                quantized_spec = quantization_utils.quantize_weights(
                    model_spec, nbits=16
                )

                # 新しいモデルを作成
                model = ct.models.MLModel(quantized_spec)

            # 保存
            if output_path is None:
                output_path = mlmodel_path

            model.save(output_path)
            logger.info(f"Optimized model saved: {output_path}")

            # ファイルサイズを表示
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"Model size: {size_mb:.2f} MB")

            return True

        except Exception as e:
            logger.error(f"Failed to optimize model: {e}")
            return False

    @staticmethod
    def benchmark_model(mlmodel_path: str, num_iterations: int = 100) -> dict:
        """
        Core MLモデルのパフォーマンスをベンチマーク

        Args:
            mlmodel_path: Core MLモデルパス
            num_iterations: 実行回数

        Returns:
            ベンチマーク結果の辞書
        """
        try:
            import time

            logger.info(f"Benchmarking model: {mlmodel_path}")

            # モデルを読み込み
            model = ct.models.MLModel(mlmodel_path)

            # 入力サンプルを作成
            spec = model.get_spec()
            input_name = spec.description.input[0].name

            # 入力タイプに応じてサンプルデータを作成
            input_type = spec.description.input[0].type
            if input_type.HasField("imageType"):
                # 画像入力の場合
                from PIL import Image

                width = input_type.imageType.width
                height = input_type.imageType.height
                sample_image = Image.new("RGB", (width, height))
                sample_input = {input_name: sample_image}
            else:
                # その他の入力
                sample_input = {input_name: np.random.randn(1, 3, 256, 256)}

            # ウォームアップ
            for _ in range(10):
                model.predict(sample_input)

            # ベンチマーク
            start_time = time.time()
            for _ in range(num_iterations):
                model.predict(sample_input)
            end_time = time.time()

            total_time = end_time - start_time
            avg_time = total_time / num_iterations
            fps = 1.0 / avg_time

            results = {
                "total_time_sec": total_time,
                "avg_time_ms": avg_time * 1000,
                "fps": fps,
                "num_iterations": num_iterations,
            }

            logger.info(f"Benchmark results:")
            logger.info(f"  Average time: {avg_time * 1000:.2f} ms")
            logger.info(f"  FPS: {fps:.1f}")

            return results

        except Exception as e:
            logger.error(f"Failed to benchmark model: {e}")
            return {}

    @staticmethod
    def download_mediapipe_models(output_dir: str = "models") -> bool:
        """
        MediaPipe公式モデルをダウンロード

        Args:
            output_dir: 出力ディレクトリ

        Returns:
            ダウンロード成功時True
        """
        try:
            import urllib.request

            os.makedirs(output_dir, exist_ok=True)

            models = {
                "pose_landmark_full.tflite": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task",
                "face_landmarker.tflite": "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
            }

            for filename, url in models.items():
                output_path = os.path.join(output_dir, filename)
                if os.path.exists(output_path):
                    logger.info(f"Model already exists: {output_path}")
                    continue

                logger.info(f"Downloading {filename}...")
                urllib.request.urlretrieve(url, output_path)
                logger.info(f"Downloaded: {output_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to download models: {e}")
            return False
