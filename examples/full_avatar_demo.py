#!/usr/bin/env python3
"""
統合デモ - ポーズ・表情キャプチャ + 声質変換 + アバター制御

リアルタイムでポーズ、表情、声を変換して3Dアバターに反映し、配信します。

使用方法:
    python examples/full_avatar_demo.py \\
        --unity-host localhost --unity-port 9000 \\
        --voice-pitch 5.0 --virtual-camera
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import argparse
import logging
import time
import threading
from src.camera.capture import CameraCapture
from src.pose.estimator import PoseEstimator
from src.face.expression import FaceExpression
from src.avatar.unity_integration import UnityAvatar
from src.streaming.virtual_camera import VirtualCamera
from src.audio.voice_conversion import VoiceConverter, ConversionMode
from src.audio.virtual_audio import AudioLoopback

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def parse_args():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description="CaptyOU Full Avatar Demo")

    # Unity設定
    parser.add_argument(
        "--unity-host", default="localhost", help="Unity server host (default: localhost)"
    )
    parser.add_argument(
        "--unity-port", type=int, default=9000, help="Unity server port (default: 9000)"
    )
    parser.add_argument(
        "--unity-protocol",
        choices=["osc", "websocket"],
        default="osc",
        help="Unity protocol (default: osc)",
    )

    # 映像設定
    parser.add_argument(
        "--camera-id", type=int, default=0, help="Camera device ID (default: 0)"
    )
    parser.add_argument(
        "--width", type=int, default=1280, help="Camera width (default: 1280)"
    )
    parser.add_argument(
        "--height", type=int, default=720, help="Camera height (default: 720)"
    )
    parser.add_argument(
        "--fps", type=int, default=30, help="Frame rate (default: 30)"
    )
    parser.add_argument(
        "--virtual-camera", action="store_true", help="Enable virtual camera output"
    )

    # 音声設定
    parser.add_argument(
        "--enable-voice", action="store_true", help="声質変換を有効化"
    )
    parser.add_argument(
        "--voice-mode",
        choices=["pitch_shift", "formant_shift", "world_vocoder"],
        default="world_vocoder",
        help="声質変換モード (default: world_vocoder)",
    )
    parser.add_argument(
        "--voice-pitch",
        type=float,
        default=5.0,
        help="ピッチシフト量（半音）(default: 5.0)",
    )
    parser.add_argument(
        "--voice-formant",
        type=float,
        default=1.2,
        help="フォルマントシフト率 (default: 1.2)",
    )
    parser.add_argument(
        "--audio-input-device", type=int, help="音声入力デバイスID"
    )
    parser.add_argument(
        "--audio-output-device", type=int, help="音声出力デバイスID"
    )

    # その他
    parser.add_argument(
        "--show-preview", action="store_true", help="プレビューウィンドウを表示"
    )

    return parser.parse_args()


def run_audio_loopback(args, voice_converter):
    """音声ループバックを別スレッドで実行"""
    try:
        with AudioLoopback(
            input_device=args.audio_input_device,
            output_device=args.audio_output_device,
            sample_rate=48000,
            channels=1,
            block_size=2048,
            converter=voice_converter,
        ) as loopback:
            if loopback.is_running:
                logging.info("音声ループバック開始")
                # スレッドが終了されるまで待機
                while True:
                    time.sleep(0.1)
    except Exception as e:
        logging.error(f"音声ループバックエラー: {e}")


def main():
    """メイン関数"""
    args = parse_args()

    print("=" * 70)
    print("CaptyOU - Full Avatar Demo")
    print("=" * 70)
    print(f"Unity: {args.unity_host}:{args.unity_port} ({args.unity_protocol})")
    print(f"映像: {args.width}x{args.height}@{args.fps}fps")
    print(f"Virtual Camera: {'有効' if args.virtual_camera else '無効'}")
    print(f"声質変換: {'有効' if args.enable_voice else '無効'}")
    if args.enable_voice:
        print(f"  モード: {args.voice_mode}")
        print(f"  ピッチ: +{args.voice_pitch} 半音")
        print(f"  フォルマント: {args.voice_formant}x")
    print("=" * 70)
    print("終了: ESCキー または Qキー")
    print("=" * 70)

    # カメラを初期化
    camera = CameraCapture(
        camera_id=args.camera_id,
        width=args.width,
        height=args.height,
        fps=args.fps,
        use_macos_optimization=True,
    )

    # ポーズ推定器を初期化
    pose_estimator = PoseEstimator(
        model_complexity=1, smooth_landmarks=True, min_tracking_confidence=0.5
    )

    # 表情認識器を初期化
    face_estimator = FaceExpression(
        max_num_faces=1, refine_landmarks=True, min_tracking_confidence=0.5
    )

    # Unityアバターを初期化
    unity_avatar = UnityAvatar(
        host=args.unity_host, port=args.unity_port, protocol=args.unity_protocol
    )

    # Virtual Cameraを初期化
    virtual_cam = None
    if args.virtual_camera:
        virtual_cam = VirtualCamera(
            width=args.width, height=args.height, fps=args.fps, backend="obs"
        )

    # 声質変換器を初期化
    voice_converter = None
    audio_thread = None
    if args.enable_voice:
        mode_map = {
            "pitch_shift": ConversionMode.PITCH_SHIFT,
            "formant_shift": ConversionMode.FORMANT_SHIFT,
            "world_vocoder": ConversionMode.WORLD_VOCODER,
        }

        voice_converter = VoiceConverter(
            sample_rate=48000,
            mode=mode_map[args.voice_mode],
            pitch_shift_semitones=args.voice_pitch,
            formant_shift=args.voice_formant,
        )

        # 音声ループバックを別スレッドで開始
        audio_thread = threading.Thread(
            target=run_audio_loopback,
            args=(args, voice_converter),
            daemon=True,
        )
        audio_thread.start()

    # 接続
    if not camera.open():
        print("エラー: カメラを開けませんでした")
        return

    unity_avatar.connect()

    if virtual_cam:
        if not virtual_cam.start():
            print("警告: Virtual Cameraを開始できませんでした")
            virtual_cam = None

    print("\n処理開始...")
    print("(初回フレームの処理には時間がかかる場合があります)")

    try:
        frame_count = 0
        start_time = time.time()

        while True:
            # フレームを読み込み
            ret, frame = camera.read()
            if not ret or frame is None:
                print("エラー: フレームを読み込めませんでした")
                break

            frame_count += 1

            # ポーズを推定
            pose_data = pose_estimator.process(frame)

            # 表情を認識
            face_data = face_estimator.process(frame)

            # Unityに送信
            if pose_data is not None:
                unity_avatar.send_pose(pose_data)

            if face_data is not None:
                unity_avatar.send_expression(face_data)

            # プレビュー表示 or Virtual Camera出力
            if args.show_preview or virtual_cam:
                display_frame = frame.copy()

                # ランドマークを描画
                if pose_data is not None:
                    display_frame = pose_estimator.draw_landmarks(
                        display_frame, pose_data
                    )

                if face_data is not None:
                    display_frame = face_estimator.draw_landmarks(
                        display_frame, face_data
                    )

                # FPS表示
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0

                cv2.putText(
                    display_frame,
                    f"FPS: {fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                # 音声状態表示
                if args.enable_voice:
                    cv2.putText(
                        display_frame,
                        "Voice: ON",
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2,
                    )

                # プレビュー表示
                if args.show_preview:
                    cv2.imshow("CaptyOU - Full Avatar Demo", display_frame)

                    key = cv2.waitKey(1) & 0xFF
                    if key == 27 or key == ord("q"):
                        break

                # Virtual Cameraに送信
                if virtual_cam:
                    virtual_cam.send_frame(display_frame)
                    virtual_cam.wait()

            # 定期的にFPS表示
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                print(f"Frames: {frame_count}, FPS: {fps:.1f}")

    except KeyboardInterrupt:
        print("\n中断されました")
    finally:
        # クリーンアップ
        camera.close()
        pose_estimator.close()
        face_estimator.close()
        unity_avatar.disconnect()

        if virtual_cam:
            virtual_cam.stop()

        if args.show_preview:
            cv2.destroyAllWindows()

        # 最終統計
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        print("\n統計:")
        print(f"  総フレーム数: {frame_count}")
        print(f"  実行時間: {elapsed:.1f}秒")
        print(f"  平均FPS: {fps:.1f}")
        print("\n終了しました")


if __name__ == "__main__":
    main()
