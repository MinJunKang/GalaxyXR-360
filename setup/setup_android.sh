#!/usr/bin/env bash
set -e
cd /workspace/code/pano_xr
[ -x /workspace/code/pano_xr/env_jdk/bin/java ] || /opt/conda/bin/conda create -y -p /workspace/code/pano_xr/env_jdk -c conda-forge openjdk=17 > logs/android_jdk.txt 2>&1
export JAVA_HOME=/workspace/code/pano_xr/env_jdk/lib/jvm; [ -d $JAVA_HOME ] || export JAVA_HOME=/workspace/code/pano_xr/env_jdk
export PATH=$JAVA_HOME/bin:$PATH
mkdir -p android-sdk/cmdline-tools && cd android-sdk
curl -sSL --retry 5 --speed-limit 100000 --speed-time 30 -C - -o clt.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip -q -o clt.zip -d cmdline-tools && rm -rf cmdline-tools/latest && mv cmdline-tools/cmdline-tools cmdline-tools/latest
yes | cmdline-tools/latest/bin/sdkmanager --sdk_root=$PWD --licenses > ../logs/android_lic.txt 2>&1 || true
cmdline-tools/latest/bin/sdkmanager --sdk_root=$PWD "platform-tools" "platforms;android-35" "platforms;android-36" "build-tools;35.0.0" > ../logs/android_sdk.txt 2>&1
curl -sSL --retry 5 --speed-limit 100000 --speed-time 30 -o gradle.zip https://services.gradle.org/distributions/gradle-8.11.1-bin.zip && unzip -q -o gradle.zip -d . && rm gradle.zip
echo ANDROID_DONE
