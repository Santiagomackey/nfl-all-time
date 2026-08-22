# Blitzbook Android

Android app wrapper for the live Blitzbook NFL all-time database.

## Production site

https://nfl-all-time.vercel.app/

## What this app adds

- No browser address bar.
- Native Android bottom navigation for Home, Teams, Games and Universe.
- Android back-button support.
- External sites open outside the app while Blitzbook pages stay inside it.
- APK-only mobile CSS is injected after each page loads, so the app can have a clean phone layout without changing the desktop website.
- Live website updates appear in the app automatically.

## Build locally

Open this folder in Android Studio, let Gradle sync, then choose **Build > Build APK(s)**.

Or from a machine with Android SDK + Gradle installed:

```bash
gradle assembleDebug
```

APK output:

`app/build/outputs/apk/debug/app-debug.apk`

## GitHub Actions

The included `build-apk.yml` can build the APK automatically when this project is placed in the repository under `android/`.
