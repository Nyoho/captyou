#!/usr/bin/env python3
"""
基本デモ - ポーズと表情をリアルタイムで検出して画面に表示

使用方法:
    python examples/basic_demo.py
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import logging
from src.camera.capture import CameraCapture
from src.pose.estimator import PoseEstimator
from src.face.expression import FaceExpression

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """メイン関数"""
    print("=" * 60)
    print("CaptyOU - Basic Demo")
    print("=" * 60)
    print("カメラからリアルタイムでポーズと表情を検出します")
    print("終了: ESCキー または Qキー")
    print("=" * 60)

    # カメラを初期化
    camera = CameraCapture(
        camera_id=0, width=1280, height=720, fps=30, use_macos_optimization=True
    )

    # ポーズ推定器を初期化
    pose_estimator = PoseEstimator(
        model_complexity=1,  # 0=Lite, 1=Full, 2=Heavy
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    # 表情認識器を初期化
    face_estimator = FaceExpression(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    # カメラを開く
    if not camera.open():
        print("エラー: カメラを開けませんでした")
        return

    print("\n処理開始...")
    print("(初回フレームの処理には時間がかかる場合があります)")

    try:
        frame_count = 0
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

            # 結果を画面に描画
            if pose_data is not None:
                frame = pose_estimator.draw_landmarks(frame, pose_data)

                # ポーズ情報を表示
                cv2.putText(
                    frame,
                    f"Pose Confidence: {pose_data.confidence:.2f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

            if face_data is not None:
                frame = face_estimator.draw_landmarks(frame, face_data)

                # 表情情報を表示
                blend_shapes = face_data.blend_shapes
                y_offset = 60
                cv2.putText(
                    frame,
                    f"Eye Blink L: {blend_shapes.eye_blink_left:.2f}",
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 0),
                    1,
                )
                y_offset += 25
                cv2.putText(
                    frame,
                    f"Eye Blink R: {blend_shapes.eye_blink_right:.2f}",
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 0),
                    1,
                )
                y_offset += 25
                cv2.putText(
                    frame,
                    f"Jaw Open: {blend_shapes.jaw_open:.2f}",
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 0),
                    1,
                )
                y_offset += 25
                cv2.putText(
                    frame,
                    f"Smile L: {blend_shapes.mouth_smile_left:.2f}",
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 0),
                    1,
                )
                y_offset += 25
                cv2.putText(
                    frame,
                    f"Smile R: {blend_shapes.mouth_smile_right:.2f}",
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 0),
                    1,
                )

            # FPS表示
            cv2.putText(
                frame,
                f"Frame: {frame_count}",
                (frame.shape[1] - 150, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

            # 画面に表示
            cv2.imshow("CaptyOU - Basic Demo", frame)

            # キー入力処理
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):  # ESCまたはQ
                break

    except KeyboardInterrupt:
        print("\n中断されました")
    finally:
        # クリーンアップ
        camera.close()
        pose_estimator.close()
        face_estimator.close()
        cv2.destroyAllWindows()
        print("\n終了しました")


if __name__ == "__main__":
    main()
