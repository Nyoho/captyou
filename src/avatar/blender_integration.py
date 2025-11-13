"""
Blender統合モジュール

Blender Python APIを使用して3Dアバターを制御します。
"""

import numpy as np
from typing import Optional, Dict
import logging
import socket
import json

logger = logging.getLogger(__name__)


class BlenderAvatar:
    """
    Blenderアバター制御クラス

    Blender内のアバターをリアルタイムで制御します。
    ソケット通信またはBlender Python APIの直接呼び出しで動作します。
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        use_socket: bool = True,
    ):
        """
        Blenderアバター制御を初期化

        Args:
            host: Blenderサーバーのホスト
            port: Blenderサーバーのポート
            use_socket: ソケット通信を使用（Falseの場合は直接API呼び出し）
        """
        self.host = host
        self.port = port
        self.use_socket = use_socket
        self.socket: Optional[socket.socket] = None
        self.connected = False

        # ボーン名マッピング（Mixamoリグを想定）
        self.bone_mapping = {
            # 頭部
            "head": "mixamorig:Head",
            "neck": "mixamorig:Neck",
            # 上半身
            "spine": "mixamorig:Spine",
            "spine1": "mixamorig:Spine1",
            "spine2": "mixamorig:Spine2",
            # 左腕
            "left_shoulder": "mixamorig:LeftShoulder",
            "left_arm": "mixamorig:LeftArm",
            "left_forearm": "mixamorig:LeftForeArm",
            "left_hand": "mixamorig:LeftHand",
            # 右腕
            "right_shoulder": "mixamorig:RightShoulder",
            "right_arm": "mixamorig:RightArm",
            "right_forearm": "mixamorig:RightForeArm",
            "right_hand": "mixamorig:RightHand",
            # 左脚
            "left_up_leg": "mixamorig:LeftUpLeg",
            "left_leg": "mixamorig:LeftLeg",
            "left_foot": "mixamorig:LeftFoot",
            # 右脚
            "right_up_leg": "mixamorig:RightUpLeg",
            "right_leg": "mixamorig:RightLeg",
            "right_foot": "mixamorig:RightFoot",
        }

        logger.info(f"BlenderAvatar initialized: {host}:{port}, socket={use_socket}")

    def connect(self) -> bool:
        """
        Blenderに接続

        Returns:
            接続成功時True
        """
        if not self.use_socket:
            logger.info("Direct API mode (requires running inside Blender)")
            self.connected = True
            return True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Connected to Blender: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Blender: {e}")
            return False

    def disconnect(self):
        """接続を切断"""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False
        logger.info("Disconnected from Blender")

    def update_pose(self, pose_landmarks) -> bool:
        """
        ポーズデータでアバターを更新

        Args:
            pose_landmarks: PoseLandmarksオブジェクト

        Returns:
            更新成功時True
        """
        if not self.connected:
            logger.warning("Not connected to Blender")
            return False

        try:
            # ランドマークから回転を計算
            rotations = self._calculate_bone_rotations(pose_landmarks)

            # Blenderに送信
            data = {"type": "pose", "rotations": rotations}

            if self.use_socket:
                self._send_data(data)
            else:
                self._apply_rotations_direct(rotations)

            return True

        except Exception as e:
            logger.error(f"Failed to update pose: {e}")
            return False

    def update_expression(self, face_landmarks) -> bool:
        """
        表情データでアバターを更新

        Args:
            face_landmarks: FaceLandmarksオブジェクト

        Returns:
            更新成功時True
        """
        if not self.connected:
            logger.warning("Not connected to Blender")
            return False

        try:
            # ブレンドシェイプを取得
            blend_shapes = face_landmarks.blend_shapes.to_dict()

            # Blenderに送信
            data = {"type": "expression", "blend_shapes": blend_shapes}

            if self.use_socket:
                self._send_data(data)
            else:
                self._apply_blend_shapes_direct(blend_shapes)

            return True

        except Exception as e:
            logger.error(f"Failed to update expression: {e}")
            return False

    def _calculate_bone_rotations(self, pose_landmarks) -> Dict[str, list]:
        """
        ポーズランドマークからボーン回転を計算

        Args:
            pose_landmarks: PoseLandmarksオブジェクト

        Returns:
            ボーン名と回転角度（オイラー角）の辞書
        """
        rotations = {}
        landmarks = pose_landmarks.landmarks

        # 簡易的な実装：主要なボーンのみ計算
        # より正確な実装には逆運動学（IK）が必要

        # 肩の回転（左）
        left_shoulder = landmarks[11]  # 左肩
        left_elbow = landmarks[13]  # 左肘
        shoulder_to_elbow = left_elbow[:3] - left_shoulder[:3]
        left_arm_rotation = self._vector_to_euler(shoulder_to_elbow)
        rotations["left_arm"] = left_arm_rotation.tolist()

        # 肩の回転（右）
        right_shoulder = landmarks[12]  # 右肩
        right_elbow = landmarks[14]  # 右肘
        shoulder_to_elbow = right_elbow[:3] - right_shoulder[:3]
        right_arm_rotation = self._vector_to_euler(shoulder_to_elbow)
        rotations["right_arm"] = right_arm_rotation.tolist()

        return rotations

    def _vector_to_euler(self, vector: np.ndarray) -> np.ndarray:
        """
        ベクトルからオイラー角を計算

        Args:
            vector: 方向ベクトル

        Returns:
            オイラー角 (x, y, z) in radians
        """
        # 正規化
        vector = vector / (np.linalg.norm(vector) + 1e-6)

        # オイラー角を計算
        pitch = np.arcsin(-vector[1])
        yaw = np.arctan2(vector[0], vector[2])
        roll = 0.0  # 簡易実装

        return np.array([pitch, yaw, roll])

    def _send_data(self, data: dict):
        """
        データをBlenderに送信

        Args:
            data: 送信するデータ
        """
        if not self.socket:
            return

        json_data = json.dumps(data)
        self.socket.sendall(json_data.encode("utf-8") + b"\n")

    def _apply_rotations_direct(self, rotations: Dict[str, list]):
        """
        Blender Python APIで直接回転を適用

        Args:
            rotations: ボーン回転の辞書
        """
        try:
            import bpy
            import mathutils

            # アクティブなアーマチュアを取得
            armature = bpy.context.active_object
            if not armature or armature.type != "ARMATURE":
                logger.warning("No active armature found")
                return

            # ポーズモードに切り替え
            bpy.ops.object.mode_set(mode="POSE")

            # 各ボーンに回転を適用
            for bone_key, rotation in rotations.items():
                bone_name = self.bone_mapping.get(bone_key, bone_key)
                if bone_name in armature.pose.bones:
                    bone = armature.pose.bones[bone_name]
                    bone.rotation_euler = mathutils.Euler(rotation, "XYZ")

        except ImportError:
            logger.error("Blender Python API not available (not running in Blender)")
        except Exception as e:
            logger.error(f"Failed to apply rotations: {e}")

    def _apply_blend_shapes_direct(self, blend_shapes: Dict[str, float]):
        """
        Blender Python APIで直接ブレンドシェイプを適用

        Args:
            blend_shapes: ブレンドシェイプの辞書
        """
        try:
            import bpy

            # アクティブなメッシュオブジェクトを取得
            obj = bpy.context.active_object
            if not obj or not obj.data.shape_keys:
                logger.warning("No shape keys found")
                return

            # 各ブレンドシェイプの値を設定
            for shape_name, value in blend_shapes.items():
                if shape_name in obj.data.shape_keys.key_blocks:
                    obj.data.shape_keys.key_blocks[shape_name].value = value

        except ImportError:
            logger.error("Blender Python API not available (not running in Blender)")
        except Exception as e:
            logger.error(f"Failed to apply blend shapes: {e}")

    def __enter__(self):
        """コンテキストマネージャー: 開始"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了"""
        self.disconnect()
