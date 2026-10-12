[app]

# (str) Title of your application
title = Detector de Estrés - Caligrafía IA

# (str) Package name
package.name = estres_caligrafia

# (str) Package domain (needed for android/ios packaging)
package.domain = org.nazerenobm

# (source.dir) Source directory (where your main python file is)
source.dir = .

# (source.include_exts) Source include extensions (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (version) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy,opencv,numpy,scikit-learn,joblib,pyjnius,android

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = INTERNET,CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (list) Android archs (arm64-v8a, armeabi-v7a, x86, x86_64)
android.archs = arm64-v8a

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (int) Target Android API
android.api = 31

# (int) Minimum API to support
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK version to use
android.sdk = 31

# (bool) Accept SDK license
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2
