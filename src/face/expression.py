"""
表情認識モジュール

MediaPipe Face Meshを使用して顔のランドマークと表情をリアルタイムで認識します。
"""

import mediapipe as mp
import numpy as np
import cv2
from typing import Optional, Dict, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class BlendShapes:
    """
    ARKit互換のブレンドシェイプ（表情パラメータ）

    52種類の表情パラメータを0.0～1.0の範囲で保持
    """

    # 目
    eye_blink_left: float = 0.0
    eye_blink_right: float = 0.0
    eye_look_down_left: float = 0.0
    eye_look_down_right: float = 0.0
    eye_look_in_left: float = 0.0
    eye_look_in_right: float = 0.0
    eye_look_out_left: float = 0.0
    eye_look_out_right: float = 0.0
    eye_look_up_left: float = 0.0
    eye_look_up_right: float = 0.0
    eye_squint_left: float = 0.0
    eye_squint_right: float = 0.0
    eye_wide_left: float = 0.0
    eye_wide_right: float = 0.0

    # 眉
    brow_down_left: float = 0.0
    brow_down_right: float = 0.0
    brow_inner_up: float = 0.0
    brow_outer_up_left: float = 0.0
    brow_outer_up_right: float = 0.0

    # 口
    mouth_close: float = 0.0
    mouth_funnel: float = 0.0
    mouth_pucker: float = 0.0
    mouth_left: float = 0.0
    mouth_right: float = 0.0
    mouth_smile_left: float = 0.0
    mouth_smile_right: float = 0.0
    mouth_frown_left: float = 0.0
    mouth_frown_right: float = 0.0
    mouth_dimple_left: float = 0.0
    mouth_dimple_right: float = 0.0
    mouth_stretch_left: float = 0.0
    mouth_stretch_right: float = 0.0
    mouth_roll_lower: float = 0.0
    mouth_roll_upper: float = 0.0
    mouth_shrug_lower: float = 0.0
    mouth_shrug_upper: float = 0.0
    mouth_press_left: float = 0.0
    mouth_press_right: float = 0.0
    mouth_lower_down_left: float = 0.0
    mouth_lower_down_right: float = 0.0
    mouth_upper_up_left: float = 0.0
    mouth_upper_up_right: float = 0.0

    # 頬
    cheek_puff: float = 0.0
    cheek_squint_left: float = 0.0
    cheek_squint_right: float = 0.0

    # 顎
    jaw_open: float = 0.0
    jaw_forward: float = 0.0
    jaw_left: float = 0.0
    jaw_right: float = 0.0

    # 鼻
    nose_sneer_left: float = 0.0
    nose_sneer_right: float = 0.0

    # 舌
    tongue_out: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """辞書形式に変換"""
        return {k: v for k, v in self.__dict__.items() if isinstance(v, float)}


@dataclass
class FaceLandmarks:
    """
    顔のランドマークデータ

    468個のランドマークポイントと表情パラメータを保持
    """

    landmarks: np.ndarray  # (468, 3) - x, y, z
    blend_shapes: BlendShapes = field(default_factory=BlendShapes)
    timestamp: float = 0.0
    confidence: float = 0.0

    def get_landmark(self, index: int) -> Optional[np.ndarray]:
        """
        指定インデックスのランドマークを取得

        Args:
            index: ランドマークインデックス (0-467)

        Returns:
            (x, y, z) または None
        """
        if 0 <= index < len(self.landmarks):
            return self.landmarks[index]
        return None

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "landmarks": self.landmarks.tolist(),
            "blend_shapes": self.blend_shapes.to_dict(),
            "timestamp": self.timestamp,
            "confidence": self.confidence,
        }


class FaceExpression:
    """
    表情認識クラス

    MediaPipe Face Meshを使用して顔のランドマークと表情を認識します。
    ARKit互換のブレンドシェイプを出力します。
    """

    def __init__(
        self,
        static_image_mode: bool = False,
        max_num_faces: int = 1,
        refine_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        use_coreml: bool = False,
        coreml_model_path: Optional[str] = None,
    ):
        """
        表情認識器を初期化

        Args:
            static_image_mode: 静止画モード（Falseでビデオモード）
            max_num_faces: 最大検出顔数
            refine_landmarks: アイリス周辺のランドマークを精密化
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
            # MediaPipe Face Meshを初期化
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=static_image_mode,
                max_num_faces=max_num_faces,
                refine_landmarks=refine_landmarks,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )

        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        logger.info(
            f"FaceExpression initialized: max_faces={max_num_faces}, "
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

    def process(self, image: np.ndarray) -> Optional[FaceLandmarks]:
        """
        画像から顔のランドマークと表情を認識

        Args:
            image: 入力画像 (BGR形式)

        Returns:
            FaceLandmarksオブジェクト、検出失敗時はNone
        """
        if self.use_coreml and self.coreml_model is not None:
            return self._process_coreml(image)
        else:
            return self._process_mediapipe(image)

    def _process_mediapipe(self, image: np.ndarray) -> Optional[FaceLandmarks]:
        """MediaPipeで表情認識"""
        # BGRからRGBに変換
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        # 顔認識を実行
        results = self.face_mesh.process(image_rgb)

        image_rgb.flags.writeable = True

        if not results.multi_face_landmarks:
            return None

        # 最初の顔のランドマークを使用
        face_landmarks = results.multi_face_landmarks[0]

        # ランドマークをNumPy配列に変換
        landmarks = np.array([[lm.x, lm.y, lm.z] for lm in face_landmarks.landmark])

        # ブレンドシェイプを計算
        blend_shapes = self._calculate_blend_shapes(landmarks)

        return FaceLandmarks(
            landmarks=landmarks,
            blend_shapes=blend_shapes,
            timestamp=0.0,  # TODO: タイムスタンプを実装
            confidence=1.0,  # MediaPipeは信頼度を直接提供しない
        )

    def _calculate_blend_shapes(self, landmarks: np.ndarray) -> BlendShapes:
        """
        ランドマークからブレンドシェイプ（表情パラメータ）を計算

        簡易的な実装：主要な表情のみ計算
        より高度な実装には機械学習モデルが必要
        """
        blend_shapes = BlendShapes()

        # 目の開閉度を計算
        # 左目
        left_eye_top = landmarks[159]  # 上まぶた
        left_eye_bottom = landmarks[145]  # 下まぶた
        left_eye_height = np.linalg.norm(left_eye_top - left_eye_bottom)
        blend_shapes.eye_blink_left = max(0.0, 1.0 - left_eye_height * 30)

        # 右目
        right_eye_top = landmarks[386]
        right_eye_bottom = landmarks[374]
        right_eye_height = np.linalg.norm(right_eye_top - right_eye_bottom)
        blend_shapes.eye_blink_right = max(0.0, 1.0 - right_eye_height * 30)

        # 口の開き度を計算
        mouth_top = landmarks[13]  # 上唇
        mouth_bottom = landmarks[14]  # 下唇
        mouth_height = np.linalg.norm(mouth_top - mouth_bottom)
        blend_shapes.jaw_open = min(1.0, mouth_height * 10)

        # 笑顔を計算（口角の高さ）
        mouth_left = landmarks[61]
        mouth_right = landmarks[291]
        mouth_center = landmarks[13]

        left_smile = mouth_left[1] - mouth_center[1]
        right_smile = mouth_right[1] - mouth_center[1]

        blend_shapes.mouth_smile_left = max(0.0, min(1.0, -left_smile * 20))
        blend_shapes.mouth_smile_right = max(0.0, min(1.0, -right_smile * 20))

        # 眉の動きを計算
        left_brow = landmarks[70]
        left_eye_ref = landmarks[159]
        brow_left_dist = left_brow[1] - left_eye_ref[1]

        right_brow = landmarks[300]
        right_eye_ref = landmarks[386]
        brow_right_dist = right_brow[1] - right_eye_ref[1]

        # 眉を上げる
        if brow_left_dist < -0.03:
            blend_shapes.brow_outer_up_left = min(1.0, abs(brow_left_dist) * 20)
        if brow_right_dist < -0.03:
            blend_shapes.brow_outer_up_right = min(1.0, abs(brow_right_dist) * 20)

        return blend_shapes

    def _process_coreml(self, image: np.ndarray) -> Optional[FaceLandmarks]:
        """Core MLで表情認識（Neural Engine最適化）"""
        # TODO: Core ML実装
        logger.warning("Core ML processing not yet implemented, using MediaPipe")
        return self._process_mediapipe(image)

    def draw_landmarks(
        self, image: np.ndarray, face_landmarks: FaceLandmarks
    ) -> np.ndarray:
        """
        画像上にランドマークを描画

        Args:
            image: 入力画像
            face_landmarks: 顔ランドマーク

        Returns:
            描画済み画像
        """
        annotated_image = image.copy()

        # MediaPipe形式に変換して描画
        from mediapipe.framework.formats import landmark_pb2

        landmark_list = landmark_pb2.NormalizedLandmarkList()
        for lm in face_landmarks.landmarks:
            landmark = landmark_list.landmark.add()
            landmark.x = lm[0]
            landmark.y = lm[1]
            landmark.z = lm[2]

        # ランドマークを描画（顔の輪郭のみ）
        self.mp_drawing.draw_landmarks(
            image=annotated_image,
            landmark_list=landmark_list,
            connections=self.mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style(),
        )

        # 虹彩を描画（refine_landmarks=Trueの場合）
        if len(face_landmarks.landmarks) > 468:
            self.mp_drawing.draw_landmarks(
                image=annotated_image,
                landmark_list=landmark_list,
                connections=self.mp_face_mesh.FACEMESH_IRISES,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_iris_connections_style(),
            )

        return annotated_image

    def close(self):
        """リソースを解放"""
        if hasattr(self, "face_mesh"):
            self.face_mesh.close()

    def __del__(self):
        """デストラクタ"""
        self.close()
