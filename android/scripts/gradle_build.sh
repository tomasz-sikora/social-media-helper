#!/usr/bin/env bash
# Build the Android release APK using Gradle.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANDROID_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ANDROID_DIR"
./gradlew assembleRelease
echo "APK built: app/build/outputs/apk/release/app-release-unsigned.apk"
