[app]
title = Match3 Game
package.name = match3game
package.domain = org.yourname
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav,mp3,dat
version = 0.1
requirements = python3,pygame,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 23b
android.sdk = 31
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
