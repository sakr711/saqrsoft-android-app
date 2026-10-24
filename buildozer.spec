[app]
title = SaqrSoft Status
package.name = saqrsoftstatus
package.domain = com.saqrsoft
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt
version = 1.0.0

requirements = python3,kivy==2.3.0,pyjnius,requests,arabic-reshaper,python-bidi

orientation = portrait
fullscreen = 0

# إذن الإنترنت فقط
android.permissions = INTERNET

android.api = 34
android.minapi = 24
android.ndk_api = 24

android.archs = arm64-v8a

android.allow_backup = True
android.copy_assets = True

[buildozer]
log_level = 2
warn_on_root = 1

