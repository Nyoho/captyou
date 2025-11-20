#!/usr/bin/env python3
"""
Blenderデモ - ポーズと表情をBlenderのVRMアバターに送信

使用方法:
    # 1. Blender側でcaptyou_receiver.pyを実行
    # 2. このスクリプトを実行
    uv run examples/blender_demo.py
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import logging
import time
from src.camera.capture import CameraCapture
from src.pose.estimator import PoseEstimator
from src.face.expression import FaceExpression
from src.avatar.blender_integration import BlenderAvatar

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """メイン関数"""
    print("=" * 70)
    print("CaptyOU - Blender Demo")
    print("=" * 70)
    print("\n準備:")
    print("1. Blenderでcaptyou_receiver.pyを実行済みか確認")
    print("2. VRMアバターがシーンに読み込まれているか確認")
    print("=" * 70)
    print("\nBlenderに接続します...")

    # カメラを初期化
    camera = CameraCapture(
        camera_id=0,
        width=1280,
        height=720,
        fps=30,
        use_macos_optimization=True
    )

    # ポーズ推定器を初期化
    pose_estimator = PoseEstimator(
        model_complexity=1,
        smooth_landmarks=True,
        min_tracking_confidence=0.5,
    )

    # 表情認識器を初期化
    face_estimator = FaceExpression(
        max_num_faces=1,
        refine_landmarks=True,
        min_tracking_confidence=0.5,
    )

    # Blenderアバターに接続
    blender_avatar = BlenderAvatar(
        host="localhost",
        port=9000,
        use_socket=True
    )

    # カメラを開く
    if not camera.open():
        print("エラー: カメラを開けませんでした")
        return

    # Blenderに接続
    print("\nBlenderに接続中...")
    if not blender_avatar.connect():
        print("エラー: Blenderに接続できませんでした")
        print("\n確認事項:")
        print("1. Blenderでcaptyou_receiver.pyが実行されているか")
        print("2. ポート番号が9000で合っているか")
        print("3. Blenderのコンソールに 'Waiting for connection...' と表示されているか")
        return

    print("✓ Blenderに接続しました！")
    print("\n処理開始...")
    print("(カメラに向かって動いてみてください)")
    print("終了: ESCキー または Qキー\n")

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

            # Blenderに送信
            if pose_data is not None:
                blender_avatar.update_pose(pose_data)

            if face_data is not None:
                blender_avatar.update_expression(face_data)

            # プレビュー表示（オプション）
            display_frame = frame.copy()

            # ランドマークを描画
            if pose_data is not None:
                display_frame = pose_estimator.draw_landmarks(display_frame, pose_data)

            if face_data is not None:
                display_frame = face_estimator.draw_landmarks(display_frame, face_data)

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

            cv2.putText(
                display_frame,
                "Blender: Connected",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )

            # 画面に表示
            cv2.imshow("CaptyOU - Blender Demo", display_frame)

            # キー入力処理
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):  # ESCまたはQ
                break

            # 定期的にFPS表示
            if frame_count % 100 == 0:
                print(f"Frames: {frame_count}, FPS: {fps:.1f}")

    except KeyboardInterrupt:
        print("\n中断されました")
    finally:
        # クリーンアップ
        camera.close()
        pose_estimator.close()
        face_estimator.close()
        blender_avatar.disconnect()
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
