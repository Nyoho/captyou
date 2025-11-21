import bpy
import socket
import json
import threading
import mathutils
from mathutils import Vector, Euler

class CaptyOUReceiverVRoid:
    """
    CaptyOUからデータを受信してVRoidアバターを制御
    VRoid Studio製アバター専用
    """

    def __init__(self, port=9000):
        self.port = port
        self.socket = None
        self.running = False
        self.thread = None

        # アバターデータ
        self.armature = None
        self.mesh = None

        # ポーズデータ
        self.pose_data = {}

        # 表情データ
        self.expression_data = {
            'eye_blink_left': 0.0,
            'eye_blink_right': 0.0,
            'jaw_open': 0.0,
            'mouth_smile_left': 0.0,
            'mouth_smile_right': 0.0,
        }

    def find_avatar(self):
        """シーン内のVRoidアバターを検索"""
        # アーマチュアを検索
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                self.armature = obj
                print(f"Found armature: {obj.name}")
                break

        # メッシュを検索（シェイプキー用）
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data.shape_keys:
                self.mesh = obj
                print(f"Found mesh with shape keys: {obj.name}")
                break

    def start(self):
        """受信を開始"""
        self.find_avatar()

        if not self.armature:
            print("Error: No armature found in scene")
            print("Please import a VRM avatar first!")
            return False

        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()

        # タイマーで定期的にアバターを更新
        bpy.app.timers.register(self._update_avatar, first_interval=0.033)  # 30 FPS

        print(f"CaptyOU Receiver (VRoid) started on port {self.port}")
        return True

    def stop(self):
        """受信を停止"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("CaptyOU Receiver stopped")

    def _receive_loop(self):
        """ソケットでデータ受信（バックグラウンドスレッド）"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('localhost', self.port))
            self.socket.listen(1)

            print(f"Waiting for connection on port {self.port}...")

            conn, addr = self.socket.accept()
            print(f"Connected: {addr}")

            buffer = ""
            while self.running:
                try:
                    data = conn.recv(4096).decode('utf-8')
                    if not data:
                        break

                    buffer += data

                    # 改行で区切ってJSONをパース
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                msg = json.loads(line)
                                self._process_message(msg)
                            except json.JSONDecodeError as e:
                                print(f"JSON decode error: {e}")
                except Exception as e:
                    print(f"Receive error: {e}")
                    break

        except Exception as e:
            print(f"Socket error: {e}")
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass

    def _process_message(self, msg):
        """受信したメッセージを処理"""
        msg_type = msg.get('type')

        if msg_type == 'pose':
            # ポーズデータ
            self.pose_data = msg.get('rotations', {})

        elif msg_type == 'expression':
            # 表情データ
            blend_shapes = msg.get('blend_shapes', {})
            self.expression_data.update(blend_shapes)

    def _update_avatar(self):
        """アバターを更新（メインスレッド）"""
        if not self.running:
            return None  # タイマーを停止

        # ポーズを適用
        self._apply_pose()

        # 表情を適用
        self._apply_expressions()

        return 0.033  # 30 FPS

    def _apply_pose(self):
        """ポーズをアバターに適用"""
        if not self.armature or not self.pose_data:
            return

        # ポーズモードに切り替え
        bpy.context.view_layer.objects.active = self.armature

        for bone_key, rotation in self.pose_data.items():
            # VRoidボーン名を取得
            bone_name = self._get_vroid_bone_name(bone_key)

            if bone_name and bone_name in self.armature.pose.bones:
                bone = self.armature.pose.bones[bone_name]

                # オイラー角を適用
                bone.rotation_euler = Euler(rotation, 'XYZ')

    def _apply_expressions(self):
        """表情（シェイプキー）をアバターに適用"""
        if not self.mesh or not self.mesh.data.shape_keys:
            return

        shape_keys = self.mesh.data.shape_keys.key_blocks

        # VRoidシェイプキーにマッピング
        mapping = {
            'eye_blink_left': 'Fcl_EYE_Close_L',
            'eye_blink_right': 'Fcl_EYE_Close_R',
            'jaw_open': 'Fcl_MTH_A',
            'mouth_smile_left': 'Fcl_MTH_Joy',
            'mouth_smile_right': 'Fcl_MTH_Joy',
        }

        for exp_key, shape_name in mapping.items():
            if exp_key in self.expression_data and shape_name in shape_keys:
                value = self.expression_data[exp_key]

                # Joy（笑顔）は左右の平均
                if shape_name == 'Fcl_MTH_Joy':
                    value = (self.expression_data.get('mouth_smile_left', 0) +
                            self.expression_data.get('mouth_smile_right', 0)) / 2

                shape_keys[shape_name].value = value

    def _get_vroid_bone_name(self, bone_key):
        """CaptyOUのボーンキーからVRoidボーン名を取得"""
        # VRoidボーン名マッピング（J_Bip_ プレフィックス）
        vroid_mapping = {
            'head': 'J_Bip_C_Head',
            'neck': 'J_Bip_C_Neck',
            'spine': 'J_Bip_C_Spine',
            'chest': 'J_Bip_C_Chest',
            'upper_chest': 'J_Bip_C_UpperChest',
            'hips': 'J_Bip_C_Hips',
            # 左腕
            'left_shoulder': 'J_Bip_L_Shoulder',
            'left_arm': 'J_Bip_L_UpperArm',
            'left_forearm': 'J_Bip_L_LowerArm',
            'left_hand': 'J_Bip_L_Hand',
            # 右腕
            'right_shoulder': 'J_Bip_R_Shoulder',
            'right_arm': 'J_Bip_R_UpperArm',
            'right_forearm': 'J_Bip_R_LowerArm',
            'right_hand': 'J_Bip_R_Hand',
            # 左脚
            'left_up_leg': 'J_Bip_L_UpperLeg',
            'left_leg': 'J_Bip_L_LowerLeg',
            'left_foot': 'J_Bip_L_Foot',
            # 右脚
            'right_up_leg': 'J_Bip_R_UpperLeg',
            'right_leg': 'J_Bip_R_LowerLeg',
            'right_foot': 'J_Bip_R_Foot',
        }

        return vroid_mapping.get(bone_key)


# グローバル変数
receiver = None


def start_receiver(port=9000):
    """受信を開始"""
    global receiver

    if receiver and receiver.running:
        print("Receiver already running")
        return

    receiver = CaptyOUReceiverVRoid(port=port)
    receiver.start()


def stop_receiver():
    """受信を停止"""
    global receiver

    if receiver:
        receiver.stop()
        receiver = None


# Blenderオペレーター（UIボタン用）
class CAPTYOU_OT_start_receiver(bpy.types.Operator):
    """CaptyOU受信を開始"""
    bl_idname = "captyou.start_receiver"
    bl_label = "Start CaptyOU Receiver"

    def execute(self, context):
        start_receiver()
        return {'FINISHED'}


class CAPTYOU_OT_stop_receiver(bpy.types.Operator):
    """CaptyOU受信を停止"""
    bl_idname = "captyou.stop_receiver"
    bl_label = "Stop CaptyOU Receiver"

    def execute(self, context):
        stop_receiver()
        return {'FINISHED'}


# UIパネル
class CAPTYOU_PT_panel(bpy.types.Panel):
    """CaptyOUパネル"""
    bl_label = "CaptyOU Receiver (VRoid)"
    bl_idname = "CAPTYOU_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CaptyOU'

    def draw(self, context):
        layout = self.layout

        layout.operator("captyou.start_receiver")
        layout.operator("captyou.stop_receiver")


# 登録
classes = [
    CAPTYOU_OT_start_receiver,
    CAPTYOU_OT_stop_receiver,
    CAPTYOU_PT_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


# スクリプトから直接実行する場合
if __name__ == "__main__":
    register()
    start_receiver(port=9000)
