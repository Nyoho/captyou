"""
Hello Blender - 最も簡単なテストスクリプト

このスクリプトがBlenderで実行されると、コンソールにメッセージを表示します。
"""

# テスト: コンソールにメッセージを表示
print("")
print("=" * 70)
print("Hello Blender!")
print("このメッセージが見えていれば、スクリプトは正しく動作しています！")
print("=" * 70)
print("")

# Blenderのバージョンを表示
import bpy
print(f"Blenderバージョン: {bpy.app.version_string}")
print("")

# 次のステップを案内
print("次のステップ:")
print("1. VRMアバターをインポート (File → Import → VRM)")
print("2. test_simple.py を実行")
print("3. captyou_receiver.py を実行")
print("")
print("=" * 70)
