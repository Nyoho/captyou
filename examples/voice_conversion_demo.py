#!/usr/bin/env python3
"""
声質変換デモ - 男性の声を女性の声にリアルタイム変換

使用方法:
    python examples/voice_conversion_demo.py --mode world_vocoder --pitch 5.0

前提条件:
    - macOSにBlackHoleまたはSoundflowerがインストールされていること
    - インストール: brew install blackhole-2ch
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import logging
import time
import sounddevice as sd
from src.audio.capture import AudioCapture
from src.audio.voice_conversion import VoiceConverter, ConversionMode
from src.audio.virtual_audio import VirtualAudioOutput, AudioLoopback

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def parse_args():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description="CaptyOU Voice Conversion Demo")
    parser.add_argument(
        "--mode",
        choices=["pitch_shift", "formant_shift", "world_vocoder"],
        default="world_vocoder",
        help="変換モード (default: world_vocoder)",
    )
    parser.add_argument(
        "--pitch",
        type=float,
        default=5.0,
        help="ピッチシフト量（半音）(default: 5.0)",
    )
    parser.add_argument(
        "--formant",
        type=float,
        default=1.2,
        help="フォルマントシフト率 (default: 1.2)",
    )
    parser.add_argument(
        "--input-device", type=int, help="入力デバイスID（指定しない場合はデフォルト）"
    )
    parser.add_argument(
        "--output-device", type=int, help="出力デバイスID（指定しない場合はデフォルト）"
    )
    parser.add_argument(
        "--list-devices", action="store_true", help="デバイス一覧を表示して終了"
    )
    parser.add_argument(
        "--sample-rate", type=int, default=48000, help="サンプリングレート (default: 48000)"
    )
    parser.add_argument(
        "--block-size", type=int, default=2048, help="ブロックサイズ (default: 2048)"
    )
    return parser.parse_args()


def list_devices():
    """オーディオデバイス一覧を表示"""
    print("=" * 60)
    print("利用可能なオーディオデバイス")
    print("=" * 60)

    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"\n[{i}] {device['name']}")
        print(f"    入力チャンネル: {device['max_input_channels']}")
        print(f"    出力チャンネル: {device['max_output_channels']}")
        print(f"    デフォルトサンプルレート: {device['default_samplerate']} Hz")
        print(f"    デフォルトレイテンシ: "
              f"In={device.get('default_low_input_latency', 0)*1000:.1f}ms, "
              f"Out={device.get('default_low_output_latency', 0)*1000:.1f}ms")

    print("\n" + "=" * 60)
    print("推奨設定:")
    print("  入力: MacBookの内蔵マイク")
    print("  出力: BlackHole 2ch または Soundflower (2ch)")
    print("=" * 60)


def main():
    """メイン関数"""
    args = parse_args()

    if args.list_devices:
        list_devices()
        return

    print("=" * 60)
    print("CaptyOU - Voice Conversion Demo")
    print("=" * 60)
    print(f"モード: {args.mode}")
    print(f"ピッチシフト: +{args.pitch} 半音")
    print(f"フォルマントシフト: {args.formant}x")
    print("=" * 60)
    print("終了: Ctrl+C")
    print("=" * 60)

    # 変換モードを設定
    mode_map = {
        "pitch_shift": ConversionMode.PITCH_SHIFT,
        "formant_shift": ConversionMode.FORMANT_SHIFT,
        "world_vocoder": ConversionMode.WORLD_VOCODER,
    }

    # 声質変換器を初期化
    converter = VoiceConverter(
        sample_rate=args.sample_rate,
        mode=mode_map[args.mode],
        pitch_shift_semitones=args.pitch,
        formant_shift=args.formant,
    )

    # 出力デバイスを検索
    output_device = args.output_device
    if output_device is None:
        # BlackHoleを検索
        output_device = VirtualAudioOutput.find_virtual_device("BlackHole")
        if output_device is None:
            # Soundflowerを検索
            output_device = VirtualAudioOutput.find_virtual_device("Soundflower")

    if output_device is None:
        print("\n警告: 仮想オーディオデバイスが見つかりませんでした")
        print("デフォルトの出力デバイスを使用します")
        print("\nBlackHoleのインストール:")
        print("  brew install blackhole-2ch")
        print("\nまたはSoundflowerをインストール:")
        print("  https://github.com/mattingalls/Soundflower/releases")

    # オーディオループバックを開始
    print("\n処理開始...")
    print("(初回処理には時間がかかる場合があります)")

    try:
        with AudioLoopback(
            input_device=args.input_device,
            output_device=output_device,
            sample_rate=args.sample_rate,
            channels=1,
            block_size=args.block_size,
            converter=converter,
        ) as loopback:
            if not loopback.is_running:
                print("エラー: オーディオループバックを開始できませんでした")
                return

            print("\n声質変換が動作中...")
            print("マイクに向かって話してください")

            # 無限ループ
            while True:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n中断されました")
    finally:
        print("終了しました")


if __name__ == "__main__":
    main()
