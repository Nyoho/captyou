#!/usr/bin/env python3
"""
Blender接続デバッグスクリプト

接続状態とデータ送信を詳しく確認します
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import logging
import time
from src.camera.capture import CameraCapture
from src.pose.estimator import PoseEstimator
from src.face.expression import FaceExpression
from src.avatar.blender_integration import BlenderAvatar

# デバッグレベルのログを有効化
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def main():
    print("=" * 70)
    print("CaptyOU - Blender Debug")
    print("=" * 70)

    # ステップ1: Blenderに接続
    print("\n[ステップ1] Blenderへの接続を試みます...")
    print("確認: Blenderでcaptyou_receiver.pyを実行していますか?")
    input("準備ができたらEnterキーを押してください...")

    blender_avatar = BlenderAvatar(
        host="localhost",
        port=9000,
        use_socket=True
    )

    if not blender_avatar.connect():
        print("❌ エラー: Blenderに接続できませんでした")
        print("\n確認事項:")
        print("1. Blenderを起動していますか?")
        print("2. captyou_receiver.pyをBlenderで実行しましたか?")
        print("3. Blenderのコンソールに 'Waiting for connection on port 9000...' と表示されていますか?")
        print("\n実行方法:")
        print("  - Blender → Scripting → Text Editor → captyou_receiver.py を開く")
        print("  - 'Run Script' ボタンをクリック")
        return

    print("✅ Blenderに接続しました!")

    # ステップ2: カメラを初期化
    print("\n[ステップ2] カメラを初期化します...")
    camera = CameraCapture(
        camera_id=0,
        width=1280,
        height=720,
        fps=30,
        use_macos_optimization=True
    )

    if not camera.open():
        print("❌ エラー: カメラを開けませんでした")
        return

    print("✅ カメラを開きました")

    # ステップ3: エスティメータを初期化
    print("\n[ステップ3] ポーズ・表情推定器を初期化します...")
    pose_estimator = PoseEstimator(
        model_complexity=1,
        smooth_landmarks=True,
        min_tracking_confidence=0.5,
    )

    face_estimator = FaceExpression(
        max_num_faces=1,
        refine_landmarks=True,
        min_tracking_confidence=0.5,
    )

    print("✅ エスティメータを初期化しました")

    # ステップ4: テストフレームを処理
    print("\n[ステップ4] テストフレームを処理します...")
    print("カメラに向かって顔を見せてください...")

    pose_detected = False
    face_detected = False

    for i in range(30):  # 30フレーム試行
        ret, frame = camera.read()
        if not ret:
            continue

        # ポーズ検出
        pose_data = pose_estimator.process(frame)
        if pose_data is not None and not pose_detected:
            print(f"✅ ポーズを検出しました! (ランドマーク数: {len(pose_data.landmarks)})")
            pose_detected = True

        # 表情検出
        face_data = face_estimator.process(frame)
        if face_data is not None and not face_detected:
            print(f"✅ 顔を検出しました! (ランドマーク数: {len(face_data.landmarks)})")
            print(f"   ブレンドシェイプ例: 目の開閉={face_data.blend_shapes.eye_blink_left:.2f}")
            face_detected = True

        if pose_detected and face_detected:
            break

        time.sleep(0.1)

    if not pose_detected:
        print("⚠️ 警告: ポーズが検出されませんでした")
        print("   カメラに体全体が映っているか確認してください")

    if not face_detected:
        print("⚠️ 警告: 顔が検出されませんでした")
        print("   カメラに顔がはっきり映っているか確認してください")

    # ステップ5: Blenderにデータ送信
    print("\n[ステップ5] Blenderにデータを送信します...")

    data_sent = False

    try:
        for i in range(100):  # 100フレーム送信
            ret, frame = camera.read()
            if not ret:
                continue

            # ポーズ処理
            pose_data = pose_estimator.process(frame)
            if pose_data is not None:
                success = blender_avatar.update_pose(pose_data)
                if success and not data_sent:
                    print(f"✅ ポーズデータを送信しました (フレーム {i})")
                    data_sent = True

            # 表情処理
            face_data = face_estimator.process(frame)
            if face_data is not None:
                success = blender_avatar.update_expression(face_data)
                if success and data_sent:
                    print(f"✅ 表情データを送信しました (フレーム {i})")
                    print(f"   目の開閉: 左={face_data.blend_shapes.eye_blink_left:.2f}, 右={face_data.blend_shapes.eye_blink_right:.2f}")
                    print(f"   口の開閉: {face_data.blend_shapes.jaw_open:.2f}")
                    break

            # プレビュー表示
            display_frame = frame.copy()
            if pose_data is not None:
                display_frame = pose_estimator.draw_landmarks(display_frame, pose_data)
            if face_data is not None:
                display_frame = face_estimator.draw_landmarks(display_frame, face_data)

            cv2.imshow("Debug Preview", display_frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

            time.sleep(0.03)  # 30 FPS

    except KeyboardInterrupt:
        print("\n中断されました")
    finally:
        camera.close()
        pose_estimator.close()
        face_estimator.close()
        blender_avatar.disconnect()
        cv2.destroyAllWindows()

    print("\n" + "=" * 70)
    print("診断結果:")
    print("=" * 70)
    print(f"✅ Blender接続: 成功")
    print(f"{'✅' if pose_detected else '❌'} ポーズ検出: {'成功' if pose_detected else '失敗'}")
    print(f"{'✅' if face_detected else '❌'} 顔検出: {'成功' if face_detected else '失敗'}")
    print(f"{'✅' if data_sent else '❌'} データ送信: {'成功' if data_sent else '失敗'}")
    print("=" * 70)

    if pose_detected and face_detected and data_sent:
        print("\n✅ すべて正常に動作しています!")
        print("\nBlender側で確認:")
        print("1. アバターが動いていますか?")
        print("2. Blenderのコンソールにエラーメッセージはありませんか?")
        print("3. VRMアバターが正しく読み込まれていますか?")
    else:
        print("\n⚠️ 問題が見つかりました。上記の診断結果を確認してください。")

if __name__ == "__main__":
    main()
