"""
全ボーン名とシェイプキー名を表示
"""
import bpy

print("\n" + "=" * 70)
print("全ボーン名とシェイプキー名")
print("=" * 70)

# アーマチュアを検索
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        print(f"\n✓ アーマチュア: {obj.name}")
        print(f"  ボーン数: {len(obj.pose.bones)}\n")
        print("  全ボーン名:")
        for i, bone in enumerate(obj.pose.bones, 1):
            # 腕、脚、頭、首、スパインのみ表示
            name_lower = bone.name.lower()
            if any(keyword in name_lower for keyword in [
                'arm', 'hand', 'leg', 'foot', 'head', 'neck',
                'spine', 'chest', 'hips', 'shoulder'
            ]):
                print(f"    {i:3d}. {bone.name}")
        break

# メッシュとシェイプキーを検索
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        print(f"\n✓ シェイプキー付きメッシュ: {obj.name}")
        print(f"  シェイプキー数: {len(obj.data.shape_keys.key_blocks)}\n")
        print("  全シェイプキー名:")
        for i, key in enumerate(obj.data.shape_keys.key_blocks, 1):
            print(f"    {i:3d}. {key.name}")

print("\n" + "=" * 70)
