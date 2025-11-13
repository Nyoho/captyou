#!/usr/bin/env python3
"""
配信デモ - ポーズと表情をUnityに送信し、Virtual Cameraで配信

使用方法:
    python examples/streaming_demo.py --unity-host localhost --unity-port 9000
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import argparse
import logging
import time
from src.camera.capture import CameraCapture
from src.pose.estimator import PoseEstimator
from src.face.expression import FaceExpression
from src.avatar.unity_integration import UnityAvatar
from src.streaming.virtual_camera import VirtualCamera

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def parse_args():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description="CaptyOU Streaming Demo")
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
        help="Unity communication protocol (default: osc)",
    )
    parser.add_argument(
        "--virtual-camera",
        action="store_true",
        help="Enable virtual camera output",
    )
    parser.add_argument(
        "--show-preview", action="store_true", help="Show preview window"
    )
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
    return parser.parse_args()


def main():
    """メイン関数"""
    args = parse_args()

    print("=" * 60)
    print("CaptyOU - Streaming Demo")
    print("=" * 60)
    print(f"Unity: {args.unity_host}:{args.unity_port} ({args.unity_protocol})")
    print(f"Virtual Camera: {'有効' if args.virtual_camera else '無効'}")
    print(f"Preview: {'有効' if args.show_preview else '無効'}")
    print("=" * 60)
    print("終了: Ctrl+C")
    print("=" * 60)

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

            # プレビュー表示
            if args.show_preview:
                preview_frame = frame.copy()

                if pose_data is not None:
                    preview_frame = pose_estimator.draw_landmarks(
                        preview_frame, pose_data
                    )

                if face_data is not None:
                    preview_frame = face_estimator.draw_landmarks(
                        preview_frame, face_data
                    )

                # FPS計算
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0

                cv2.putText(
                    preview_frame,
                    f"FPS: {fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                cv2.imshow("CaptyOU - Streaming Demo", preview_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == 27 or key == ord("q"):
                    break

                # Virtual Cameraに送信
                if virtual_cam:
                    virtual_cam.send_frame(preview_frame)
            else:
                # Virtual Cameraに送信（プレビューなし）
                if virtual_cam:
                    virtual_cam.send_frame(frame)

            # FPS制御
            if virtual_cam:
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
