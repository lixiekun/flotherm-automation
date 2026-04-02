# Modify APK targetSdkVersion Guide

Steps to modify an APK's `targetSdkVersion` for Android compatibility using `apktool`.

## Prerequisites

```bash
brew install apktool
```

Android SDK with `apksigner` and debug keystore (`~/.android/debug.keystore`).

## Steps

### 1. Decode APK

```bash
apktool d Touch-Point-1-1-APKPure.apk -o Touch-Point-decoded
```

### 2. Modify targetSdkVersion

Edit `Touch-Point-decoded/apktool.yml`:

```yaml
# Before
targetSdkVersion: '18'

# After
targetSdkVersion: '24'
```

### 3. Rebuild APK

```bash
apktool b Touch-Point-decoded -o Touch-Point-modified.apk
```

### 4. Sign APK with debug key

```bash
# Generate debug keystore if not exists
keytool -genkey -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000

# Sign
apksigner sign --ks ~/.android/debug.keystore --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out Touch-Point-1-1-APKPure.apk Touch-Point-modified.apk
```

### 5. Verify

```bash
apksigner verify Touch-Point-1-1-APKPure.apk
aapt dump badging Touch-Point-1-1-APKPure.apk | grep sdkVersion
```

## Notes

- `targetSdkVersion: 24` (Android 7.0) is required for Android 16+ compatibility
- Debug-signed APK must be uninstalled before installing a different-signed version
- Original APK should be backed up before modification
