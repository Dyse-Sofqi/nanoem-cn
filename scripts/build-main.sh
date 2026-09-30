#!/bin/bash
# Main nanoem build script (release, x64, VS2022)
set -e
ROOT="F:/_Workspace/fork/nanoem-cn"
CMAKE="/c/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"

export NANOEM_BUILD_DEPENDENCIES_DIRECTORY="$ROOT/out/dependencies"
export FX9_BUILD_DEPENDENCIES_DIRECTORY="$ROOT/out/dependencies"
export NANOEM_TARGET_ARCHITECTURES=x86_64
export NANOEM_TARGET_CONFIGURATIONS=release
export NANOEM_TARGET_COMPILER=vs2022
export NANOEM_ENABLE_BUILD_MIMALLOC=1

mkdir -p "$ROOT/out/core"
cd "$ROOT/out/core"

"$CMAKE" \
  -DCMAKE_INSTALL_PREFIX=install-root \
  -DFX9_ENABLE_OPTIMIZER=OFF \
  -DNANOEM_ENABLE_BULLET=ON \
  -DNANOEM_ENABLE_MIMALLOC=ON \
  -DNANOEM_ENABLE_NMD=ON \
  -DNANOEM_ENABLE_TEST=OFF \
  -DNANOEM_INSTALL_EFFECT_PLUGIN=ON \
  -DNANOEM_INSTALL_FFMPEG_PLUGIN=OFF \
  -DNANOEM_INSTALL_GIF_PLUGIN=OFF \
  -DNANOEM_INSTALL_LSMASH_PLUGIN=ON \
  -DNANOEM_TARGET_COMPILER=vs2022 \
  -G"Visual Studio 17 2022" -Ax64 \
  ../../

"$CMAKE" --build . --config release
echo "BUILD SUCCEEDED"
