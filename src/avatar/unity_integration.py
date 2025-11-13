"""
Unity統合モジュール

OSCまたはWebSocketを使用してUnityの3Dアバターを制御します。
VRChat、VSeeFaceなどと互換性があります。
"""

from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
import asyncio
import websockets
import json
import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class UnityAvatar:
    """
    Unityアバター制御クラス

    OSC（VRChat互換）またはWebSocketでUnityのアバターを制御します。
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        protocol: str = "osc",  # "osc" or "websocket"
    ):
        """
        Unityアバター制御を初期化

        Args:
            host: Unityサーバーのホスト
            port: Unityサーバーのポート
            protocol: 通信プロトコル ("osc" or "websocket")
        """
        self.host = host
        self.port = port
        self.protocol = protocol.lower()

        if self.protocol == "osc":
            self.client = udp_client.SimpleUDPClient(host, port)
        elif self.protocol == "websocket":
            self.websocket = None
        else:
            raise ValueError(f"Unknown protocol: {protocol}")

        self.connected = False

        logger.info(
            f"UnityAvatar initialized: {host}:{port}, protocol={self.protocol}"
        )

    def connect(self) -> bool:
        """
        Unityに接続

        Returns:
            接続成功時True
        """
        if self.protocol == "osc":
            # OSCはコネクションレスなのですぐに接続済みとする
            self.connected = True
            logger.info(f"OSC client ready: {self.host}:{self.port}")
            return True
        elif self.protocol == "websocket":
            # WebSocketは非同期接続が必要
            logger.info("WebSocket connection requires async context")
            return False
        return False

    async def connect_async(self) -> bool:
        """
        Unityに非同期接続（WebSocket用）

        Returns:
            接続成功時True
        """
        if self.protocol != "websocket":
            return self.connect()

        try:
            uri = f"ws://{self.host}:{self.port}"
            self.websocket = await websockets.connect(uri)
            self.connected = True
            logger.info(f"Connected to Unity via WebSocket: {uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Unity: {e}")
            return False

    def disconnect(self):
        """接続を切断"""
        if self.protocol == "websocket" and self.websocket:
            asyncio.create_task(self.websocket.close())
        self.connected = False
        logger.info("Disconnected from Unity")

    def send_pose(self, pose_landmarks) -> bool:
        """
        ポーズデータをUnityに送信

        Args:
            pose_landmarks: PoseLandmarksオブジェクト

        Returns:
            送信成功時True
        """
        if not self.connected and self.protocol != "osc":
            logger.warning("Not connected to Unity")
            return False

        try:
            # ランドマークをVRChat OSC形式に変換
            osc_data = self._convert_pose_to_osc(pose_landmarks)

            if self.protocol == "osc":
                self._send_osc_data(osc_data)
            elif self.protocol == "websocket":
                asyncio.create_task(self._send_websocket_data(osc_data))

            return True

        except Exception as e:
            logger.error(f"Failed to send pose: {e}")
            return False

    def send_expression(self, face_landmarks) -> bool:
        """
        表情データをUnityに送信

        Args:
            face_landmarks: FaceLandmarksオブジェクト

        Returns:
            送信成功時True
        """
        if not self.connected and self.protocol != "osc":
            logger.warning("Not connected to Unity")
            return False

        try:
            # ブレンドシェイプを取得
            blend_shapes = face_landmarks.blend_shapes.to_dict()

            # VRChat OSC形式に変換
            osc_data = self._convert_expression_to_osc(blend_shapes)

            if self.protocol == "osc":
                self._send_osc_data(osc_data)
            elif self.protocol == "websocket":
                asyncio.create_task(self._send_websocket_data(osc_data))

            return True

        except Exception as e:
            logger.error(f"Failed to send expression: {e}")
            return False

    def _convert_pose_to_osc(self, pose_landmarks) -> list:
        """
        ポーズランドマークをVRChat OSC形式に変換

        Args:
            pose_landmarks: PoseLandmarksオブジェクト

        Returns:
            OSCメッセージのリスト [(address, value), ...]
        """
        osc_messages = []
        landmarks = pose_landmarks.landmarks

        # VRChatトラッキングポイント
        # 頭の位置と回転
        head = landmarks[0]  # 鼻
        osc_messages.append(("/tracking/head/position", [head[0], head[1], head[2]]))

        # 左手の位置
        left_hand = landmarks[15]  # 左手首
        osc_messages.append(
            ("/tracking/hand/left/position", [left_hand[0], left_hand[1], left_hand[2]])
        )

        # 右手の位置
        right_hand = landmarks[16]  # 右手首
        osc_messages.append(
            (
                "/tracking/hand/right/position",
                [right_hand[0], right_hand[1], right_hand[2]],
            )
        )

        # 腰の位置
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        hip_center = (left_hip[:3] + right_hip[:3]) / 2
        osc_messages.append(("/tracking/hip/position", hip_center.tolist()))

        return osc_messages

    def _convert_expression_to_osc(self, blend_shapes: Dict[str, float]) -> list:
        """
        ブレンドシェイプをVRChat OSC形式に変換

        Args:
            blend_shapes: ブレンドシェイプの辞書

        Returns:
            OSCメッセージのリスト [(address, value), ...]
        """
        osc_messages = []

        # VRChat表情パラメータマッピング
        vrchat_mapping = {
            "eye_blink_left": "/avatar/parameters/EyeBlinkLeft",
            "eye_blink_right": "/avatar/parameters/EyeBlinkRight",
            "jaw_open": "/avatar/parameters/JawOpen",
            "mouth_smile_left": "/avatar/parameters/SmileLeft",
            "mouth_smile_right": "/avatar/parameters/SmileRight",
        }

        for blend_name, osc_address in vrchat_mapping.items():
            if blend_name in blend_shapes:
                value = blend_shapes[blend_name]
                osc_messages.append((osc_address, value))

        return osc_messages

    def _send_osc_data(self, osc_data: list):
        """
        OSCデータを送信

        Args:
            osc_data: OSCメッセージのリスト [(address, value), ...]
        """
        for address, value in osc_data:
            if isinstance(value, list):
                # 複数の値
                builder = OscMessageBuilder(address=address)
                for v in value:
                    builder.add_arg(float(v))
                msg = builder.build()
                self.client.send(msg)
            else:
                # 単一の値
                self.client.send_message(address, float(value))

    async def _send_websocket_data(self, data: list):
        """
        WebSocketでデータを送信

        Args:
            data: 送信するデータ
        """
        if not self.websocket:
            return

        try:
            json_data = json.dumps({"messages": data})
            await self.websocket.send(json_data)
        except Exception as e:
            logger.error(f"Failed to send WebSocket data: {e}")

    def set_avatar_parameter(self, parameter_name: str, value: float) -> bool:
        """
        アバターパラメータを直接設定

        Args:
            parameter_name: パラメータ名
            value: 値（0.0～1.0）

        Returns:
            送信成功時True
        """
        try:
            address = f"/avatar/parameters/{parameter_name}"
            if self.protocol == "osc":
                self.client.send_message(address, float(value))
            elif self.protocol == "websocket":
                asyncio.create_task(
                    self._send_websocket_data([(address, float(value))])
                )
            return True
        except Exception as e:
            logger.error(f"Failed to set parameter: {e}")
            return False

    def __enter__(self):
        """コンテキストマネージャー: 開始"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了"""
        self.disconnect()
