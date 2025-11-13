"""
声質変換モジュール

リアルタイムで男性の声を女性の声に変換します。
ピッチシフト、フォルマントシフト、深層学習ベースの変換をサポートします。
"""

import numpy as np
import librosa
import pyworld as pw
from scipy import signal
from enum import Enum
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ConversionMode(Enum):
    """声質変換モード"""
    PITCH_SHIFT = "pitch_shift"  # ピッチシフトのみ
    FORMANT_SHIFT = "formant_shift"  # フォルマントシフト
    WORLD_VOCODER = "world_vocoder"  # WORLD Vocoderベース（高品質）
    DEEP_LEARNING = "deep_learning"  # 深層学習ベース（要モデル）


class VoiceConverter:
    """
    声質変換クラス

    男性の声を女性の声にリアルタイム変換します。
    """

    def __init__(
        self,
        sample_rate: int = 48000,
        mode: ConversionMode = ConversionMode.WORLD_VOCODER,
        pitch_shift_semitones: float = 5.0,
        formant_shift: float = 1.2,
        use_coreml: bool = False,
        coreml_model_path: Optional[str] = None,
    ):
        """
        声質変換器を初期化

        Args:
            sample_rate: サンプリングレート（Hz）
            mode: 変換モード
            pitch_shift_semitones: ピッチシフト量（半音）
            formant_shift: フォルマントシフト率（1.0=変更なし、>1.0=高く）
            use_coreml: Core MLモデルを使用（Neural Engine最適化）
            coreml_model_path: Core MLモデルのパス
        """
        self.sample_rate = sample_rate
        self.mode = mode
        self.pitch_shift_semitones = pitch_shift_semitones
        self.formant_shift = formant_shift
        self.use_coreml = use_coreml
        self.coreml_model_path = coreml_model_path
        self.coreml_model = None

        # WORLD Vocoder パラメータ
        self.frame_period = 5.0  # ms

        if use_coreml and coreml_model_path:
            self._load_coreml_model(coreml_model_path)

        logger.info(
            f"VoiceConverter initialized: mode={mode.value}, "
            f"pitch_shift={pitch_shift_semitones}st, "
            f"formant_shift={formant_shift}, coreml={use_coreml}"
        )

    def _load_coreml_model(self, model_path: str):
        """Core MLモデルを読み込み"""
        try:
            import coremltools as ct
            self.coreml_model = ct.models.MLModel(model_path)
            logger.info(f"Core ML model loaded: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load Core ML model: {e}")
            self.use_coreml = False

    def convert(self, audio: np.ndarray) -> np.ndarray:
        """
        音声を変換

        Args:
            audio: 入力音声（1次元配列）

        Returns:
            変換された音声
        """
        if self.use_coreml and self.coreml_model is not None:
            return self._convert_coreml(audio)

        if self.mode == ConversionMode.PITCH_SHIFT:
            return self._pitch_shift(audio)
        elif self.mode == ConversionMode.FORMANT_SHIFT:
            return self._formant_shift(audio)
        elif self.mode == ConversionMode.WORLD_VOCODER:
            return self._world_vocoder(audio)
        else:
            logger.warning(f"Unknown mode: {self.mode}, using pitch shift")
            return self._pitch_shift(audio)

    def _pitch_shift(self, audio: np.ndarray) -> np.ndarray:
        """
        ピッチシフト（単純だが高速）

        Args:
            audio: 入力音声

        Returns:
            変換された音声
        """
        try:
            # librosaのピッチシフト
            shifted = librosa.effects.pitch_shift(
                audio,
                sr=self.sample_rate,
                n_steps=self.pitch_shift_semitones,
            )
            return shifted
        except Exception as e:
            logger.error(f"Pitch shift failed: {e}")
            return audio

    def _formant_shift(self, audio: np.ndarray) -> np.ndarray:
        """
        フォルマントシフト（より自然）

        Args:
            audio: 入力音声

        Returns:
            変換された音声
        """
        try:
            # リサンプリングによるフォルマントシフト
            # 音声を高速再生してからピッチを下げる

            # 1. フォルマントシフト: リサンプリング
            formant_shifted_len = int(len(audio) / self.formant_shift)
            formant_shifted = signal.resample(audio, formant_shifted_len)

            # 2. ピッチシフト: 元の高さに戻す
            pitch_shifted = librosa.effects.pitch_shift(
                formant_shifted,
                sr=self.sample_rate,
                n_steps=self.pitch_shift_semitones,
            )

            return pitch_shifted
        except Exception as e:
            logger.error(f"Formant shift failed: {e}")
            return audio

    def _world_vocoder(self, audio: np.ndarray) -> np.ndarray:
        """
        WORLD Vocoderベースの声質変換（高品質）

        Args:
            audio: 入力音声

        Returns:
            変換された音声
        """
        try:
            # float64に変換（WORLDの要件）
            audio_float = audio.astype(np.float64)

            # 1. 音響特徴量を抽出
            f0, sp, ap = self._extract_world_features(audio_float)

            # 2. F0（基本周波数）をシフト
            f0_shifted = self._shift_f0(f0)

            # 3. スペクトル包絡をシフト（フォルマント変更）
            sp_shifted = self._shift_spectrum(sp)

            # 4. 音声を再合成
            synthesized = pw.synthesize(
                f0_shifted,
                sp_shifted,
                ap,
                self.sample_rate,
                self.frame_period,
            )

            # float32に戻す
            return synthesized.astype(np.float32)

        except Exception as e:
            logger.error(f"WORLD vocoder failed: {e}")
            return audio

    def _extract_world_features(
        self, audio: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        WORLDで音響特徴量を抽出

        Args:
            audio: 入力音声（float64）

        Returns:
            (f0, sp, ap) - 基本周波数、スペクトル包絡、非周期性指標
        """
        # DIOアルゴリズムでF0推定
        f0, time_axis = pw.dio(
            audio,
            self.sample_rate,
            frame_period=self.frame_period,
        )

        # F0の精密化
        f0 = pw.stonemask(audio, f0, time_axis, self.sample_rate)

        # スペクトル包絡の推定
        sp = pw.cheaptrick(audio, f0, time_axis, self.sample_rate)

        # 非周期性指標の推定
        ap = pw.d4c(audio, f0, time_axis, self.sample_rate)

        return f0, sp, ap

    def _shift_f0(self, f0: np.ndarray) -> np.ndarray:
        """
        F0（基本周波数）をシフト

        Args:
            f0: 基本周波数配列

        Returns:
            シフトされたF0
        """
        # 半音をHz比率に変換
        pitch_ratio = 2 ** (self.pitch_shift_semitones / 12.0)

        # F0をシフト（無声音区間は0のまま）
        f0_shifted = f0.copy()
        f0_shifted[f0 > 0] *= pitch_ratio

        return f0_shifted

    def _shift_spectrum(self, sp: np.ndarray) -> np.ndarray:
        """
        スペクトル包絡をシフト（フォルマント変更）

        Args:
            sp: スペクトル包絡

        Returns:
            シフトされたスペクトル包絡
        """
        if self.formant_shift == 1.0:
            return sp

        # 周波数軸をスケーリング
        n_frames, n_bins = sp.shape
        new_bins = int(n_bins * self.formant_shift)

        sp_shifted = np.zeros((n_frames, n_bins))

        for i in range(n_frames):
            # リサンプリング
            sp_resampled = signal.resample(sp[i], new_bins)

            # 元のサイズに戻す
            if new_bins > n_bins:
                sp_shifted[i] = sp_resampled[:n_bins]
            else:
                sp_shifted[i, :new_bins] = sp_resampled
                # 残りは外挿
                sp_shifted[i, new_bins:] = sp_resampled[-1]

        return sp_shifted

    def _convert_coreml(self, audio: np.ndarray) -> np.ndarray:
        """
        Core MLで声質変換（Neural Engine最適化）

        Args:
            audio: 入力音声

        Returns:
            変換された音声
        """
        # TODO: Core ML実装
        logger.warning("Core ML processing not yet implemented, using WORLD vocoder")
        return self._world_vocoder(audio)

    def set_pitch_shift(self, semitones: float):
        """
        ピッチシフト量を設定

        Args:
            semitones: 半音数（正の値で高く、負の値で低く）
        """
        self.pitch_shift_semitones = semitones
        logger.info(f"Pitch shift set to: {semitones} semitones")

    def set_formant_shift(self, ratio: float):
        """
        フォルマントシフト率を設定

        Args:
            ratio: シフト率（1.0=変更なし、>1.0=高く、<1.0=低く）
        """
        self.formant_shift = ratio
        logger.info(f"Formant shift set to: {ratio}")

    def get_recommended_settings_male_to_female(self) -> dict:
        """
        男性→女性の推奨設定を取得

        Returns:
            推奨設定の辞書
        """
        return {
            "pitch_shift_semitones": 5.0,  # +5半音（約30%高く）
            "formant_shift": 1.2,  # 20%高く
            "mode": ConversionMode.WORLD_VOCODER,
        }

    def get_recommended_settings_female_to_male(self) -> dict:
        """
        女性→男性の推奨設定を取得

        Returns:
            推奨設定の辞書
        """
        return {
            "pitch_shift_semitones": -5.0,  # -5半音（約30%低く）
            "formant_shift": 0.85,  # 15%低く
            "mode": ConversionMode.WORLD_VOCODER,
        }
