[app]
title = Tire Store
package.name = tirestore
package.domain = org.tirestore

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1
requirements = python3,kivy

orientation = portrait
fullscreen = 0
android.permissions = INTERNET

android.arch = armeabi-v7a

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1