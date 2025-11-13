"""
オーディオキャプチャモジュール

MacのマイクからリアルタイムでAudio入力をキャプチャします。
"""

import sounddevice as sd
import numpy as np
from typing import Optional, Callable, List
import queue
import logging

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    オーディオキャプチャクラス

    macOSのマイクからリアルタイムで音声をキャプチャします。
    """

    def __init__(
        self,
        sample_rate: int = 48000,
        channels: int = 1,
        dtype: str = "float32",
        block_size: int = 2048,
        device: Optional[int] = None,
        latency: str = "low",
    ):
        """
        オーディオキャプチャを初期化

        Args:
            sample_rate: サンプリングレート（Hz）
            channels: チャンネル数（1=モノラル, 2=ステレオ）
            dtype: データ型
            block_size: ブロックサイズ（サンプル数）
            device: デバイスID（Noneでデフォルト）
            latency: レイテンシ設定（"low", "high"）
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.block_size = block_size
        self.device = device
        self.latency = latency

        self.stream: Optional[sd.InputStream] = None
        self.is_recording = False
        self.audio_queue = queue.Queue()

        logger.info(
            f"AudioCapture initialized: {sample_rate}Hz, {channels}ch, "
            f"block={block_size}, latency={latency}"
        )

    @staticmethod
    def list_devices() -> List[dict]:
        """
        利用可能なオーディオデバイスを一覧表示

        Returns:
            デバイス情報のリスト
        """
        devices = sd.query_devices()
        logger.info("Available audio devices:")
        for i, device in enumerate(devices):
            logger.info(f"  [{i}] {device['name']}")
            logger.info(f"      In: {device['max_input_channels']}, "
                       f"Out: {device['max_output_channels']}, "
                       f"SR: {device['default_samplerate']}Hz")
        return devices

    @staticmethod
    def get_default_input_device() -> int:
        """
        デフォルト入力デバイスのIDを取得

        Returns:
            デバイスID
        """
        return sd.default.device[0]

    def start(self, callback: Optional[Callable] = None) -> bool:
        """
        キャプチャを開始

        Args:
            callback: オーディオコールバック関数
                      callback(audio_data: np.ndarray, sample_rate: int)

        Returns:
            開始成功時True
        """
        try:
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio status: {status}")

                # データをキューに追加
                audio_data = indata.copy()
                self.audio_queue.put(audio_data)

                # ユーザーコールバックを呼び出し
                if callback:
                    callback(audio_data, self.sample_rate)

            # ストリームを開始
            self.stream = sd.InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.block_size,
                latency=self.latency,
                callback=audio_callback,
            )

            self.stream.start()
            self.is_recording = True

            device_info = sd.query_devices(self.device or self.get_default_input_device())
            logger.info(f"Audio capture started: {device_info['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            return False

    def stop(self):
        """キャプチャを停止"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.is_recording = False
        logger.info("Audio capture stopped")

    def read(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        キューからオーディオデータを読み取り

        Args:
            timeout: タイムアウト（秒）

        Returns:
            オーディオデータ（サンプル数 x チャンネル数）
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_rms_level(self, audio_data: np.ndarray) -> float:
        """
        RMS（二乗平均平方根）レベルを計算

        Args:
            audio_data: オーディオデータ

        Returns:
            RMSレベル（0.0～1.0）
        """
        return float(np.sqrt(np.mean(audio_data ** 2)))

    def get_peak_level(self, audio_data: np.ndarray) -> float:
        """
        ピークレベルを取得

        Args:
            audio_data: オーディオデータ

        Returns:
            ピークレベル（0.0～1.0）
        """
        return float(np.max(np.abs(audio_data)))

    def __enter__(self):
        """コンテキストマネージャー: 開始"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了"""
        self.stop()

    def __del__(self):
        """デストラクタ"""
        self.stop()
