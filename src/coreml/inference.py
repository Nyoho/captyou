"""
Core ML推論ヘルパーモジュール

MediaPipeモデルのCore ML版で推論を実行します。
"""

import coremltools as ct
import numpy as np
import cv2
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CoreMLInference:
    """
    Core ML推論ヘルパークラス

    MediaPipeモデルのCore ML版で推論を実行します。
    """

    def __init__(self, model_path: str):
        """
        Core ML推論を初期化

        Args:
            model_path: Core MLモデルのパス
        """
        self.model_path = model_path
        self.model = None
        self.input_name = None
        self.output_names = []
        self.input_shape = None

        self._load_model()

    def _load_model(self):
        """モデルを読み込み"""
        try:
            logger.info(f"Loading Core ML model: {self.model_path}")
            self.model = ct.models.MLModel(self.model_path)

            # モデル情報を取得
            spec = self.model.get_spec()
            self.input_name = spec.description.input[0].name
            self.output_names = [output.name for output in spec.description.output]

            # 入力形状を取得
            input_type = spec.description.input[0].type
            if input_type.HasField("multiArrayType"):
                self.input_shape = tuple(input_type.multiArrayType.shape)
            elif input_type.HasField("imageType"):
                width = input_type.imageType.width
                height = input_type.imageType.height
                self.input_shape = (height, width, 3)

            logger.info(f"Model loaded successfully")
            logger.info(f"  Input: {self.input_name} {self.input_shape}")
            logger.info(f"  Outputs: {self.output_names}")

        except Exception as e:
            logger.error(f"Failed to load Core ML model: {e}")
            raise

    def preprocess_image(self, image: np.ndarray, target_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """
        画像を前処理

        Args:
            image: 入力画像（BGR形式）
            target_size: ターゲットサイズ（width, height）、Noneの場合はモデルのサイズ

        Returns:
            前処理済み画像
        """
        # BGRからRGBに変換
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # リサイズ
        if target_size is None and self.input_shape:
            target_size = (self.input_shape[1], self.input_shape[0])  # (width, height)

        if target_size:
            image_rgb = cv2.resize(image_rgb, target_size)

        # 正規化（0-255 → 0-1）
        image_normalized = image_rgb.astype(np.float32) / 255.0

        return image_normalized

    def predict(self, image: np.ndarray) -> dict:
        """
        推論を実行

        Args:
            image: 入力画像（前処理済み）

        Returns:
            推論結果の辞書
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        try:
            # 入力を準備
            input_dict = {self.input_name: image}

            # 推論実行
            predictions = self.model.predict(input_dict)

            return predictions

        except Exception as e:
            logger.error(f"Inference failed: {e}")
            raise

    def predict_from_raw_image(self, image: np.ndarray) -> dict:
        """
        生の画像から推論を実行（前処理を含む）

        Args:
            image: 入力画像（BGR形式）

        Returns:
            推論結果の辞書
        """
        # 前処理
        processed_image = self.preprocess_image(image)

        # 推論
        return self.predict(processed_image)


class PoseInference(CoreMLInference):
    """
    ポーズ推定用Core ML推論クラス
    """

    def extract_landmarks(self, predictions: dict, image_width: int, image_height: int) -> Optional[np.ndarray]:
        """
        推論結果からランドマークを抽出

        Args:
            predictions: 推論結果
            image_width: 元画像の幅
            image_height: 元画像の高さ

        Returns:
            ランドマーク配列 (33, 4) - x, y, z, visibility
        """
        try:
            # 出力からランドマークを取得
            # MediaPipeモデルの出力形式に応じて調整が必要
            # 通常は 'output' または 'Identity' という名前の出力

            for output_name in self.output_names:
                if output_name in predictions:
                    landmarks_raw = predictions[output_name]

                    # NumPy配列に変換
                    if not isinstance(landmarks_raw, np.ndarray):
                        landmarks_raw = np.array(landmarks_raw)

                    # ランドマーク形式に変換
                    # MediaPipeは通常 (1, 33, 5) の形式
                    # x, y, z, visibility, presence
                    if landmarks_raw.ndim == 3 and landmarks_raw.shape[0] == 1:
                        landmarks_raw = landmarks_raw[0]  # (33, 5)

                    # x, y, z, visibility のみ取得
                    if landmarks_raw.shape[1] >= 4:
                        landmarks = landmarks_raw[:, :4]  # (33, 4)

                        # 座標を正規化（0-1 → pixel）
                        landmarks[:, 0] *= image_width
                        landmarks[:, 1] *= image_height

                        return landmarks

            logger.warning("No valid landmark output found")
            return None

        except Exception as e:
            logger.error(f"Failed to extract landmarks: {e}")
            return None


class FaceInference(CoreMLInference):
    """
    顔認識用Core ML推論クラス
    """

    def extract_landmarks(self, predictions: dict, image_width: int, image_height: int) -> Optional[np.ndarray]:
        """
        推論結果からランドマークを抽出

        Args:
            predictions: 推論結果
            image_width: 元画像の幅
            image_height: 元画像の高さ

        Returns:
            ランドマーク配列 (468, 3) - x, y, z
        """
        try:
            # 出力からランドマークを取得
            for output_name in self.output_names:
                if output_name in predictions:
                    landmarks_raw = predictions[output_name]

                    # NumPy配列に変換
                    if not isinstance(landmarks_raw, np.ndarray):
                        landmarks_raw = np.array(landmarks_raw)

                    # ランドマーク形式に変換
                    # MediaPipe Face Meshは (1, 468, 3) の形式
                    if landmarks_raw.ndim == 3 and landmarks_raw.shape[0] == 1:
                        landmarks_raw = landmarks_raw[0]  # (468, 3)

                    if landmarks_raw.shape[0] == 468:
                        landmarks = landmarks_raw[:, :3]  # (468, 3)

                        # 座標を正規化（0-1 → pixel）
                        landmarks[:, 0] *= image_width
                        landmarks[:, 1] *= image_height

                        return landmarks

            logger.warning("No valid face landmark output found")
            return None

        except Exception as e:
            logger.error(f"Failed to extract face landmarks: {e}")
            return None
