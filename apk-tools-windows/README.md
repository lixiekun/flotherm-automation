# APK 修改工具包（Windows 离线版）

本目录包含修改 APK targetSdkVersion 所需的全部工具，无需联网。

## 前置条件

只需要安装 **Java**（JDK 8+），下载地址：

- [Adoptium JDK 17](https://adoptium.net/)（推荐）
- 或使用 winget：`winget install EclipseAdoptium.Temurin.17.JDK`

## 包含工具

| 文件 | 说明 |
|------|------|
| `apktool.jar` + `apktool.bat` | APK 解包/打包工具 |
| `aapt.exe` | 查看 APK 信息 |
| `apksigner.jar` + `apksigner.bat` | APK 签名工具 |

## 使用方法

将本目录加入 PATH，或用完整路径执行。以下假设在 CMD 中操作：

### 1. 解码 APK

```cmd
apktool.bat d Touch-Point-1-1-APKPure.apk -o Touch-Point-decoded
```

### 2. 修改 targetSdkVersion

编辑 `Touch-Point-decoded\apktool.yml`：

```yaml
targetSdkVersion: '24'
```

### 3. 重新打包

```cmd
apktool.bat b Touch-Point-decoded -o Touch-Point-modified.apk
```

### 4. 签名

```cmd
:: 生成 debug 密钥（只需执行一次）
keytool -genkey -v -keystore debug.keystore -alias androiddebugkey -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000

:: 签名
apksigner.bat sign --ks debug.keystore --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out Touch-Point-signed.apk Touch-Point-modified.apk
```

### 5. 验证

```cmd
apksigner.bat verify Touch-Point-signed.apk
aapt.exe dump badging Touch-Point-signed.apk | findstr sdkVersion
```

## 注意事项

- debug 签名的 APK 与原版签名不同，安装前需先卸载旧版本
- 修改前请备份原始 APK
