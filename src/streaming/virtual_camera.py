"""
Virtual Camera統合モジュール

OBS Virtual Cameraなどに映像を送信します。
"""

import numpy as np
import cv2
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VirtualCamera:
    """
    Virtual Cameraクラス

    pyvirtualcamを使用してOBSなどに映像を送信します。
    """

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        backend: str = "obs",  # "obs" or "unitycapture"
    ):
        """
        Virtual Cameraを初期化

        Args:
            width: 出力映像の幅
            height: 出力映像の高さ
            fps: フレームレート
            backend: バックエンド ("obs" or "unitycapture")
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.backend = backend
        self.camera = None
        self.is_started = False

        logger.info(
            f"VirtualCamera initialized: {width}x{height}@{fps}fps, backend={backend}"
        )

    def start(self) -> bool:
        """
        Virtual Cameraを開始

        Returns:
            開始成功時True
        """
        try:
            import pyvirtualcam

            # Virtual Cameraを開始
            self.camera = pyvirtualcam.Camera(
                width=self.width,
                height=self.height,
                fps=self.fps,
                backend=self.backend,
            )

            self.is_started = True
            logger.info(f"Virtual Camera started: {self.camera.device}")
            return True

        except ImportError:
            logger.error(
                "pyvirtualcam not installed. Install with: pip install pyvirtualcam"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to start Virtual Camera: {e}")
            logger.info(
                "Make sure OBS Virtual Camera is installed on your system:\n"
                "  macOS: Install OBS Studio (https://obsproject.com/)"
            )
            return False

    def stop(self):
        """Virtual Cameraを停止"""
        if self.camera:
            self.camera.close()
            self.camera = None
        self.is_started = False
        logger.info("Virtual Camera stopped")

    def send_frame(self, frame: np.ndarray) -> bool:
        """
        フレームを送信

        Args:
            frame: 送信するフレーム（BGR形式）

        Returns:
            送信成功時True
        """
        if not self.is_started or self.camera is None:
            logger.warning("Virtual Camera not started")
            return False

        try:
            # BGRからRGBに変換
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # リサイズ（必要な場合）
            if frame_rgb.shape[1] != self.width or frame_rgb.shape[0] != self.height:
                frame_rgb = cv2.resize(frame_rgb, (self.width, self.height))

            # フレームを送信
            self.camera.send(frame_rgb)

            return True

        except Exception as e:
            logger.error(f"Failed to send frame: {e}")
            return False

    def wait(self, duration: Optional[float] = None):
        """
        次のフレームまで待機

        Args:
            duration: 待機時間（秒）。Noneの場合はFPSに基づいて自動計算
        """
        if self.camera:
            if duration is None:
                self.camera.sleep_until_next_frame()
            else:
                import time

                time.sleep(duration)

    def __enter__(self):
        """コンテキストマネージャー: 開始"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了"""
        self.stop()
