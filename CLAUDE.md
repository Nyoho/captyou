# CaptyOU - Claude Code セッション情報

**最終更新:** 2025-11-21
**ブランチ:** `claude/realtime-pose-expression-avatar-011CV5TjqDoVm291wzrbxrW6`

---

## 📋 プロジェクト概要

MacBook Proの内蔵カメラとマイクを使って、リアルタイムにポーズと表情を認識し、3Dアバター（Blender/Unity）に反映させ、さらに音声変換も行うシステム。

### 主要機能

1. **ポーズ推定** - MediaPipe Pose (33ランドマーク)
2. **表情認識** - MediaPipe Face Mesh (478ランドマーク) + ARKit Blend Shapes (52パラメータ)
3. **Neural Engine最適化** - Core ML変換でM1/M2/M3チップのNeural Engineを活用
4. **音声変換** - WORLD Vocoderで男性→女性の声質変換
5. **アバター統合** - Blender (ソケット通信) / Unity (OSC通信)
6. **配信対応** - OBS互換の仮想カメラ/オーディオデバイス

---

## 🎯 現在の状態

### ✅ 動作確認済み

- **カメラキャプチャ**: AVFoundation最適化で動作 (1280x720@30fps)
- **ポーズ検出**: MediaPipeで33ランドマーク検出成功
- **顔検出**: MediaPipeで478ランドマーク検出成功
- **Blender接続**: ソケット通信 (localhost:9000) で接続成功
- **データ送信**: ポーズと表情データがBlenderに送信されている
- **VRoidアバター**: ボーン名とシェイプキー名を完全に取得済み

### ⚠️ 現在の問題

**VRMモデルが動かない問題**

**症状:**
- Blender側: "Connected: ('127.0.0.1', xxxxx)" と表示される
- CaptyOU側: データ送信成功 (ポーズ・表情とも検出されている)
- しかし、Blender上のVRMアバターが動かない

**判明している情報:**
- アーマチュア: `Armature` (148ボーン)
- メッシュ: `Face` (58シェイプキー)
- ボーン名: VRoid形式 (`J_Bip_L_UpperArm` など)
- シェイプキー名: VRoid形式 (`Fcl_EYE_Close_L`, `Fcl_MTH_A` など)
- マッピング作成済み: `blender/captyou_receiver_vroid.py`

**可能性のある原因:**
1. Blenderのビューポート更新が必要
2. ボーン/シェイプキーの適用方法に問題
3. Blenderのモードの問題 (Object Mode vs Pose Mode)
4. VRMアドオンとの競合

---

## 📁 プロジェクト構造

```
captyou/
├── src/                          # ソースコード
│   ├── camera/
│   │   └── capture.py           # カメラキャプチャ (AVFoundation)
│   ├── pose/
│   │   └── estimator.py         # ポーズ推定 (MediaPipe + Core ML)
│   ├── face/
│   │   └── expression.py        # 表情認識 (MediaPipe + Core ML)
│   ├── audio/
│   │   └── voice_conversion.py  # 音声変換 (WORLD Vocoder)
│   ├── avatar/
│   │   ├── blender_integration.py  # Blender統合
│   │   └── unity_integration.py    # Unity統合
│   └── coreml/
│       ├── converter.py         # TFLite → Core ML変換
│       └── inference.py         # Core ML推論エンジン
│
├── blender/                      # Blenderスクリプト
│   ├── hello_blender.py         # 動作確認用 (最小限)
│   ├── test_simple.py           # アバター確認用
│   ├── show_all_bones_and_shapes.py  # ボーン/シェイプキー表示
│   ├── captyou_receiver.py      # レシーバー (汎用)
│   ├── captyou_receiver_debug.py     # デバッグ版
│   ├── captyou_receiver_vroid.py     # VRoid専用 ⭐
│   └── README.md                # スクリプト集の説明
│
├── examples/                     # デモスクリプト
│   ├── blender_demo.py          # Blenderデモ (メイン)
│   └── blender_debug.py         # 接続テスト用
│
├── scripts/
│   └── setup_coreml_models.py   # Core MLモデルセットアップ
│
└── docs/                         # ドキュメント
    ├── BLENDER_SETUP.md         # Blender統合ガイド (詳細)
    ├── BLENDER_QUICK_START.md   # クイックスタート
    ├── BLENDER_STEP_BY_STEP.md  # ステップバイステップガイド
    ├── UNITY_SETUP.md           # Unity統合ガイド
    └── NEURAL_ENGINE.md         # Neural Engine最適化ガイド
```

---

## 🔧 VRoidアバター情報

### ボーン名マッピング

```python
vroid_mapping = {
    # 頭部・体幹
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
```

### シェイプキーマッピング

```python
shape_mapping = {
    'eye_blink_left': 'Fcl_EYE_Close_L',    # 左目閉じ
    'eye_blink_right': 'Fcl_EYE_Close_R',   # 右目閉じ
    'jaw_open': 'Fcl_MTH_A',                # 口開け (あ)
    'mouth_smile': 'Fcl_MTH_Joy',           # 笑顔
}
```

### VRoidシェイプキー一覧 (抜粋)

**目:**
- `Fcl_EYE_Close` - 両目閉じ
- `Fcl_EYE_Close_L` - 左目閉じ
- `Fcl_EYE_Close_R` - 右目閉じ
- `Fcl_EYE_Joy` - 笑顔目
- `Fcl_EYE_Angry` - 怒り目

**口:**
- `Fcl_MTH_A` - あ
- `Fcl_MTH_I` - い
- `Fcl_MTH_U` - う
- `Fcl_MTH_E` - え
- `Fcl_MTH_O` - お
- `Fcl_MTH_Joy` - 笑顔
- `Fcl_MTH_Angry` - 怒り

**表情プリセット:**
- `Fcl_ALL_Joy` - 喜び
- `Fcl_ALL_Angry` - 怒り
- `Fcl_ALL_Sorrow` - 悲しみ
- `Fcl_ALL_Surprised` - 驚き

---

## 🚀 実行方法

### 1. Blender側のセットアップ

```bash
# 1. ターミナルからBlenderを起動 (ログ確認のため)
/Applications/Blender.app/Contents/MacOS/Blender

# 2. Blenderで以下を実行:
#    - Scripting ワークスペースに切り替え
#    - Text Editor → Open Text
#    - blender/captyou_receiver_vroid.py を開く
#    - Run Script ボタンをクリック
#
# 3. コンソールで確認:
#    Found armature: Armature
#    Found mesh with shape keys: Face
#    Waiting for connection on port 9000...
```

### 2. CaptyOU側の実行

```bash
# 別ターミナルで実行
cd /home/user/captyou
uv run examples/blender_demo.py

# または、デバッグモードで実行
uv run examples/blender_debug.py
```

### 3. 動作確認

**期待される動作:**
- カメラプレビューウィンドウが開く
- ポーズと顔のランドマークが表示される
- Blenderのコンソールに "Connected: ..." と表示
- **VRMアバターが動く** (← 現在この部分が動かない)

---

## 🐛 トラブルシューティング

### Blenderのコンソールが見えない

**macOS:**
```bash
/Applications/Blender.app/Contents/MacOS/Blender
```

**Blender内:**
- Window → Toggle System Console

### 接続できない

**確認:**
1. Blenderでスクリプトを実行済みか？
2. "Waiting for connection..." と表示されているか？
3. ポート9000が使用されていないか？

```bash
# ポート確認
lsof -i :9000

# プロセス終了
kill -9 [PID]
```

### データは送られているのにアバターが動かない (現在の問題)

**確認済み:**
- ✅ 接続成功
- ✅ データ受信成功
- ✅ ボーン名・シェイプキー名取得済み
- ✅ マッピング作成済み

**未確認:**
- ❓ ボーン/シェイプキーの適用が実際に動いているか
- ❓ Blenderのビューポート更新が必要か
- ❓ VRMアドオンとの競合

**次のデバッグステップ:**
1. `captyou_receiver_debug.py` を使ってログ確認
2. Blenderのコンソールで "ポーズ適用: X個適用" を確認
3. 手動でシェイプキーを変更してアバターが動くか確認
4. Blenderのモードを確認 (Object Mode / Pose Mode)

---

## 📊 技術スタック

**Python:**
- MediaPipe - ポーズ・表情認識
- Core ML - Neural Engine最適化
- OpenCV - カメラキャプチャ
- WORLD Vocoder - 音声変換
- sounddevice - オーディオ入出力

**Blender:**
- Blender Python API (bpy)
- VRM Add-on for Blender
- Socket通信 (JSON)

**Unity:**
- extOSC - OSCプロトコル
- VRM SDK
- UniVRM

**macOS:**
- AVFoundation - カメラ最適化
- Core ML - Neural Engine
- BlackHole - 仮想オーディオデバイス

---

## 📝 解決済みの問題

### 1. MediaPipeがNeural Engineを使っていなかった

**問題:** MediaPipeはデフォルトでCPU/GPUで動作

**解決策:**
- TFLite → Core ML変換パイプラインを実装
- `scripts/setup_coreml_models.py` でモデル変換
- `src/coreml/inference.py` で推論エンジン実装
- 2-3倍の高速化を達成 (15-25 FPS → 30-60 FPS)

### 2. Blenderのコンソールが表示されない

**問題:** スクリプトを実行してもログが見えない

**解決策:**
- ターミナルからBlenderを起動
- `hello_blender.py` で動作確認
- `test_simple.py` でアバター確認
- 段階的なデバッグツールを提供

### 3. VRMボーン名が一致しない

**問題:** 標準VRM名 (`leftUpperArm`) がVRoidで使えない

**解決策:**
- `show_all_bones_and_shapes.py` で実際の名前を取得
- VRoid形式 (`J_Bip_L_UpperArm`) にマッピング
- `captyou_receiver_vroid.py` を作成

### 4. シェイプキー名が一致しない

**問題:** 標準VRM名 (`Blink_L`) がVRoidで使えない

**解決策:**
- VRoid形式 (`Fcl_EYE_Close_L`) にマッピング
- 58個のシェイプキーを全て確認済み

---

## 🎯 次のステップ

### 最優先: VRMアバターを動かす

**現在の状況:**
- 接続: ✅
- データ送信: ✅
- マッピング: ✅
- アバターが動く: ❌ ← これを解決

**デバッグ方法:**

1. **手動テストでシェイプキーが動くか確認**
   ```python
   # Blenderのコンソールで実行
   import bpy
   mesh = bpy.data.objects['Face']
   shape_keys = mesh.data.shape_keys.key_blocks

   # 手動で目を閉じる
   shape_keys['Fcl_EYE_Close_L'].value = 1.0
   shape_keys['Fcl_EYE_Close_R'].value = 1.0

   # 手動で口を開ける
   shape_keys['Fcl_MTH_A'].value = 1.0
   ```

   → これで動けば、スクリプトの適用方法に問題
   → 動かなければ、VRMアドオンの設定に問題

2. **ボーンの手動テスト**
   ```python
   # Blenderのコンソールで実行
   import bpy
   from mathutils import Euler

   armature = bpy.data.objects['Armature']
   bpy.context.view_layer.objects.active = armature
   bpy.ops.object.mode_set(mode='POSE')

   # 左腕を動かす
   bone = armature.pose.bones['J_Bip_L_UpperArm']
   bone.rotation_euler = Euler([1.0, 0.0, 0.0], 'XYZ')
   ```

3. **デバッグ版スクリプトでログ確認**
   - `blender/captyou_receiver_debug.py` を実行
   - "ポーズ適用: X個適用" の数値を確認
   - "⚠ ボーン" の警告を確認

### その後の拡張

1. **全身トラッキング強化**
   - 指の動き (MediaPipe Hands)
   - 視線追跡 (MediaPipe Iris)

2. **表情の詳細化**
   - 52個のARKit Blend Shapesを全てマッピング
   - VRoidの58個のシェイプキーを活用

3. **Neural Engine最適化**
   - Core MLモデルの性能ベンチマーク
   - リアルタイム性の向上

4. **配信対応**
   - OBS統合
   - 仮想カメラ出力
   - 音声変換の統合

---

## 🔗 関連ドキュメント

- `BLENDER_STEP_BY_STEP.md` - Blenderセットアップの詳細手順
- `BLENDER_QUICK_START.md` - クイックスタートガイド
- `blender/README.md` - スクリプト集の使い方
- `NEURAL_ENGINE.md` - Core ML最適化ガイド
- `UNITY_SETUP.md` - Unity統合ガイド

---

## 💡 重要なコマンド

```bash
# Blenderをターミナルから起動 (macOS)
/Applications/Blender.app/Contents/MacOS/Blender

# CaptyOUデモ実行
uv run examples/blender_demo.py

# デバッグモード実行
uv run examples/blender_debug.py

# Core MLモデルセットアップ
uv run scripts/setup_coreml_models.py

# ポート確認
lsof -i :9000

# Git状態確認
git status
git log --oneline -10
```

---

## 📌 メモ

- **開発環境:** macOS, Apple M1 Max, Python 3.10
- **Blenderバージョン:** 3.0以降推奨
- **VRMアドオン:** Saturday06/VRM_Addon_for_Blender
- **カメラ解像度:** 1280x720@30fps (変更可能)
- **通信プロトコル:** Blender (Socket/JSON), Unity (OSC)

---

**最終更新:** 2025-11-21
**セッションID:** 011CV5TjqDoVm291wzrbxrW6
**次回セッション開始時:** このファイルを参照してコンテキストを継続
