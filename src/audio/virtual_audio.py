"""
仮想オーディオデバイス出力モジュール

変換した音声を仮想オーディオデバイスに出力します。
"""

import sounddevice as sd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VirtualAudioOutput:
    """
    仮想オーディオ出力クラス

    変換した音声を仮想オーディオデバイス（BlackHole, Soundflowerなど）に出力します。
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
        仮想オーディオ出力を初期化

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

        self.stream: Optional[sd.OutputStream] = None
        self.is_playing = False

        logger.info(
            f"VirtualAudioOutput initialized: {sample_rate}Hz, {channels}ch, "
            f"block={block_size}, latency={latency}"
        )

    @staticmethod
    def find_virtual_device(device_name_contains: str = "BlackHole") -> Optional[int]:
        """
        仮想オーディオデバイスを検索

        Args:
            device_name_contains: デバイス名に含まれる文字列

        Returns:
            デバイスID、見つからない場合None
        """
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if (
                device_name_contains.lower() in device["name"].lower()
                and device["max_output_channels"] > 0
            ):
                logger.info(f"Found virtual device: [{i}] {device['name']}")
                return i

        logger.warning(f"Virtual device containing '{device_name_contains}' not found")
        return None

    @staticmethod
    def list_output_devices():
        """出力可能なオーディオデバイスを一覧表示"""
        devices = sd.query_devices()
        logger.info("Available output devices:")
        for i, device in enumerate(devices):
            if device["max_output_channels"] > 0:
                logger.info(
                    f"  [{i}] {device['name']} "
                    f"(Out: {device['max_output_channels']}, "
                    f"SR: {device['default_samplerate']}Hz)"
                )

    def start(self) -> bool:
        """
        出力を開始

        Returns:
            開始成功時True
        """
        try:
            self.stream = sd.OutputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.block_size,
                latency=self.latency,
            )

            self.stream.start()
            self.is_playing = True

            device_info = sd.query_devices(
                self.device or sd.default.device[1]
            )
            logger.info(f"Audio output started: {device_info['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to start audio output: {e}")
            return False

    def stop(self):
        """出力を停止"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.is_playing = False
        logger.info("Audio output stopped")

    def write(self, audio_data: np.ndarray):
        """
        オーディオデータを出力

        Args:
            audio_data: 出力するオーディオデータ
        """
        if not self.is_playing or self.stream is None:
            logger.warning("Audio output not started")
            return

        try:
            self.stream.write(audio_data)
        except Exception as e:
            logger.error(f"Failed to write audio: {e}")

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


class AudioLoopback:
    """
    オーディオループバッククラス

    入力を変換して出力にリアルタイム送信します。
    """

    def __init__(
        self,
        input_device: Optional[int] = None,
        output_device: Optional[int] = None,
        sample_rate: int = 48000,
        channels: int = 1,
        block_size: int = 2048,
        converter=None,
    ):
        """
        オーディオループバックを初期化

        Args:
            input_device: 入力デバイスID
            output_device: 出力デバイスID
            sample_rate: サンプリングレート
            channels: チャンネル数
            block_size: ブロックサイズ
            converter: 声質変換器（VoiceConverterインスタンス）
        """
        self.input_device = input_device
        self.output_device = output_device
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_size = block_size
        self.converter = converter

        self.stream: Optional[sd.Stream] = None
        self.is_running = False

        logger.info(
            f"AudioLoopback initialized: {sample_rate}Hz, {channels}ch, "
            f"block={block_size}"
        )

    def start(self) -> bool:
        """
        ループバックを開始

        Returns:
            開始成功時True
        """
        try:

            def callback(indata, outdata, frames, time, status):
                if status:
                    logger.warning(f"Audio status: {status}")

                # 入力データをコピー
                audio = indata[:, 0] if indata.shape[1] > 1 else indata.flatten()

                # 声質変換を適用
                if self.converter:
                    try:
                        converted = self.converter.convert(audio)
                        # 長さを揃える
                        if len(converted) < frames:
                            converted = np.pad(
                                converted, (0, frames - len(converted))
                            )
                        elif len(converted) > frames:
                            converted = converted[:frames]
                        audio = converted
                    except Exception as e:
                        logger.error(f"Conversion failed: {e}")

                # 出力にコピー
                if self.channels == 1:
                    outdata[:] = audio.reshape(-1, 1)
                else:
                    outdata[:] = np.tile(audio.reshape(-1, 1), (1, self.channels))

            # 双方向ストリームを開始
            self.stream = sd.Stream(
                device=(self.input_device, self.output_device),
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                dtype="float32",
                latency="low",
                channels=(1, self.channels),
                callback=callback,
            )

            self.stream.start()
            self.is_running = True

            in_dev = sd.query_devices(self.input_device or sd.default.device[0])
            out_dev = sd.query_devices(self.output_device or sd.default.device[1])
            logger.info(
                f"Audio loopback started: {in_dev['name']} -> {out_dev['name']}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start audio loopback: {e}")
            return False

    def stop(self):
        """ループバックを停止"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.is_running = False
        logger.info("Audio loopback stopped")

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
