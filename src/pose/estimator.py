"""
ポーズ推定モジュール

MediaPipe Poseを使用して全身のポーズをリアルタイムで推定します。
"""

import mediapipe as mp
import numpy as np
import cv2
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PoseLandmarks:
    """
    ポーズランドマークデータ

    33個のランドマークポイントと各種情報を保持
    """

    landmarks: np.ndarray  # (33, 4) - x, y, z, visibility
    world_landmarks: Optional[np.ndarray] = None  # (33, 4) - 実世界座標系
    timestamp: float = 0.0
    confidence: float = 0.0

    def get_landmark(self, index: int) -> Tuple[float, float, float, float]:
        """
        指定インデックスのランドマークを取得

        Args:
            index: ランドマークインデックス (0-32)

        Returns:
            (x, y, z, visibility)
        """
        if 0 <= index < len(self.landmarks):
            return tuple(self.landmarks[index])
        return (0.0, 0.0, 0.0, 0.0)

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "landmarks": self.landmarks.tolist(),
            "world_landmarks": (
                self.world_landmarks.tolist()
                if self.world_landmarks is not None
                else None
            ),
            "timestamp": self.timestamp,
            "confidence": self.confidence,
        }


class PoseEstimator:
    """
    ポーズ推定クラス

    MediaPipe Poseを使用して全身のポーズを推定します。
    オプションでCore MLモデルによるNeural Engine最適化が可能です。
    """

    # MediaPipe Poseランドマークの名前マッピング
    LANDMARK_NAMES = [
        "nose",
        "left_eye_inner",
        "left_eye",
        "left_eye_outer",
        "right_eye_inner",
        "right_eye",
        "right_eye_outer",
        "left_ear",
        "right_ear",
        "mouth_left",
        "mouth_right",
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "left_pinky",
        "right_pinky",
        "left_index",
        "right_index",
        "left_thumb",
        "right_thumb",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
        "left_heel",
        "right_heel",
        "left_foot_index",
        "right_foot_index",
    ]

    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        smooth_landmarks: bool = True,
        enable_segmentation: bool = False,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        use_coreml: bool = False,
        coreml_model_path: Optional[str] = None,
    ):
        """
        ポーズ推定器を初期化

        Args:
            static_image_mode: 静止画モード（Falseでビデオモード）
            model_complexity: モデル複雑度 (0=Lite, 1=Full, 2=Heavy)
            smooth_landmarks: ランドマークの平滑化を有効化
            enable_segmentation: セグメンテーション（背景分離）を有効化
            min_detection_confidence: 検出信頼度閾値
            min_tracking_confidence: トラッキング信頼度閾値
            use_coreml: Core MLモデルを使用（Neural Engine最適化）
            coreml_model_path: Core MLモデルのパス
        """
        self.use_coreml = use_coreml
        self.coreml_model_path = coreml_model_path
        self.coreml_model = None

        if use_coreml and coreml_model_path:
            self._load_coreml_model(coreml_model_path)
        else:
            # MediaPipe Poseを初期化
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=static_image_mode,
                model_complexity=model_complexity,
                smooth_landmarks=smooth_landmarks,
                enable_segmentation=enable_segmentation,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )

        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        logger.info(
            f"PoseEstimator initialized: complexity={model_complexity}, "
            f"coreml={use_coreml}"
        )

    def _load_coreml_model(self, model_path: str):
        """Core MLモデルを読み込み"""
        try:
            import coremltools as ct

            self.coreml_model = ct.models.MLModel(model_path)
            logger.info(f"Core ML model loaded: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load Core ML model: {e}")
            logger.info("Falling back to MediaPipe")
            self.use_coreml = False

    def process(self, image: np.ndarray) -> Optional[PoseLandmarks]:
        """
        画像からポーズを推定

        Args:
            image: 入力画像 (BGR形式)

        Returns:
            PoseLandmarksオブジェクト、検出失敗時はNone
        """
        if self.use_coreml and self.coreml_model is not None:
            return self._process_coreml(image)
        else:
            return self._process_mediapipe(image)

    def _process_mediapipe(self, image: np.ndarray) -> Optional[PoseLandmarks]:
        """MediaPipeでポーズ推定"""
        # BGRからRGBに変換
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        # ポーズ推定を実行
        results = self.pose.process(image_rgb)

        image_rgb.flags.writeable = True

        if results.pose_landmarks is None:
            return None

        # ランドマークをNumPy配列に変換
        landmarks = np.array(
            [
                [lm.x, lm.y, lm.z, lm.visibility]
                for lm in results.pose_landmarks.landmark
            ]
        )

        # 世界座標系のランドマーク
        world_landmarks = None
        if results.pose_world_landmarks:
            world_landmarks = np.array(
                [
                    [lm.x, lm.y, lm.z, lm.visibility]
                    for lm in results.pose_world_landmarks.landmark
                ]
            )

        # 信頼度を計算（全ランドマークの可視性の平均）
        confidence = float(np.mean(landmarks[:, 3]))

        return PoseLandmarks(
            landmarks=landmarks,
            world_landmarks=world_landmarks,
            timestamp=0.0,  # TODO: タイムスタンプを実装
            confidence=confidence,
        )

    def _process_coreml(self, image: np.ndarray) -> Optional[PoseLandmarks]:
        """Core MLでポーズ推定（Neural Engine最適化）"""
        try:
            from ..coreml.inference import PoseInference

            # Core ML推論器を初期化（初回のみ）
            if not hasattr(self, '_coreml_inference'):
                self._coreml_inference = PoseInference(self.coreml_model_path)

            # 推論実行
            predictions = self._coreml_inference.predict_from_raw_image(image)

            # ランドマークを抽出
            image_height, image_width = image.shape[:2]
            landmarks = self._coreml_inference.extract_landmarks(
                predictions, image_width, image_height
            )

            if landmarks is None:
                return None

            # 信頼度を計算（全ランドマークの可視性の平均）
            confidence = float(np.mean(landmarks[:, 3]))

            return PoseLandmarks(
                landmarks=landmarks,
                world_landmarks=None,  # Core MLでは世界座標系は未対応
                timestamp=0.0,
                confidence=confidence,
            )

        except Exception as e:
            logger.error(f"Core ML inference failed: {e}")
            logger.info("Falling back to MediaPipe")
            return self._process_mediapipe(image)

    def draw_landmarks(
        self,
        image: np.ndarray,
        pose_landmarks: PoseLandmarks,
        draw_world: bool = False,
    ) -> np.ndarray:
        """
        画像上にランドマークを描画

        Args:
            image: 入力画像
            pose_landmarks: ポーズランドマーク
            draw_world: 世界座標系を描画するか

        Returns:
            描画済み画像
        """
        annotated_image = image.copy()

        # MediaPipe形式に変換して描画
        from mediapipe.framework.formats import landmark_pb2

        landmark_list = landmark_pb2.NormalizedLandmarkList()
        for lm in pose_landmarks.landmarks:
            landmark = landmark_list.landmark.add()
            landmark.x = lm[0]
            landmark.y = lm[1]
            landmark.z = lm[2]
            landmark.visibility = lm[3]

        # ランドマークとコネクションを描画
        self.mp_drawing.draw_landmarks(
            annotated_image,
            landmark_list,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style(),
        )

        return annotated_image

    def get_landmark_by_name(
        self, pose_landmarks: PoseLandmarks, name: str
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        名前でランドマークを取得

        Args:
            pose_landmarks: ポーズランドマーク
            name: ランドマーク名

        Returns:
            (x, y, z, visibility) または None
        """
        try:
            index = self.LANDMARK_NAMES.index(name)
            return pose_landmarks.get_landmark(index)
        except ValueError:
            logger.warning(f"Unknown landmark name: {name}")
            return None

    def close(self):
        """リソースを解放"""
        if hasattr(self, "pose"):
            self.pose.close()

    def __del__(self):
        """デストラクタ"""
        self.close()
