# VRoidアバターが動かない問題のデバッグ手順

**問題:** 接続は成功しているが、Blender上のVRMアバターが動かない

**状況:**
- ✅ Blender接続成功
- ✅ ポーズ・表情データ送信成功
- ✅ ボーン名・シェイプキー名取得済み
- ❌ アバターが動かない

---

## 🔍 デバッグステップ

### ステップ1: 手動でシェイプキーが動くか確認

**目的:** VRMアドオンとシェイプキーが正常に動作するか確認

**Blenderのコンソールで実行:**

```python
import bpy

# メッシュを取得
mesh = bpy.data.objects['Face']
shape_keys = mesh.data.shape_keys.key_blocks

# 全シェイプキーをリセット
for key in shape_keys:
    key.value = 0.0

# 左目を閉じる (0.0 → 1.0 で閉じる)
shape_keys['Fcl_EYE_Close_L'].value = 1.0

# 右目を閉じる
shape_keys['Fcl_EYE_Close_R'].value = 1.0

# 口を開ける
shape_keys['Fcl_MTH_A'].value = 1.0

# 笑顔にする
shape_keys['Fcl_MTH_Joy'].value = 0.8
```

**期待される結果:**
- アバターの左目が閉じる
- アバターの右目が閉じる
- アバターの口が開く
- アバターが笑顔になる

**結果判定:**
- ✅ 動いた → スクリプトの適用方法に問題。ステップ3へ
- ❌ 動かない → VRMアドオンの設定に問題。ステップ2へ

---

### ステップ2: VRMアドオンの設定確認

**確認項目:**

1. **VRMアドオンが有効か**
   - Edit → Preferences → Add-ons
   - "VRM" で検索
   - VRM Add-on for Blender にチェックが入っているか

2. **VRMアバターが正しくインポートされているか**
   - File → Import → VRM (.vrm) でインポートしたか
   - 別の方法（FBX, GLB など）でインポートしていないか

3. **メッシュの選択**
   ```python
   import bpy

   # シーン内の全メッシュオブジェクトを表示
   for obj in bpy.data.objects:
       if obj.type == 'MESH':
           print(f"Mesh: {obj.name}")
           if obj.data.shape_keys:
               print(f"  Has shape keys: {len(obj.data.shape_keys.key_blocks)}")
   ```

   → 複数のメッシュがある場合、正しいメッシュを選択しているか確認

---

### ステップ3: ボーンの手動テスト

**目的:** ボーンが正常に動作するか確認

**Blenderのコンソールで実行:**

```python
import bpy
from mathutils import Euler

# アーマチュアを取得
armature = bpy.data.objects['Armature']

# アクティブにしてPose Modeに切り替え
bpy.context.view_layer.objects.active = armature
bpy.ops.object.mode_set(mode='POSE')

# 左腕を動かす
bone = armature.pose.bones['J_Bip_L_UpperArm']
bone.rotation_euler = Euler([1.0, 0.5, 0.0], 'XYZ')

# 右腕を動かす
bone = armature.pose.bones['J_Bip_R_UpperArm']
bone.rotation_euler = Euler([1.0, -0.5, 0.0], 'XYZ')

# 頭を動かす
bone = armature.pose.bones['J_Bip_C_Head']
bone.rotation_euler = Euler([0.0, 0.5, 0.0], 'XYZ')
```

**期待される結果:**
- アバターの左腕が上がる
- アバターの右腕が上がる
- アバターの頭が回転する

**結果判定:**
- ✅ 動いた → スクリプトの適用方法に問題。ステップ4へ
- ❌ 動かない → ボーンの命名規則や構造に問題

---

### ステップ4: デバッグ版スクリプトでログ確認

**Blenderで実行:**

1. `blender/captyou_receiver_debug.py` を開く
2. Run Script
3. 別ターミナルで `uv run examples/blender_demo.py` を実行
4. Blenderのコンソール出力を確認

**確認するログ:**

```
[メッセージ #1] 受信: type=pose
  ポーズデータ: 2 ボーン
    - left_arm: [...]
    - right_arm: [...]

[更新 #1] アバター更新中...
  ⚠ ボーン 'left_arm' → 'J_Bip_L_UpperArm' が見つかりません  ← これが出たら問題
  ポーズ適用: 2個適用  ← この数値が0なら問題
  表情適用: 3個適用  ← この数値が0なら問題
```

**判定:**
- "ポーズ適用: 0個" → ボーンマッピングが失敗
- "表情適用: 0個" → シェイプキーマッピングが失敗
- "X個適用" (X > 0) → 適用は成功しているのにアバターが動かない

---

### ステップ5: ビューポート更新の確認

**問題:** Blenderのビューポートが自動更新されていない可能性

**解決方法1: 手動更新を追加**

`captyou_receiver_vroid.py` の `_apply_pose()` 関数に以下を追加:

```python
def _apply_pose(self):
    """ポーズをアバターに適用"""
    if not self.armature or not self.pose_data:
        return

    # ポーズモードに切り替え
    bpy.context.view_layer.objects.active = self.armature

    for bone_key, rotation in self.pose_data.items():
        bone_name = self._get_vroid_bone_name(bone_key)

        if bone_name and bone_name in self.armature.pose.bones:
            bone = self.armature.pose.bones[bone_name]
            bone.rotation_euler = Euler(rotation, 'XYZ')

    # ビューポート更新を強制
    bpy.context.view_layer.update()  # ← これを追加
```

**解決方法2: タグ更新を追加**

```python
# ボーン適用後に追加
self.armature.update_tag()
bpy.context.view_layer.update()
```

---

### ステップ6: モードの確認

**問題:** Blenderが間違ったモードになっている可能性

**確認:**

```python
import bpy

# 現在のモードを確認
print(f"Current mode: {bpy.context.mode}")

# Pose Modeに強制切り替え
armature = bpy.data.objects['Armature']
bpy.context.view_layer.objects.active = armature
bpy.ops.object.mode_set(mode='POSE')

print(f"New mode: {bpy.context.mode}")
```

**期待される出力:**
```
Current mode: OBJECT  または  POSE
New mode: POSE
```

---

### ステップ7: 回転の適用方法の変更

**問題:** `rotation_euler` ではなく `rotation_quaternion` が必要な可能性

**修正案:**

```python
from mathutils import Euler, Quaternion

def _apply_pose(self):
    if not self.armature or not self.pose_data:
        return

    bpy.context.view_layer.objects.active = self.armature

    for bone_key, rotation in self.pose_data.items():
        bone_name = self._get_vroid_bone_name(bone_key)

        if bone_name and bone_name in self.armature.pose.bones:
            bone = self.armature.pose.bones[bone_name]

            # オイラー角をクォータニオンに変換
            euler = Euler(rotation, 'XYZ')
            quat = euler.to_quaternion()

            # ボーンの回転モードを確認して適用
            if bone.rotation_mode == 'QUATERNION':
                bone.rotation_quaternion = quat
            else:
                bone.rotation_euler = euler
```

---

## 🧪 テスト用の簡易スクリプト

以下のスクリプトをBlenderで実行して、アニメーションループをテスト:

```python
import bpy
import time
import math
from mathutils import Euler

armature = bpy.data.objects['Armature']
mesh = bpy.data.objects['Face']

bpy.context.view_layer.objects.active = armature
bpy.ops.object.mode_set(mode='POSE')

# 10秒間アニメーション
for i in range(300):
    t = i / 30.0  # 時間 (秒)

    # 腕を上下に動かす
    angle = math.sin(t * 2) * 0.5
    bone_l = armature.pose.bones['J_Bip_L_UpperArm']
    bone_r = armature.pose.bones['J_Bip_R_UpperArm']
    bone_l.rotation_euler = Euler([angle, 0, 0], 'XYZ')
    bone_r.rotation_euler = Euler([angle, 0, 0], 'XYZ')

    # まばたき
    blink = abs(math.sin(t * 4))
    if mesh.data.shape_keys:
        shape_keys = mesh.data.shape_keys.key_blocks
        shape_keys['Fcl_EYE_Close_L'].value = blink
        shape_keys['Fcl_EYE_Close_R'].value = blink

    # 更新
    bpy.context.view_layer.update()

    # 待機 (本来はbpy.app.timersを使うべき)
    time.sleep(0.033)

print("Test animation complete")
```

**期待される結果:**
- アバターの腕が上下に動く
- アバターがまばたきする

---

## 📋 チェックリスト

デバッグ時に以下を確認:

- [ ] VRMアドオンが有効
- [ ] VRMアバターが正しくインポートされている
- [ ] 手動でシェイプキーを変更すると動く
- [ ] 手動でボーンを変更すると動く
- [ ] デバッグ版スクリプトで "X個適用" (X > 0) と表示される
- [ ] Blenderが Pose Mode になっている
- [ ] ビューポート更新が呼ばれている
- [ ] ボーンの回転モードが正しい

---

## 🔧 修正候補スクリプト

上記のデバッグ結果を踏まえて、改良版を作成できます。
デバッグ結果を教えてください:

1. **手動テストの結果** (ステップ1, 3)
2. **デバッグログの "X個適用"** (ステップ4)
3. **現在のモード** (ステップ6)

これらの情報があれば、的確な修正ができます。

---

**次回のClaude Codeセッション開始時:**
1. `CLAUDE.md` でコンテキストを確認
2. このファイルでデバッグ状況を確認
3. デバッグ結果に基づいて修正を実施
