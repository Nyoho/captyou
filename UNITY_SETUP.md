# Unity統合ガイド

CaptyOUからのポーズ・表情データをUnityで受信してアバターに反映する方法を説明します。

## 必要なもの

### 1. Unity環境
- **Unity 2021.3 LTS以降**推奨
- プラットフォーム: macOS、Windows、Linux

### 2. 3Dアバター
以下のいずれか：
- **VRM形式**のアバター（推奨）
- **Humanoid Rig**設定済みのアバター
- **Mixamo**リグのアバター

### 3. OSC通信ライブラリ
- **extOSC**（推奨、無料）
- または **UnityOSC**

## セットアップ手順

### ステップ1: extOSCのインストール

#### Package Managerから
1. Unity → Window → Package Manager
2. 「+」→ Add package from git URL
3. 以下を入力:
```
https://github.com/Iam1337/extOSC.git
```

#### または Asset Storeから
- [extOSC - Asset Store](https://assetstore.unity.com/packages/tools/input-management/extosc-open-sound-control-159500)

### ステップ2: アバターのインポート

#### VRMアバターの場合
1. **UniVRM**をインストール
   ```
   https://github.com/vrm-c/UniVRM.git?path=/Assets/VRM#v0.112.0
   ```

2. VRMファイルをドラッグ&ドロップ
3. プレハブをシーンに配置

#### Humanoidアバターの場合
1. アバターをインポート
2. Rig設定でAnimation TypeをHumanoidに設定
3. Configure...でボーンマッピングを確認

### ステップ3: OSC受信スクリプトの追加

以下のスクリプトを作成します：

#### `CaptyOUReceiver.cs`

```csharp
using UnityEngine;
using extOSC;

public class CaptyOUReceiver : MonoBehaviour
{
    [Header("OSC Settings")]
    public int receivePort = 9000;

    [Header("Avatar")]
    public Animator avatarAnimator;
    public SkinnedMeshRenderer faceMesh;

    private OSCReceiver receiver;

    // ポーズデータ（33点）
    private Vector3[] poseLandmarks = new Vector3[33];

    // 表情データ
    private float eyeBlinkLeft = 0f;
    private float eyeBlinkRight = 0f;
    private float jawOpen = 0f;
    private float smileLeft = 0f;
    private float smileRight = 0f;

    void Start()
    {
        // OSCレシーバーを初期化
        receiver = gameObject.AddComponent<OSCReceiver>();
        receiver.LocalPort = receivePort;

        // ポーズデータの受信
        receiver.Bind("/tracking/head/position", OnHeadPosition);
        receiver.Bind("/tracking/hand/left/position", OnLeftHandPosition);
        receiver.Bind("/tracking/hand/right/position", OnRightHandPosition);
        receiver.Bind("/tracking/hip/position", OnHipPosition);

        // 表情データの受信
        receiver.Bind("/avatar/parameters/EyeBlinkLeft", OnEyeBlinkLeft);
        receiver.Bind("/avatar/parameters/EyeBlinkRight", OnEyeBlinkRight);
        receiver.Bind("/avatar/parameters/JawOpen", OnJawOpen);
        receiver.Bind("/avatar/parameters/SmileLeft", OnSmileLeft);
        receiver.Bind("/avatar/parameters/SmileRight", OnSmileRight);

        Debug.Log($"CaptyOU Receiver started on port {receivePort}");
    }

    void Update()
    {
        // アバターに反映
        ApplyPoseToAvatar();
        ApplyExpressionsToAvatar();
    }

    // === OSCメッセージ受信ハンドラ ===

    private void OnHeadPosition(OSCMessage message)
    {
        if (message.Values.Count >= 3)
        {
            poseLandmarks[0] = new Vector3(
                message.Values[0].FloatValue,
                message.Values[1].FloatValue,
                message.Values[2].FloatValue
            );
        }
    }

    private void OnLeftHandPosition(OSCMessage message)
    {
        if (message.Values.Count >= 3)
        {
            poseLandmarks[15] = new Vector3(
                message.Values[0].FloatValue,
                message.Values[1].FloatValue,
                message.Values[2].FloatValue
            );
        }
    }

    private void OnRightHandPosition(OSCMessage message)
    {
        if (message.Values.Count >= 3)
        {
            poseLandmarks[16] = new Vector3(
                message.Values[0].FloatValue,
                message.Values[1].FloatValue,
                message.Values[2].FloatValue
            );
        }
    }

    private void OnHipPosition(OSCMessage message)
    {
        if (message.Values.Count >= 3)
        {
            poseLandmarks[23] = new Vector3(
                message.Values[0].FloatValue,
                message.Values[1].FloatValue,
                message.Values[2].FloatValue
            );
        }
    }

    private void OnEyeBlinkLeft(OSCMessage message)
    {
        eyeBlinkLeft = message.Values[0].FloatValue;
    }

    private void OnEyeBlinkRight(OSCMessage message)
    {
        eyeBlinkRight = message.Values[0].FloatValue;
    }

    private void OnJawOpen(OSCMessage message)
    {
        jawOpen = message.Values[0].FloatValue;
    }

    private void OnSmileLeft(OSCMessage message)
    {
        smileLeft = message.Values[0].FloatValue;
    }

    private void OnSmileRight(OSCMessage message)
    {
        smileRight = message.Values[0].FloatValue;
    }

    // === アバターへの適用 ===

    private void ApplyPoseToAvatar()
    {
        if (avatarAnimator == null) return;

        // 頭の位置と回転
        Transform head = avatarAnimator.GetBoneTransform(HumanBodyBones.Head);
        if (head != null && poseLandmarks[0] != Vector3.zero)
        {
            // MediaPipeの座標系をUnityに変換
            Vector3 unityPos = new Vector3(
                -poseLandmarks[0].x,  // X軸を反転
                poseLandmarks[0].y,
                poseLandmarks[0].z
            );

            head.localPosition = unityPos * 2f;  // スケール調整
        }

        // 手の位置
        Transform leftHand = avatarAnimator.GetBoneTransform(HumanBodyBones.LeftHand);
        Transform rightHand = avatarAnimator.GetBoneTransform(HumanBodyBones.RightHand);

        if (leftHand != null && poseLandmarks[15] != Vector3.zero)
        {
            Vector3 unityPos = new Vector3(
                -poseLandmarks[15].x,
                poseLandmarks[15].y,
                poseLandmarks[15].z
            );
            leftHand.localPosition = unityPos * 2f;
        }

        if (rightHand != null && poseLandmarks[16] != Vector3.zero)
        {
            Vector3 unityPos = new Vector3(
                -poseLandmarks[16].x,
                poseLandmarks[16].y,
                poseLandmarks[16].z
            );
            rightHand.localPosition = unityPos * 2f;
        }
    }

    private void ApplyExpressionsToAvatar()
    {
        if (faceMesh == null) return;

        // ブレンドシェイプを適用
        // 注: ブレンドシェイプ名はアバターに合わせて調整してください

        SetBlendShape("Blink_L", eyeBlinkLeft * 100f);
        SetBlendShape("Blink_R", eyeBlinkRight * 100f);
        SetBlendShape("A", jawOpen * 100f);  // 口を開ける
        SetBlendShape("Joy", (smileLeft + smileRight) * 50f);  // 笑顔
    }

    private void SetBlendShape(string name, float value)
    {
        int index = faceMesh.sharedMesh.GetBlendShapeIndex(name);
        if (index >= 0)
        {
            faceMesh.SetBlendShapeWeight(index, value);
        }
    }

    void OnDestroy()
    {
        if (receiver != null)
        {
            receiver.Close();
        }
    }
}
```

### ステップ4: Unityでの設定

1. **空のGameObjectを作成**
   - Hierarchy → 右クリック → Create Empty
   - 名前を「CaptyOUReceiver」に変更

2. **スクリプトをアタッチ**
   - `CaptyOUReceiver.cs`をGameObjectにドラッグ

3. **アバターを割り当て**
   - Avatar Animator: アバターのAnimatorコンポーネント
   - Face Mesh: 顔のSkinnedMeshRenderer

4. **ポート設定**
   - Receive Port: 9000（デフォルト）

## ブレンドシェイプのマッピング

### VRMアバターの場合

VRMのブレンドシェイプ名は標準化されています：

```csharp
// VRM標準ブレンドシェイプ
SetBlendShape("Blink_L", eyeBlinkLeft * 100f);      // 左目を閉じる
SetBlendShape("Blink_R", eyeBlinkRight * 100f);     // 右目を閉じる
SetBlendShape("A", jawOpen * 100f);                 // あ（口を開ける）
SetBlendShape("I", 0f);                             // い
SetBlendShape("U", 0f);                             // う
SetBlendShape("E", 0f);                             // え
SetBlendShape("O", 0f);                             // お
SetBlendShape("Joy", (smileLeft + smileRight) * 50f); // 笑顔
SetBlendShape("Angry", 0f);                         // 怒り
SetBlendShape("Sorrow", 0f);                        // 悲しみ
SetBlendShape("Fun", 0f);                           // 楽しい
```

### その他のアバターの場合

ブレンドシェイプ名を確認する方法：

```csharp
// ブレンドシェイプ名を列挙
Mesh mesh = faceMesh.sharedMesh;
for (int i = 0; i < mesh.blendShapeCount; i++)
{
    Debug.Log($"BlendShape {i}: {mesh.GetBlendShapeName(i)}");
}
```

## テスト方法

### 1. Unityでプレイモードを開始

### 2. CaptyOUを起動

```bash
python examples/full_avatar_demo.py \
  --unity-host localhost \
  --unity-port 9000 \
  --unity-protocol osc
```

### 3. 動作確認

- カメラに向かって動く
- 手を動かす
- 表情を変える

アバターが反応すれば成功です！

## 高度な設定

### IK（Inverse Kinematics）の使用

より自然な動きのために、Unity IKを使用：

```csharp
void OnAnimatorIK(int layerIndex)
{
    if (avatarAnimator == null) return;

    // 左手のIK
    if (poseLandmarks[15] != Vector3.zero)
    {
        avatarAnimator.SetIKPositionWeight(AvatarIKGoal.LeftHand, 1f);
        avatarAnimator.SetIKPosition(AvatarIKGoal.LeftHand,
            transform.TransformPoint(poseLandmarks[15]));
    }

    // 右手のIK
    if (poseLandmarks[16] != Vector3.zero)
    {
        avatarAnimator.SetIKPositionWeight(AvatarIKGoal.RightHand, 1f);
        avatarAnimator.SetIKPosition(AvatarIKGoal.RightHand,
            transform.TransformPoint(poseLandmarks[16]));
    }
}
```

### リップシンク（音声同期）

音声の周波数解析でリップシンクを実装：

```csharp
using UnityEngine;

public class LipSync : MonoBehaviour
{
    public AudioSource audioSource;
    public SkinnedMeshRenderer faceMesh;

    private float[] samples = new float[256];

    void Update()
    {
        if (audioSource.isPlaying)
        {
            audioSource.GetSpectrumData(samples, 0, FFTWindow.Blackman);

            float volume = 0f;
            for (int i = 0; i < samples.Length; i++)
            {
                volume += samples[i];
            }
            volume /= samples.Length;

            // 口の開き度を設定
            SetBlendShape("A", volume * 5000f);
        }
    }

    private void SetBlendShape(string name, float value)
    {
        int index = faceMesh.sharedMesh.GetBlendShapeIndex(name);
        if (index >= 0)
        {
            faceMesh.SetBlendShapeWeight(index, Mathf.Clamp(value, 0f, 100f));
        }
    }
}
```

## トラブルシューティング

### データが受信されない

1. **ポート番号を確認**
   ```bash
   # CaptyOU側
   --unity-port 9000

   # Unity側
   receivePort = 9000
   ```

2. **ファイアウォールを確認**
   - macOS: システム環境設定 → セキュリティとプライバシー → ファイアウォール
   - Unityアプリを許可

3. **OSCメッセージを確認**
   ```csharp
   // デバッグログを追加
   private void OnHeadPosition(OSCMessage message)
   {
       Debug.Log($"Received head position: {message.Values[0].FloatValue}");
       // ...
   }
   ```

### アバターが動かない

1. **Animatorを確認**
   - Animatorコンポーネントがアタッチされているか
   - Humanoid Rigが設定されているか

2. **ブレンドシェイプ名を確認**
   ```csharp
   // すべてのブレンドシェイプ名を出力
   for (int i = 0; i < faceMesh.sharedMesh.blendShapeCount; i++)
   {
       Debug.Log(faceMesh.sharedMesh.GetBlendShapeName(i));
   }
   ```

3. **スケールを調整**
   ```csharp
   // ポーズデータのスケールを変更
   head.localPosition = unityPos * 5f;  // 2f → 5fに変更
   ```

## 推奨アセット

### 無料
- **UniVRM** - VRMインポート
- **extOSC** - OSC通信
- **Final IK** - 高度なIK（有料だが強力）

### 有料
- **Oculus Lipsync** - 高品質リップシンク
- **Salsa LipSync** - リップシンク＆表情

## サンプルシーン

完全なサンプルプロジェクトは以下で公開予定：
- GitHub: `captyou-unity-sample`（準備中）

## 参考資料

- [extOSC Documentation](https://github.com/Iam1337/extOSC)
- [Unity Humanoid Avatar](https://docs.unity3d.com/Manual/ConfiguringtheAvatar.html)
- [VRM Specification](https://vrm.dev/en/)
- [OSC Protocol](http://opensoundcontrol.org/)
