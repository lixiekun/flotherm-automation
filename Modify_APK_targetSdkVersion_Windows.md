# 修改 APK targetSdkVersion 操作步骤（Windows 版）

使用 `apktool` 修改 APK 的 `targetSdkVersion`，解决 Android 高版本兼容性问题。

## 前置条件

### 安装 Java（需要 JDK 8+）

从 [Adoptium](https://adoptium.net/) 下载安装，或使用 winget：

```cmd
winget install EclipseAdoptium.Temurin.17.JDK
```

安装后验证：

```cmd
java -version
```

### 安装 apktool

方式一：从 [apktool 官网](https://apktool.org/) 下载 `apktool_2.x.x.jar`，然后创建批处理包装：

1. 新建文件夹，例如 `C:\apktool\`
2. 将下载的 `apktool_2.x.x.jar` 放入，重命名为 `apktool.jar`
3. 在同目录下新建 `apktool.bat`，内容如下：

```bat
@echo off
java -jar "%~dp0\apktool.jar" %*
```

4. 将 `C:\apktool\` 加入系统 PATH 环境变量

方式二：使用 [Chocolatey](https://chocolatey.org/)：

```cmd
choco install apktool
```

### 安装 Android SDK 命令行工具

需要 `apksigner` 和 `aapt`，它们在 Android SDK Build Tools 中。

1. 安装 [Android Studio](https://developer.android.com/studio)，或单独安装 [command-line tools](https://developer.android.com/studio#command-tools)
2. 通过 SDK Manager 安装 Build Tools（建议 30+ 版本）
3. 工具路径通常在：`%LOCALAPPDATA%\Android\Sdk\build-tools\<版本号>\`

> 以下命令假设 `apksigner` 和 `aapt` 已加入 PATH。如果没有，请使用完整路径，例如：
> `%LOCALAPPDATA%\Android\Sdk\build-tools\34.0.0\apksigner`

## 操作步骤

### 1. 解码 APK

```cmd
apktool d Touch-Point-1-1-APKPure.apk -o Touch-Point-decoded
```

### 2. 修改 targetSdkVersion

用记事本或其他编辑器打开 `Touch-Point-decoded\apktool.yml`：

```yaml
# 修改前
targetSdkVersion: '18'

# 修改后
targetSdkVersion: '24'
```

### 3. 重新打包

```cmd
apktool b Touch-Point-decoded -o Touch-Point-modified.apk
```

### 4. 用 debug 密钥签名

```cmd
:: 如果没有 debug 密钥，先生成一个
keytool -genkey -v -keystore %USERPROFILE%\.android\debug.keystore -alias androiddebugkey -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000

:: 签名
apksigner sign --ks %USERPROFILE%\.android\debug.keystore --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out Touch-Point-1-1-APKPure.apk Touch-Point-modified.apk
```

### 5. 验证

```cmd
apksigner verify Touch-Point-1-1-APKPure.apk
aapt dump badging Touch-Point-1-1-APKPure.apk | findstr sdkVersion
```

## 注意事项

- `targetSdkVersion: 24`（Android 7.0）是 Android 16+ 正常运行的最低要求
- debug 签名的 APK 与原版签名不同，安装前需要先卸载旧版本
- 修改前请备份原始 APK
- Windows 下建议在 CMD 或 PowerShell 中执行上述命令
- 如果路径中包含空格（如用户名），请用双引号包裹路径
