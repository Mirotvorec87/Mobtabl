[app]

# Название приложения
title = MobileAnniversaryTracker

# Имя пакета (должно быть уникальным)
package.name = mobileanniversarytracker

# Домен (используется для создания package.domain)
package.domain = org.example

# Исходный код приложения
source.dir = .

# Главный файл приложения
source.include_exts = py,png,jpg,kv,atlas,db
main.py = main.py

# Версия приложения
version = 1.0.0

# Требования
requirements = python3,kivy==2.3.0,pillow==10.3.0,sqlite3,android

# Разрешения Android
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Характеристики оборудования
android.api = 30
android.minapi = 21
android.ndk = 23b
android.sdk = 33
android.ndk_api = 21

# Архитектура
android.arch = arm64-v8a

# Ориентация экрана
orientation = portrait

# Полноэкранный режим
fullscreen = 0