"""
Blender接続テスト - 最小限のテストスクリプト

このスクリプトはBlenderで正しく動作するかをテストします。
"""

import bpy

# テスト1: Blenderで実行されているか確認
print("=" * 70)
print("CaptyOU Blender Test - スクリプトが実行されました！")
print("=" * 70)

# テスト2: シーン内のオブジェクトを表示
print("\n[テスト1] シーン内のオブジェクト:")
for obj in bpy.data.objects:
    print(f"  - {obj.name} (type: {obj.type})")

# テスト3: アーマチュアを検索
print("\n[テスト2] アーマチュアの検索:")
armature_found = False
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        print(f"  ✓ アーマチュアを発見: {obj.name}")
        armature_found = True

        # ボーン名を表示
        print(f"  ボーン数: {len(obj.pose.bones)}")
        print(f"  最初の5つのボーン:")
        for i, bone in enumerate(obj.pose.bones[:5]):
            print(f"    - {bone.name}")

if not armature_found:
    print("  ✗ アーマチュアが見つかりません")
    print("  → VRMアバターをインポートしてください")
    print("  → File → Import → VRM (.vrm)")

# テスト4: メッシュとシェイプキーを検索
print("\n[テスト3] シェイプキーの検索:")
shape_key_found = False
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        print(f"  ✓ シェイプキーを発見: {obj.name}")
        shape_key_found = True

        # シェイプキー名を表示
        print(f"  シェイプキー数: {len(obj.data.shape_keys.key_blocks)}")
        print(f"  最初の5つのシェイプキー:")
        for i, key in enumerate(obj.data.shape_keys.key_blocks[:5]):
            print(f"    - {key.name}")

if not shape_key_found:
    print("  ✗ シェイプキーが見つかりません")
    print("  → VRMアバターに表情データがない可能性があります")

# テスト5: ソケット接続のテスト
print("\n[テスト4] ソケット接続のテスト:")
try:
    import socket
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    test_socket.bind(('localhost', 9000))
    test_socket.close()
    print("  ✓ ポート9000は使用可能です")
except Exception as e:
    print(f"  ✗ ポート9000のエラー: {e}")
    print("  → 別のプログラムがポートを使用している可能性があります")

# 最終結果
print("\n" + "=" * 70)
print("テスト完了!")
print("=" * 70)

if armature_found:
    print("✓ このスクリプトは正しく動作しています")
    print("✓ 次のステップ: captyou_receiver.py を実行してください")
else:
    print("✗ VRMアバターをインポートしてから再度実行してください")
print("=" * 70)
