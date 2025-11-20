# Blender クイックスタートガイド

VRMアバターをBlenderでリアルタイムに動かすための最短セットアップガイドです。

## 重要な実行順序

**必ず以下の順番で実行してください:**

```
1. Blenderを起動
2. VRMアバターをインポート
3. captyou_receiver.pyをBlenderで実行 ← サーバーとして待機
4. uv run examples/blender_debug.py ← クライアントとして接続
```

## ステップ1: Blenderの準備

### 1.1 VRMアドオンのインストール

1. [VRM Add-on for Blender](https://github.com/saturday06/VRM_Addon_for_Blender/releases)から最新版をダウンロード
2. Blender → Edit → Preferences → Add-ons → Install
3. ダウンロードしたZIPファイルを選択
4. "VRM"で検索してチェックを入れる

### 1.2 VRMアバターのインポート

1. File → Import → VRM (.vrm)
2. VRMファイルを選択してインポート

## ステップ2: Blender側のスクリプト設定

### 2.1 スクリプトをBlenderにコピー

**方法1: Text Editorで直接開く**

1. Blender → Scripting ワークスペース
2. Text Editor → Open Text
3. `/path/to/captyou/blender/captyou_receiver.py` を開く

**方法2: コピー&ペースト**

1. Blender → Scripting ワークスペース
2. Text Editor → New
3. `blender/captyou_receiver.py`の内容をコピー&ペースト
4. Text → Save As → 名前を付けて保存

### 2.2 スクリプトを実行

1. Text Editor で `captyou_receiver.py` が開いていることを確認
2. **"Run Script"ボタンをクリック**
3. Blenderのコンソールに以下が表示されることを確認:
   ```
   Found armature: Armature
   Found mesh with shape keys: Body
   Waiting for connection on port 9000...
   ```

**これでBlender側の準備完了です！**

## ステップ3: CaptyOU側の実行

### 3.1 デバッグモードで接続テスト

ターミナルで以下を実行:

```bash
cd /path/to/captyou
uv run examples/blender_debug.py
```

**表示される確認:**
- ✅ Blenderに接続しました!
- ✅ カメラを開きました
- ✅ ポーズを検出しました!
- ✅ 顔を検出しました!
- ✅ データを送信しました

**Blender側の確認:**
- コンソールに "Connected: ('127.0.0.1', xxxxx)" と表示
- **VRMアバターが動く!**

### 3.2 通常モードで実行

デバッグが成功したら、通常のデモを実行:

```bash
uv run examples/blender_demo.py
```

## トラブルシューティング

### 問題1: "Error: No armature found in scene"

**原因:** VRMアバターがインポートされていない

**解決方法:**
1. File → Import → VRM (.vrm) でアバターをインポート
2. Outlinerでアーマチュアオブジェクトが存在することを確認
3. スクリプトを再実行

### 問題2: "Failed to connect to Blender"

**原因:** Blender側のスクリプトが実行されていない、または順序が逆

**解決方法:**
1. **まずBlenderでスクリプトを実行**（サーバーとして起動）
2. コンソールに "Waiting for connection..." が表示されることを確認
3. **その後**にPythonスクリプトを実行（クライアントとして接続）

**正しい順序:**
```
Blender (サーバー) → 待機 → Python (クライアント) → 接続
```

**間違った順序:**
```
Python (クライアント) → 接続失敗 ← Blender (サーバー) まだ起動していない
```

### 問題3: 接続はするがアバターが動かない

**確認事項:**

1. **VRMボーン名の確認:**
   ```python
   # Blenderのコンソールで実行
   armature = bpy.data.objects['Armature']
   for bone in armature.pose.bones:
       print(bone.name)
   ```

2. **シェイプキーの確認:**
   ```python
   # Blenderのコンソールで実行
   mesh = bpy.context.active_object
   if mesh.data.shape_keys:
       for key in mesh.data.shape_keys.key_blocks:
           print(key.name)
   ```

3. **Blenderのビューモード:**
   - Object Mode または Pose Mode になっているか確認
   - Viewport Shading → Solid または Material Preview

### 問題4: ポートが使用中

**エラー:** "OSError: [Errno 48] Address already in use"

**解決方法:**
```bash
# macOSでポートを確認
lsof -i :9000

# プロセスを終了
kill -9 [PID]
```

または、Blenderを再起動してスクリプトを再実行

## 動作確認のチェックリスト

### Blender側
- [ ] VRMアバターがインポートされている
- [ ] captyou_receiver.pyが実行されている
- [ ] コンソールに "Waiting for connection..." と表示
- [ ] コンソールに "Connected: ..." と表示（接続後）

### CaptyOU側
- [ ] カメラが起動している
- [ ] プレビューウィンドウが表示されている
- [ ] ポーズのランドマークが表示されている
- [ ] 顔のランドマークが表示されている
- [ ] "Blender: Connected" と表示されている

### 動作確認
- [ ] 頭を動かすとアバターの頭が動く
- [ ] 腕を動かすとアバターの腕が動く
- [ ] まばたきするとアバターの目が閉じる
- [ ] 口を開けるとアバターの口が開く

## ポート番号の変更

デフォルトはポート9000ですが、変更する場合:

**Blender側:**
```python
# captyou_receiver.py の最終行を変更
start_receiver(port=9001)  # 好きなポート番号
```

**CaptyOU側:**
```python
blender_avatar = BlenderAvatar(port=9001)  # 同じポート番号
```

## パフォーマンス最適化

### Blenderの設定

1. **レンダーエンジン:** Eevee（リアルタイム向け）
2. **サンプリング:** 低め（16-32）
3. **ビューポート設定:**
   - Bloom: オフ（軽量化）
   - Screen Space Reflections: オフ（軽量化）
   - Ambient Occlusion: 低設定

### CaptyOUの設定

解像度を下げて高速化:
```python
camera = CameraCapture(
    width=640,   # 1280 → 640
    height=480,  # 720 → 480
    fps=30
)
```

## 次のステップ

動作確認ができたら:

1. **Unity統合:** `UNITY_SETUP.md` を参照
2. **Neural Engine最適化:** `NEURAL_ENGINE.md` を参照
3. **配信設定:** OBSとの連携
4. **音声変換:** Voice Conversion機能の追加

## サポート

問題が解決しない場合:

1. Blenderのバージョンを確認（3.0以降推奨）
2. VRMアドオンのバージョンを確認
3. ログを確認:
   - Blender: Window → Toggle System Console
   - CaptyOU: ターミナル出力

詳細なドキュメント: `BLENDER_SETUP.md`
