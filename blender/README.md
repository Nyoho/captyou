# Blender スクリプト集

CaptyOUとBlenderを連携するためのスクリプトとテストツールです。

## 📁 ファイル一覧

### 1. `hello_blender.py` ⭐ まずはこれ!
**最も簡単なテストスクリプト**

- Blenderで実行すると「Hello Blender!」と表示
- スクリプトが正しく動作するか確認
- コンソールの表示方法を確認

**使い方:**
1. Blender → Scripting
2. Text Editor → Open Text → `hello_blender.py`
3. Run Script (▶ ボタン)
4. コンソールに「Hello Blender!」と表示されればOK

---

### 2. `test_simple.py` ⭐ 次はこれ!
**VRMアバターの確認スクリプト**

- シーン内のアバターを検索
- アーマチュアとシェイプキーを確認
- ソケット接続をテスト

**使い方:**
1. VRMアバターをインポート (File → Import → VRM)
2. Blender → Scripting
3. Text Editor → Open Text → `test_simple.py`
4. Run Script
5. コンソールで結果を確認

**期待される出力:**
```
✓ アーマチュアを発見: Armature
✓ シェイプキーを発見: Body
✓ ポート9000は使用可能です
```

---

### 3. `captyou_receiver.py` ⭐ 本番用!
**CaptyOUからデータを受信するメインスクリプト**

- ポーズと表情データを受信
- VRMアバターにリアルタイムで反映
- ポート9000でソケット接続

**使い方:**
1. VRMアバターをインポート済みであることを確認
2. Blender → Scripting
3. Text Editor → Open Text → `captyou_receiver.py`
4. Run Script
5. コンソールに "Waiting for connection on port 9000..." と表示されればOK
6. 別のターミナルで `uv run examples/blender_debug.py` を実行

**期待される出力:**
```
Found armature: Armature
Found mesh with shape keys: Body
Waiting for connection on port 9000...
Connected: ('127.0.0.1', 54321)
```

---

## 🚨 トラブルシューティング

### コンソールにメッセージが表示されない

**解決方法1: ターミナルからBlenderを起動**

```bash
# macOS
/Applications/Blender.app/Contents/MacOS/Blender

# Linux
blender

# Windows
"C:\Program Files\Blender Foundation\Blender\blender.exe"
```

この方法だと、ターミナルに直接ログが表示されます。

**解決方法2: Blenderのコンソールを開く**

- macOS/Linux: Window → Toggle System Console
- Windows: Window → Toggle System Console（別ウィンドウが開く）

---

### "Error: No armature found in scene"

**原因:** VRMアバターがインポートされていない

**解決方法:**
1. File → Import → VRM (.vrm)
2. VRMファイルを選択
3. スクリプトを再実行

---

### "OSError: Address already in use"

**原因:** ポート9000が既に使用されている

**解決方法:**
```bash
# ポートを確認
lsof -i :9000

# プロセスを終了
kill -9 [PID]

# またはBlenderを再起動
```

---

## 📝 実行の順番（重要！）

```
Step 1: hello_blender.py を実行
  └─> コンソール表示の確認

Step 2: VRMアバターをインポート
  └─> File → Import → VRM

Step 3: test_simple.py を実行
  └─> アバターの確認

Step 4: captyou_receiver.py を実行
  └─> Blenderで待機
       |
       v
  別ターミナルで:
  uv run examples/blender_debug.py
  └─> CaptyOUから接続
```

---

## 🔗 関連ドキュメント

- **初心者向け:** `../BLENDER_STEP_BY_STEP.md` - 詳しい手順
- **クイックスタート:** `../BLENDER_QUICK_START.md` - 概要と設定
- **完全ガイド:** `../BLENDER_SETUP.md` - 詳細な技術情報

---

## ⚙️ 必要な環境

- **Blender:** 3.0以降
- **VRM Add-on:** インストール済み
- **VRMアバター:** インポート済み
- **Python環境:** uvまたはPython 3.8以降

---

## 💡 ヒント

1. **ターミナルからBlenderを起動すると、ログが見やすい**
2. **hello_blender.py で必ず動作確認してから次へ**
3. **エラーメッセージは全文コピーしてググると解決策が見つかる**
4. **VRMアバターは VRoid Studio で簡単に作れる**

---

## 🎯 成功の確認

以下が全て表示されれば成功:

- [ ] hello_blender.py: "Hello Blender!" と表示
- [ ] test_simple.py: "✓ アーマチュアを発見" と表示
- [ ] captyou_receiver.py: "Waiting for connection..." と表示
- [ ] CaptyOU側: "✅ Blenderに接続しました!" と表示
- [ ] Blenderのアバターが動く!

---

Happy Blending! 🎨
