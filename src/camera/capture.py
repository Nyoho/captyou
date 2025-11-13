"""
カメラキャプチャモジュール

MacBook Proの内蔵カメラからリアルタイムで映像をキャプチャします。
OpenCVベースの基本実装と、macOS AVFoundation最適化版を提供します。
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Generator
import platform
import logging

logger = logging.getLogger(__name__)


class CameraCapture:
    """
    カメラキャプチャクラス

    MacBook Proの内蔵カメラから映像をキャプチャします。
    """

    def __init__(
        self,
        camera_id: int = 0,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        use_macos_optimization: bool = True,
    ):
        """
        カメラキャプチャを初期化

        Args:
            camera_id: カメラデバイスID（通常は0が内蔵カメラ）
            width: キャプチャ幅
            height: キャプチャ高さ
            fps: フレームレート
            use_macos_optimization: macOS最適化を使用するか
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.use_macos_optimization = use_macos_optimization and self._is_macos()

        self.cap: Optional[cv2.VideoCapture] = None
        self._is_opened = False

        logger.info(
            f"CameraCapture initialized: {width}x{height}@{fps}fps, "
            f"macOS optimization: {self.use_macos_optimization}"
        )

    def _is_macos(self) -> bool:
        """macOSかどうかを判定"""
        return platform.system() == "Darwin"

    def open(self) -> bool:
        """
        カメラを開く

        Returns:
            成功した場合True
        """
        try:
            # macOS最適化: AVFoundationバックエンドを使用
            if self.use_macos_optimization:
                self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_AVFOUNDATION)
            else:
                self.cap = cv2.VideoCapture(self.camera_id)

            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_id}")
                return False

            # カメラ設定
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            # macOS最適化: 追加設定
            if self.use_macos_optimization:
                # バッファリングを最小化してレイテンシを削減
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                # H.264ハードウェアデコードを有効化
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"H264"))

            # 実際の設定値を取得
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

            logger.info(
                f"Camera opened: {actual_width}x{actual_height}@{actual_fps}fps"
            )

            self._is_opened = True
            return True

        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            return False

    def close(self):
        """カメラを閉じる"""
        if self.cap is not None:
            self.cap.release()
            self._is_opened = False
            logger.info("Camera closed")

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        1フレームを読み取る

        Returns:
            (成功フラグ, フレーム画像)
        """
        if not self._is_opened or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        return ret, frame if ret else None

    def capture(self) -> Generator[np.ndarray, None, None]:
        """
        フレームをジェネレータとして連続取得

        Yields:
            フレーム画像
        """
        if not self._is_opened:
            if not self.open():
                raise RuntimeError("Failed to open camera")

        try:
            while True:
                ret, frame = self.read()
                if not ret or frame is None:
                    logger.warning("Failed to read frame")
                    break
                yield frame
        finally:
            self.close()

    def get_frame_size(self) -> Tuple[int, int]:
        """
        フレームサイズを取得

        Returns:
            (width, height)
        """
        if self.cap is not None:
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return width, height
        return self.width, self.height

    def get_fps(self) -> int:
        """
        FPSを取得

        Returns:
            FPS
        """
        if self.cap is not None:
            return int(self.cap.get(cv2.CAP_PROP_FPS))
        return self.fps

    def __enter__(self):
        """コンテキストマネージャー: 開始"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了"""
        self.close()

    def __del__(self):
        """デストラクタ"""
        self.close()
