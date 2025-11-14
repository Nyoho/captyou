"""
Core ML変換・モデル管理モジュール

MediaPipeモデルをダウンロードし、Core MLに変換してNeural Engineで最適化します。
"""

import coremltools as ct
import numpy as np
from typing import Optional, Tuple, Dict
import logging
import os
import urllib.request
import zipfile
import shutil

logger = logging.getLogger(__name__)


class MediaPipeModelManager:
    """
    MediaPipeモデルマネージャー

    公式モデルのダウンロードと管理を行います。
    """

    # MediaPipe公式モデルのURL
    MODELS = {
        "pose_landmarker": {
            "url": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
            "filename": "pose_landmarker_lite.task",
            "type": "pose",
        },
        "pose_landmarker_full": {
            "url": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task",
            "filename": "pose_landmarker_full.task",
            "type": "pose",
        },
        "pose_landmarker_heavy": {
            "url": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task",
            "filename": "pose_landmarker_heavy.task",
            "type": "pose",
        },
        "face_landmarker": {
            "url": "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
            "filename": "face_landmarker.task",
            "type": "face",
        },
    }

    @staticmethod
    def download_model(model_name: str, output_dir: str = "models") -> str:
        """
        MediaPipe公式モデルをダウンロード

        Args:
            model_name: モデル名（"pose_landmarker", "face_landmarker"など）
            output_dir: 出力ディレクトリ

        Returns:
            ダウンロードしたファイルのパス
        """
        if model_name not in MediaPipeModelManager.MODELS:
            raise ValueError(f"Unknown model: {model_name}")

        model_info = MediaPipeModelManager.MODELS[model_name]
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, model_info["filename"])

        if os.path.exists(output_path):
            logger.info(f"Model already exists: {output_path}")
            return output_path

        logger.info(f"Downloading {model_name} from {model_info['url']}")

        try:
            urllib.request.urlretrieve(model_info["url"], output_path)
            logger.info(f"Downloaded: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise

    @staticmethod
    def extract_tflite_from_task(task_path: str, output_dir: Optional[str] = None) -> str:
        """
        .taskファイルからTFLiteモデルを抽出

        MediaPipeの.taskファイルは実際にはZIPアーカイブです。

        Args:
            task_path: .taskファイルのパス
            output_dir: 出力ディレクトリ（Noneの場合は.taskと同じディレクトリ）

        Returns:
            抽出されたTFLiteモデルのパス
        """
        if output_dir is None:
            output_dir = os.path.dirname(task_path)

        # .taskファイルをZIPとして展開
        extract_dir = os.path.join(output_dir, "extracted_" + os.path.basename(task_path))

        try:
            with zipfile.ZipFile(task_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # TFLiteファイルを探す
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.tflite'):
                        tflite_path = os.path.join(root, file)

                        # わかりやすい名前にリネーム
                        task_basename = os.path.splitext(os.path.basename(task_path))[0]
                        new_path = os.path.join(output_dir, f"{task_basename}.tflite")
                        shutil.copy(tflite_path, new_path)

                        # 展開ディレクトリを削除
                        shutil.rmtree(extract_dir)

                        logger.info(f"Extracted TFLite model: {new_path}")
                        return new_path

            raise FileNotFoundError("No TFLite model found in .task file")

        except Exception as e:
            logger.error(f"Failed to extract TFLite model: {e}")
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            raise


class CoreMLConverter:
    """
    Core ML変換クラス

    TFLiteモデルをCore MLに変換し、Apple Neural Engineで高速実行できるようにします。
    """

    @staticmethod
    def convert_tflite_to_coreml(
        tflite_path: str,
        output_path: str,
        model_type: str = "pose",
        compute_units: ct.ComputeUnit = ct.ComputeUnit.ALL,
    ) -> bool:
        """
        TFLiteモデルをCore MLに変換

        Args:
            tflite_path: TFLiteモデルのパス
            output_path: 出力するCore MLモデルパス
            model_type: モデルタイプ（"pose" or "face"）
            compute_units: 計算ユニット（ALL=CPU+GPU+ANE）

        Returns:
            変換成功時True
        """
        try:
            logger.info(f"Converting TFLite model: {tflite_path}")
            logger.info(f"Output: {output_path}")
            logger.info(f"Compute units: {compute_units}")

            # TFLiteモデルを読み込み
            model = ct.convert(
                tflite_path,
                source="tensorflow",
                compute_units=compute_units,
                minimum_deployment_target=ct.target.macOS13,
                convert_to="neuralnetwork",  # Neural Engine対応
            )

            # メタデータを追加
            model.author = "CaptyOU (MediaPipe)"
            model.short_description = f"{model_type.capitalize()} landmarker optimized for Neural Engine"
            model.version = "1.0"
            model.license = "Apache 2.0 (MediaPipe)"

            # 保存
            model.save(output_path)
            logger.info(f"Model saved: {output_path}")

            # モデル情報を表示
            spec = model.get_spec()
            logger.info(f"Model inputs: {[i.name for i in spec.description.input]}")
            logger.info(f"Model outputs: {[o.name for i in spec.description.output]}")

            # ファイルサイズを表示
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"Model size: {size_mb:.2f} MB")

            return True

        except Exception as e:
            logger.error(f"Failed to convert model: {e}")
            logger.info("Note: TFLite -> Core ML conversion may require specific TensorFlow versions")
            return False

    @staticmethod
    def optimize_coreml_model(
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
                # 16bit float量子化でモデルサイズを削減
                logger.info("Quantizing weights to float16")

                # 量子化を実行
                from coremltools.models.neural_network import quantization_utils

                spec = model.get_spec()
                quantized_spec = quantization_utils.quantize_weights(spec, nbits=16)

                # 新しいモデルを作成
                model = ct.models.MLModel(quantized_spec)

            # 保存
            if output_path is None:
                output_path = mlmodel_path

            model.save(output_path)
            logger.info(f"Optimized model saved: {output_path}")

            # ファイルサイズを表示
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"Optimized model size: {size_mb:.2f} MB")

            return True

        except Exception as e:
            logger.error(f"Failed to optimize model: {e}")
            return False

    @staticmethod
    def benchmark_model(mlmodel_path: str, num_iterations: int = 100) -> Dict[str, float]:
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

            # 入力サイズを取得
            input_type = spec.description.input[0].type
            if input_type.HasField("multiArrayType"):
                shape = input_type.multiArrayType.shape
                sample_input = {input_name: np.random.randn(*shape).astype(np.float32)}
            elif input_type.HasField("imageType"):
                width = input_type.imageType.width
                height = input_type.imageType.height
                from PIL import Image
                sample_image = Image.new("RGB", (width, height))
                sample_input = {input_name: sample_image}
            else:
                logger.warning("Unknown input type")
                return {}

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


def setup_models(models_dir: str = "models") -> Dict[str, str]:
    """
    MediaPipeモデルをダウンロードしてCore MLに変換

    Args:
        models_dir: モデルディレクトリ

    Returns:
        変換されたCore MLモデルのパス辞書
    """
    os.makedirs(models_dir, exist_ok=True)
    converted_models = {}

    logger.info("Setting up models for Neural Engine...")

    # ポーズモデル（Full版を使用）
    try:
        logger.info("\n=== Pose Model ===")
        task_path = MediaPipeModelManager.download_model("pose_landmarker_full", models_dir)
        tflite_path = MediaPipeModelManager.extract_tflite_from_task(task_path, models_dir)
        coreml_path = os.path.join(models_dir, "pose_landmarker.mlmodel")

        if CoreMLConverter.convert_tflite_to_coreml(
            tflite_path, coreml_path, model_type="pose"
        ):
            converted_models["pose"] = coreml_path
            logger.info(f"✓ Pose model ready: {coreml_path}")
    except Exception as e:
        logger.error(f"Failed to setup pose model: {e}")

    # 表情モデル
    try:
        logger.info("\n=== Face Model ===")
        task_path = MediaPipeModelManager.download_model("face_landmarker", models_dir)
        tflite_path = MediaPipeModelManager.extract_tflite_from_task(task_path, models_dir)
        coreml_path = os.path.join(models_dir, "face_landmarker.mlmodel")

        if CoreMLConverter.convert_tflite_to_coreml(
            tflite_path, coreml_path, model_type="face"
        ):
            converted_models["face"] = coreml_path
            logger.info(f"✓ Face model ready: {coreml_path}")
    except Exception as e:
        logger.error(f"Failed to setup face model: {e}")

    return converted_models
