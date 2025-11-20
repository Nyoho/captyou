import bpy
import socket
import json
import threading
import mathutils
from mathutils import Vector, Euler

class CaptyOUReceiver:
    """
    CaptyOUからデータを受信してBlenderアバターを制御（デバッグ版）
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

        # デバッグカウンター
        self.message_count = 0
        self.update_count = 0

    def find_avatar(self):
        """シーン内のVRMアバターを検索"""
        print("\n=== アバター検索開始 ===")

        # アーマチュアを検索
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                self.armature = obj
                print(f"✓ アーマチュアを発見: {obj.name}")

                # ボーン名を表示
                print(f"  ボーン数: {len(obj.pose.bones)}")
                print(f"  最初の10個のボーン名:")
                for i, bone in enumerate(obj.pose.bones[:10]):
                    print(f"    {i+1}. {bone.name}")
                break

        if not self.armature:
            print("✗ アーマチュアが見つかりません")

        # メッシュを検索（シェイプキー用）
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data.shape_keys:
                self.mesh = obj
                print(f"✓ シェイプキー付きメッシュを発見: {obj.name}")

                # シェイプキー名を表示
                print(f"  シェイプキー数: {len(obj.data.shape_keys.key_blocks)}")
                print(f"  シェイプキー名:")
                for i, key in enumerate(obj.data.shape_keys.key_blocks[:10]):
                    print(f"    {i+1}. {key.name}")
                break

        if not self.mesh:
            print("⚠ シェイプキーが見つかりません（表情は動きません）")

        print("=== アバター検索完了 ===\n")

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

        print(f"CaptyOU Receiver started on port {self.port}")
        print("=== データ受信待機中 ===\n")
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

        self.message_count += 1

        # 最初の数回と、その後は100回ごとにログを出力
        if self.message_count <= 5 or self.message_count % 100 == 0:
            print(f"[メッセージ #{self.message_count}] 受信: type={msg_type}")

        if msg_type == 'pose':
            # ポーズデータ
            self.pose_data = msg.get('rotations', {})
            if self.message_count <= 3:
                print(f"  ポーズデータ: {len(self.pose_data)} ボーン")
                for key in list(self.pose_data.keys())[:3]:
                    print(f"    - {key}: {self.pose_data[key]}")

        elif msg_type == 'expression':
            # 表情データ
            blend_shapes = msg.get('blend_shapes', {})
            self.expression_data.update(blend_shapes)
            if self.message_count <= 3:
                print(f"  表情データ: {len(blend_shapes)} ブレンドシェイプ")
                for key in list(blend_shapes.keys())[:3]:
                    print(f"    - {key}: {blend_shapes[key]:.2f}")

    def _update_avatar(self):
        """アバターを更新（メインスレッド）"""
        if not self.running:
            return None  # タイマーを停止

        self.update_count += 1

        # 最初の数回だけログ出力
        if self.update_count <= 5:
            print(f"[更新 #{self.update_count}] アバター更新中...")

        # ポーズを適用
        pose_result = self._apply_pose()

        # 表情を適用
        expr_result = self._apply_expressions()

        if self.update_count <= 5:
            print(f"  ポーズ適用: {pose_result}, 表情適用: {expr_result}")

        return 0.033  # 30 FPS

    def _apply_pose(self):
        """ポーズをアバターに適用"""
        if not self.armature:
            return "アーマチュアなし"

        if not self.pose_data:
            return "データなし"

        try:
            # ポーズモードに切り替え
            bpy.context.view_layer.objects.active = self.armature

            applied_count = 0
            for bone_key, rotation in self.pose_data.items():
                # ボーン名を取得
                bone_name = self._get_vrm_bone_name(bone_key)

                if bone_name and bone_name in self.armature.pose.bones:
                    bone = self.armature.pose.bones[bone_name]
                    # オイラー角を適用
                    bone.rotation_euler = Euler(rotation, 'XYZ')
                    applied_count += 1
                elif self.update_count <= 3:
                    # 最初の数回だけ、マッピングできなかったボーンを表示
                    print(f"  ⚠ ボーン '{bone_key}' → '{bone_name}' が見つかりません")

            return f"{applied_count}個適用"
        except Exception as e:
            return f"エラー: {e}"

    def _apply_expressions(self):
        """表情（シェイプキー）をアバターに適用"""
        if not self.mesh or not self.mesh.data.shape_keys:
            return "シェイプキーなし"

        try:
            shape_keys = self.mesh.data.shape_keys.key_blocks

            # VRM標準シェイプキーにマッピング
            mapping = {
                'eye_blink_left': 'Blink_L',
                'eye_blink_right': 'Blink_R',
                'jaw_open': 'A',
                'mouth_smile_left': 'Joy',
                'mouth_smile_right': 'Joy',
            }

            applied_count = 0
            for exp_key, shape_name in mapping.items():
                if exp_key in self.expression_data and shape_name in shape_keys:
                    value = self.expression_data[exp_key]

                    # Joy（笑顔）は左右の平均
                    if shape_name == 'Joy':
                        value = (self.expression_data.get('mouth_smile_left', 0) +
                                self.expression_data.get('mouth_smile_right', 0)) / 2

                    shape_keys[shape_name].value = value
                    applied_count += 1
                elif self.update_count <= 3:
                    # 最初の数回だけ、マッピングできなかったシェイプキーを表示
                    if exp_key in self.expression_data:
                        print(f"  ⚠ シェイプキー '{exp_key}' → '{shape_name}' が見つかりません")

            return f"{applied_count}個適用"
        except Exception as e:
            return f"エラー: {e}"

    def _get_vrm_bone_name(self, bone_key):
        """CaptyOUのボーンキーからVRMボーン名を取得"""
        # VRMボーン名マッピング
        vrm_mapping = {
            'head': 'head',
            'neck': 'neck',
            'spine': 'spine',
            'left_arm': 'leftUpperArm',
            'right_arm': 'rightUpperArm',
            'left_forearm': 'leftLowerArm',
            'right_forearm': 'rightLowerArm',
            'left_hand': 'leftHand',
            'right_hand': 'rightHand',
            'left_up_leg': 'leftUpperLeg',
            'right_up_leg': 'rightUpperLeg',
            'left_leg': 'leftLowerLeg',
            'right_leg': 'rightLowerLeg',
            'left_foot': 'leftFoot',
            'right_foot': 'rightFoot',
        }

        return vrm_mapping.get(bone_key)


# グローバル変数
receiver = None


def start_receiver(port=9000):
    """受信を開始"""
    global receiver

    if receiver and receiver.running:
        print("Receiver already running")
        return

    receiver = CaptyOUReceiver(port=port)
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
    bl_label = "CaptyOU Receiver"
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
