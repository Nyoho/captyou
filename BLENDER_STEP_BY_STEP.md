# Blender セットアップ完全ガイド

コンソールにメッセージが表示されない場合の解決方法を、ステップバイステップで説明します。

## ステップ0: Blenderのコンソールを表示する

### macOSの場合

**方法1: メニューから開く**
1. Blenderのメニューバー → **Window** → **Toggle System Console**

**方法2: ターミナルからBlenderを起動**
```bash
# Blenderをターミナルから起動すると、ターミナルにログが表示されます
/Applications/Blender.app/Contents/MacOS/Blender
```

この方法だと、Pythonスクリプトの`print()`出力がターミナルに表示されます。

### Windowsの場合

1. Blenderのメニューバー → **Window** → **Toggle System Console**
2. 別ウィンドウでコンソールが開きます

### Linuxの場合

ターミナルからBlenderを起動すると、自動的にログが表示されます：
```bash
blender
```

## ステップ1: テストスクリプトで確認

まず、簡単なテストスクリプトでBlenderが正しく動作するか確認します。

### 1.1 Blenderでテストスクリプトを開く

1. **Blenderを起動**

2. **Scriptingワークスペースに切り替え**
   - 上部のタブで「Scripting」をクリック

3. **テキストエディタでスクリプトを開く**
   - Text Editor（中央のエディタ部分）→ **Open Text** アイコンをクリック
   - または Text Editor上部の **Text** メニュー → **Open Text**

4. **ファイルを選択**
   - `/path/to/captyou/blender/test_simple.py` を開く
   - パスが分からない場合は以下で確認:
     ```bash
     cd /home/user/captyou
     pwd
     # → /home/user/captyou と表示される
     # → /home/user/captyou/blender/test_simple.py を開く
     ```

### 1.2 スクリプトを実行

1. **Run Scriptボタンをクリック**
   - Text Editor上部の **▶ Run Script** ボタン
   - または **Alt + P** キー

2. **コンソールを確認**
   - macOS: Window → Toggle System Console
   - または、ターミナルからBlenderを起動している場合は、ターミナルを確認

3. **期待される出力**
   ```
   ======================================================================
   CaptyOU Blender Test - スクリプトが実行されました！
   ======================================================================

   [テスト1] シーン内のオブジェクト:
     - Camera (type: CAMERA)
     - Light (type: LIGHT)
     - Cube (type: MESH)

   [テスト2] アーマチュアの検索:
     ✗ アーマチュアが見つかりません
     → VRMアバターをインポートしてください
   ```

### 1.3 問題が発生する場合

**何も表示されない場合:**
- コンソールが開いていない可能性があります
- ターミナルからBlenderを起動してみてください:
  ```bash
  /Applications/Blender.app/Contents/MacOS/Blender
  ```

**エラーが表示される場合:**
- エラーメッセージをコピーして確認してください
- Blenderのバージョンを確認（3.0以降が必要）

## ステップ2: VRMアバターをインポート

### 2.1 VRMアドオンのインストール（初回のみ）

1. **GitHubからダウンロード**
   - https://github.com/saturday06/VRM_Addon_for_Blender/releases
   - 最新版の`.zip`ファイルをダウンロード

2. **Blenderにインストール**
   - Edit → Preferences → Add-ons
   - **Install...** ボタンをクリック
   - ダウンロードした`.zip`ファイルを選択
   - 検索ボックスに「VRM」と入力
   - **VRM Add-on for Blender** にチェックを入れる
   - Preferencesを閉じる

### 2.2 VRMファイルをインポート

1. **VRMファイルを準備**
   - VRoid Studioで作成したアバター
   - または、テスト用のVRMファイルをダウンロード

2. **Blenderにインポート**
   - File → Import → **VRM (.vrm)**
   - VRMファイルを選択
   - **Import VRM** ボタンをクリック

3. **インポート完了を確認**
   - シーン内にアバターが表示される
   - Outliner（右上のパネル）に「Armature」オブジェクトが表示される

4. **再度テストスクリプトを実行**
   - `test_simple.py`を再度 Run Script
   - 今度は以下のように表示されるはず:
     ```
     [テスト2] アーマチュアの検索:
       ✓ アーマチュアを発見: Armature
       ボーン数: 55
       最初の5つのボーン:
         - Hips
         - Spine
         - Chest
         - UpperChest
         - Neck
     ```

## ステップ3: captyou_receiver.pyを実行

### 3.1 スクリプトを開く

1. **Text Editor** → **Open Text**
2. `/home/user/captyou/blender/captyou_receiver.py` を開く

### 3.2 スクリプトを実行

1. **Run Script** ボタンをクリック

2. **コンソールを確認**
   - 以下のメッセージが表示されるはず:
     ```
     Found armature: Armature
     Found mesh with shape keys: Body
     Waiting for connection on port 9000...
     ```

### 3.3 メッセージが表示されない場合

#### 問題A: "Error: No armature found in scene"

**原因:** VRMアバターがインポートされていない

**解決方法:**
1. ステップ2に戻ってVRMアバターをインポート
2. Outlinerで「Armature」オブジェクトが存在するか確認
3. スクリプトを再実行

#### 問題B: 何も表示されない

**原因1: コンソールが開いていない**

**解決方法:**
```bash
# ターミナルからBlenderを起動
/Applications/Blender.app/Contents/MacOS/Blender
```

**原因2: スクリプトにエラーがある**

**解決方法:**
1. エラーメッセージを確認
2. Blenderのバージョンを確認（3.0以降が必要）
3. スクリプトが正しくコピーされているか確認

#### 問題C: "OSError: [Errno 48] Address already in use"

**原因:** ポート9000が既に使用されている

**解決方法:**
```bash
# ポートを使用しているプロセスを確認
lsof -i :9000

# プロセスを終了
kill -9 [PID]

# またはBlenderを再起動
```

## ステップ4: CaptyOU側から接続

### 4.1 接続テスト

Blenderで "Waiting for connection..." と表示されたら、別のターミナルで:

```bash
cd /home/user/captyou
uv run examples/blender_debug.py
```

### 4.2 期待される動作

**Blender側:**
```
Waiting for connection on port 9000...
Connected: ('127.0.0.1', 54321)
```

**CaptyOU側:**
```
✅ Blenderに接続しました!
✅ カメラを開きました
✅ ポーズを検出しました!
✅ 顔を検出しました!
✅ データを送信しました
```

## トラブルシューティング チェックリスト

実行前に以下を確認してください:

- [ ] Blenderのバージョンは3.0以降
- [ ] VRMアドオンがインストールされている
- [ ] VRMアバターがシーンにインポートされている
- [ ] Outlinerに「Armature」オブジェクトが表示されている
- [ ] Blenderのコンソールが表示されている（または、ターミナルからBlenderを起動）
- [ ] test_simple.py が正しく動作する
- [ ] captyou_receiver.py を実行後、"Waiting for connection..." が表示される
- [ ] その後、uv run examples/blender_debug.py を実行

## よくある質問

**Q: Text Editorが見つかりません**

A: 上部のタブで「Scripting」ワークスペースに切り替えてください。中央の大きなエディタがText Editorです。

**Q: Open Textボタンが見つかりません**

A: Text Editor上部の **Text** メニュー → **Open Text** を選択してください。

**Q: Run Scriptボタンが見つかりません**

A: Text Editor上部の **▶** アイコンです。またはキーボードで **Alt + P** を押してください。

**Q: スクリプトを実行しても何も起こりません**

A: コンソールを確認してください。ターミナルからBlenderを起動すると確実です:
```bash
/Applications/Blender.app/Contents/MacOS/Blender
```

**Q: "Waiting for connection..." と表示されたあと何をすれば？**

A: Blenderはそのまま放置して、別のターミナルで以下を実行:
```bash
uv run examples/blender_debug.py
```

## 次のステップ

テストが成功したら:

1. **通常モードで実行:**
   ```bash
   uv run examples/blender_demo.py
   ```

2. **Neural Engine最適化:**
   ```bash
   uv run scripts/setup_coreml_models.py
   ```

3. **配信設定:**
   - OBSでBlenderのウィンドウをキャプチャ
   - 詳細は `BLENDER_QUICK_START.md` を参照

## サポート

問題が解決しない場合は、以下の情報を収集してください:

1. Blenderのバージョン (Help → About Blender)
2. OSのバージョン
3. エラーメッセージ（コンソールの出力全体）
4. test_simple.py の出力結果
