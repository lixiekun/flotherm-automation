# 修改 APK targetSdkVersion 操作步骤

使用 `apktool` 修改 APK 的 `targetSdkVersion`，解决 Android 高版本兼容性问题。

## 前置条件

```bash
brew install apktool
```

需要 Android SDK 中的 `apksigner`，以及 debug 签名密钥 (`~/.android/debug.keystore`)。

## 操作步骤

### 1. 解码 APK

```bash
apktool d Touch-Point-1-1-APKPure.apk -o Touch-Point-decoded
```

### 2. 修改 targetSdkVersion

编辑 `Touch-Point-decoded/apktool.yml`：

```yaml
# 修改前
targetSdkVersion: '18'

# 修改后
targetSdkVersion: '24'
```

### 3. 重新打包

```bash
apktool b Touch-Point-decoded -o Touch-Point-modified.apk
```

### 4. 用 debug 密钥签名

```bash
# 如果没有 debug 密钥，先生成一个
keytool -genkey -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000

# 签名
apksigner sign --ks ~/.android/debug.keystore --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out Touch-Point-1-1-APKPure.apk Touch-Point-modified.apk
```

### 5. 验证

```bash
apksigner verify Touch-Point-1-1-APKPure.apk
aapt dump badging Touch-Point-1-1-APKPure.apk | grep sdkVersion
```

## 注意事项

- `targetSdkVersion: 24`（Android 7.0）是 Android 16+ 正常运行的最低要求
- debug 签名的 APK 与原版签名不同，安装前需要先卸载旧版本
- 修改前请备份原始 APK
