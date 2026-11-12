@echo off
rem Builds the AgriVision Android app. Everything (JDK, SDK, Gradle caches) lives on D:\android.
cd /d "%~dp0"
set JAVA_HOME=D:\android\jdk17
set ANDROID_HOME=D:\android\sdk
set ANDROID_USER_HOME=D:\android\.android
set GRADLE_USER_HOME=D:\android\gradle-home
if not exist D:\android\tmp mkdir D:\android\tmp
set TEMP=D:\android\tmp
set TMP=D:\android\tmp
set PATH=%JAVA_HOME%\bin;%PATH%
call D:\android\gradle-8.11.1\bin\gradle.bat assembleDebug --no-daemon --console=plain
if errorlevel 1 exit /b 1
copy /y app\build\outputs\apk\debug\app-debug.apk "..\AgriVision.apk" >nul
echo.
echo APK ready: %~dp0..\AgriVision.apk
