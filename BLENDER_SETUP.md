# Blender統合ガイド

CaptyOUからのポーズ・表情データをBlenderで受信してVRMアバターに反映する方法を説明します。

## 必要なもの

### 1. Blender環境
- **Blender 3.0以降**推奨
- プラットフォーム: macOS、Windows、Linux

### 2. VRMアドオン
- **VRM Add-on for Blender**（無料）
- [Saturday06/VRM_Addon_for_Blender](https://github.com/saturday06/VRM_Addon_for_Blender)

### 3. VRMアバター
- VRM 0.x または VRM 1.0形式のアバター
- VRoid Studioで作成したアバターなど

## セットアップ手順

### ステップ1: VRMアドオンのインストール

#### 方法1: GitHubからダウンロード

1. [Releases](https://github.com/saturday06/VRM_Addon_for_Blender/releases)から最新版をダウンロード
2. Blender → Edit → Preferences → Add-ons
3. Install... → ダウンロードしたZIPファイルを選択
4. "VRM" で検索してチェックを入れる

#### 方法2: Blenderの拡張機能から

Blender 4.2以降:
1. Edit → Preferences → Get Extensions
2. "VRM" で検索
3. Install

### ステップ2: VRMアバターのインポート

1. File → Import → VRM (.vrm)
2. VRMファイルを選択
3. Import

アバターがシーンに読み込まれます。

### ステップ3: CaptyOU受信スクリプトの作成

Blenderの Text Editor で以下のスクリプトを作成します。

#### `captyou_receiver.py`

```python
import bpy
import socket
import json
import threading
import mathutils
from mathutils import Vector, Euler

class CaptyOUReceiver:
    """
    CaptyOUからデータを受信してBlenderアバターを制御
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
            'smile_left': 0.0,
            'smile_right': 0.0,
        }

    def find_avatar(self):
        """シーン内のVRMアバターを検索"""
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
            return False

        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()

        # タイマーで定期的にアバターを更新
        bpy.app.timers.register(self._update_avatar, first_interval=0.033)  # 30 FPS

        print(f"CaptyOU Receiver started on port {self.port}")
        return True

    def stop(self):
        """受信を停止"""
        self.running = False
        if self.socket:
            self.socket.close()
        print("CaptyOU Receiver stopped")

    def _receive_loop(self):
        """ソケットでデータ受信（バックグラウンドスレッド）"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('localhost', self.port))
            self.socket.listen(1)

            print(f"Waiting for connection on port {self.port}...")

            conn, addr = self.socket.accept()
            print(f"Connected: {addr}")

            buffer = ""
            while self.running:
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
            print(f"Socket error: {e}")
        finally:
            if self.socket:
                self.socket.close()

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
            # ボーン名を取得
            bone_name = self._get_vrm_bone_name(bone_key)

            if bone_name and bone_name in self.armature.pose.bones:
                bone = self.armature.pose.bones[bone_name]

                # オイラー角を適用
                bone.rotation_euler = Euler(rotation, 'XYZ')

    def _apply_expressions(self):
        """表情（シェイプキー）をアバターに適用"""
        if not self.mesh or not self.mesh.data.shape_keys:
            return

        shape_keys = self.mesh.data.shape_keys.key_blocks

        # VRM標準シェイプキーにマッピング
        mapping = {
            'eye_blink_left': 'Blink_L',
            'eye_blink_right': 'Blink_R',
            'jaw_open': 'A',
            'smile_left': 'Joy',
            'smile_right': 'Joy',
        }

        for exp_key, shape_name in mapping.items():
            if exp_key in self.expression_data and shape_name in shape_keys:
                value = self.expression_data[exp_key]

                # Joy（笑顔）は左右の平均
                if shape_name == 'Joy':
                    value = (self.expression_data.get('smile_left', 0) +
                            self.expression_data.get('smile_right', 0)) / 2

                shape_keys[shape_name].value = value

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
```

### ステップ4: スクリプトの実行

#### 方法1: Text Editorから実行

1. Blender → Scripting ワークスペース
2. Text Editor → Open → `captyou_receiver.py`
3. Run Script ボタンをクリック

#### 方法2: UIパネルから実行

1. スクリプトを実行すると、3D Viewportの右側に「CaptyOU」パネルが表示されます
2. "Start CaptyOU Receiver" ボタンをクリック

### ステップ5: CaptyOUとの接続

#### Blender側の準備
```python
# Python Consoleで実行
import captyou_receiver
captyou_receiver.start_receiver(port=9000)
```

#### CaptyOU側の設定

`src/avatar/blender_integration.py`を使用：

```python
from src.camera.capture import CameraCapture
from src.pose.estimator import PoseEstimator
from src.face.expression import FaceExpression
from src.avatar.blender_integration import BlenderAvatar

# カメラとエスティメータを初期化
camera = CameraCapture()
pose_estimator = PoseEstimator()
face_estimator = FaceExpression()

# Blenderアバターに接続
blender_avatar = BlenderAvatar(host="localhost", port=9000, use_socket=True)
blender_avatar.connect()

# リアルタイム処理
camera.open()
while True:
    ret, frame = camera.read()
    if not ret:
        break

    pose_data = pose_estimator.process(frame)
    face_data = face_estimator.process(frame)

    if pose_data:
        blender_avatar.update_pose(pose_data)

    if face_data:
        blender_avatar.update_expression(face_data)
```

## VRMシェイプキーの確認

Blenderで使用可能なシェイプキーを確認：

```python
import bpy

# メッシュを選択
mesh = bpy.context.active_object

if mesh.data.shape_keys:
    for key in mesh.data.shape_keys.key_blocks:
        print(f"Shape Key: {key.name}")
```

VRM標準シェイプキー：
- `Blink_L` - 左目を閉じる
- `Blink_R` - 右目を閉じる
- `A` - あ（口を開ける）
- `I` - い
- `U` - う
- `E` - え
- `O` - お
- `Joy` - 笑顔
- `Angry` - 怒り
- `Sorrow` - 悲しみ
- `Fun` - 楽しい

## リアルタイムレンダリング

### Eeveeエンジンの設定

リアルタイム表示のために：

1. Render Properties → Render Engine → Eevee
2. Viewport Shading → Material Preview または Rendered
3. Eevee設定:
   - Bloom: オン（発光効果）
   - Screen Space Reflections: オン（反射）
   - Ambient Occlusion: オン（影）

### アニメーション録画

Blenderでアニメーションとして録画：

```python
import bpy

# キーフレームを自動記録
bpy.context.scene.tool_settings.use_keyframe_insert_auto = True

# 再生を開始
bpy.ops.screen.animation_play()
```

## レンダリング出力

### リアルタイムレンダリング

```python
import bpy

# OpenGL レンダリング（高速）
bpy.ops.render.opengl(animation=True, view_context=True)
```

### 高品質レンダリング

```python
# Cyclesエンジンで高品質レンダリング
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 128  # サンプル数

# レンダリング
bpy.ops.render.render(animation=True)
```

## トラブルシューティング

### データが受信されない

1. **ポート番号を確認**
   ```python
   # Blender側
   start_receiver(port=9000)

   # CaptyOU側
   BlenderAvatar(port=9000)
   ```

2. **ファイアウォールを確認**
   ```bash
   # macOS
   sudo lsof -i :9000  # ポートが使用中か確認
   ```

3. **接続ログを確認**
   ```python
   # Blenderのコンソールに表示される
   # "Connected: ..." というメッセージを確認
   ```

### アバターが動かない

1. **アーマチュアを確認**
   ```python
   # Outlinerでアーマチュアオブジェクトを確認
   # Object Mode → Pose Mode に切り替えられるか確認
   ```

2. **ボーン名を確認**
   ```python
   armature = bpy.data.objects['Armature']
   for bone in armature.pose.bones:
       print(bone.name)  # すべてのボーン名を出力
   ```

3. **VRMインポートを確認**
   - 正しくVRMアドオンでインポートしたか
   - エラーメッセージがないか確認

### シェイプキーが動かない

1. **シェイプキーの存在確認**
   ```python
   mesh = bpy.context.active_object
   if mesh.data.shape_keys:
       for key in mesh.data.shape_keys.key_blocks:
           print(key.name)
   ```

2. **値の範囲を確認**
   ```python
   # シェイプキーの値は0.0～1.0
   # スクリプトで正しく設定されているか確認
   ```

## 高度な使用方法

### カメラ追従

アバターの頭にカメラを追従：

```python
import bpy

# カメラを作成
camera = bpy.data.objects.get('Camera')
armature = bpy.data.objects.get('Armature')

# 頭ボーンを取得
head_bone = armature.pose.bones.get('head')

# カメラにコンストレイントを追加
constraint = camera.constraints.new('COPY_LOCATION')
constraint.target = armature
constraint.subtarget = 'head'
```

### ライティング

3点照明のセットアップ：

```python
import bpy
import math

def create_three_point_lighting(target):
    """3点照明を作成"""

    # キーライト（メイン）
    key_light = bpy.data.lights.new('KeyLight', 'AREA')
    key_light.energy = 300
    key_obj = bpy.data.objects.new('KeyLight', key_light)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = (2, -2, 3)
    key_obj.rotation_euler = (math.radians(60), 0, math.radians(45))

    # フィルライト（補助）
    fill_light = bpy.data.lights.new('FillLight', 'AREA')
    fill_light.energy = 100
    fill_obj = bpy.data.objects.new('FillLight', fill_light)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (-2, -1, 2)
    fill_obj.rotation_euler = (math.radians(45), 0, math.radians(-45))

    # バックライト（輪郭）
    back_light = bpy.data.lights.new('BackLight', 'AREA')
    back_light.energy = 200
    back_obj = bpy.data.objects.new('BackLight', back_light)
    bpy.context.collection.objects.link(back_obj)
    back_obj.location = (0, 2, 2)
    back_obj.rotation_euler = (math.radians(45), 0, math.radians(180))
```

## 配信への統合

### OBSとの連携

1. **Blenderをウィンドウキャプチャ**
   - OBS → Sources → Window Capture
   - Blenderのビューポートを選択

2. **または仮想カメラ**
   - OBS Virtual Cameraプラグインを使用

### 録画設定

```python
import bpy

# 出力設定
bpy.context.scene.render.filepath = "//output/"
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.fps = 30
```

## 参考資料

- [VRM Add-on for Blender](https://github.com/saturday06/VRM_Addon_for_Blender)
- [Blender Python API](https://docs.blender.org/api/current/)
- [VRM Specification](https://vrm.dev/en/)
- [Blender for VTuber](https://github.com/topics/blender-vtuber)

## サンプルプロジェクト

完全なサンプルプロジェクト（準備中）：
- Blenderファイル（.blend）
- セットアップ済みスクリプト
- サンプルVRMアバター
