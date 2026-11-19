# GalaxyXR-360

Galaxy XR(Android XR)에서 보는 **360° 영상·사진 콘텐츠 생성 파이프라인**과 재생 앱 **Calm 360**.
53개 테마(힐링·바다·우주·SF·사막·시골·쥐라기·중세·판타지·도시)로 360° 영상 106편, 360° 사진 106장을 만듭니다.

> 상태: 개발 중. 이미지 단계(FLUX 3)와 사진 단계는 검증했고, 영상 단계(A14B → CubeComposer → SeedVR2 8K)는 샘플을 검증하고 있습니다.

## 파이프라인

### 360° 영상 (7680×3840, 30fps, HEVC, 소리 포함)

| 단계 | 모델 / 처리 | 스크립트 |
|---|---|---|
| 1. 첫 이미지 | FLUX 3 Image Klein (distilled), 2048×1152, 수평·정면·왜곡 없는 90° 시야 | `scripts/flux3_gen.py` |
| 2. 원본 영상 | Wan2.2 I2V A14B, 1280×720, 16fps, 81프레임 구간 2개를 이어 10초, 40스텝 | `scripts/pers_gen_a14b.py` |
| 3. 360° 변환 | CubeComposer (3K/4K), **30스텝 이상**, 프레임 수는 window 길이의 배수 | `scripts/cube_custom.py` |
| 4. 8K 업샘플링 | SeedVR2 (360° 좌우 이어 붙이기) | `scripts/seedvr_pano.py` |
| 5. 30fps + 반복 | RIFE 4.25 보간, 끝↔처음 크로스페이드 | `scripts/post_video.py` |
| 6. 소리 | HunyuanVideo-Foley (장면별 텍스트 + 금지 소리), CLAP 자동 검사 후 재생성 | `scripts/run_foley.py`, `scripts/clap_check.py` |
| 7. 인코딩 | HEVC Main, High tier L6.0, 100 Mb/s(최대 150), Spherical Video V1 메타데이터 | `scripts/post_video.py` |

### 360° 사진 (8192×4096, GPano JPEG + 반복 환경음)

| 단계 | 모델 / 처리 | 스크립트 |
|---|---|---|
| 1. 정면 원본 | FLUX 3 Image Klein | `scripts/flux3_gen.py` |
| 2. 360° 펼치기 | FLUX.2 klein base 9B + 360 ERP outpaint LoRA, 2048×1024 | `scripts/photo360_flux2.py` |
| 3. 8K 업샘플링 | SeedVR2 ×4 | `scripts/seedvr_pano.py` |
| 4. 소리 | HunyuanVideo-Foley, 사진별 소리 설명 + CLAP 검사, 끊김 없는 반복 | `scripts/photo_audio.py` |
| 미리보기 | 8K 사진 + 소리 → 360° HEVC 정지 영상 | `scripts/photo8k_sound.py` |

## 폴더

```
content/   테마·프롬프트 원본 (themes*.py), 검수 반영본 (video_r*.py, photo_r*.py), 소리 설명 (sounds.py, photo_sounds.py)
jobs/      생성 작업 목록과 검수로 확정된 선택 (videos_v2.json, *_selection.json, *_captions.json)
scripts/   파이프라인 스크립트
setup/     환경 설치·모델 다운로드 스크립트 (경로는 개발 서버 기준)
app/       Galaxy XR 재생 앱 Calm 360 (Kotlin, Jetpack XR SceneCore 1.0.0, Media3)
```

## 앱 Calm 360

- 360° 영상·사진을 SceneCore `SurfaceEntity` 구(sphere)에 띄워 Full Space에서 재생합니다.
- ✋ 손으로 보는 방향 조절: 360° 화면을 집고 끌기, 제어판의 드래그 패드, 30° 회전 버튼, 정면 복귀.
- 🔂 한 편 반복 / 🔁 전체 반복(30초·1분·3분·5분 간격) / ▶ 전체 연속 재생, 분류·종류 필터.
- 콘텐츠는 APK에 넣지 않습니다. 앱이 세 곳을 찾아 합칩니다:
  1. 헤드셋에서 내려받은 파일(Download 등): 사진·동영상·오디오 접근 허용 후 MediaStore로 찾고, 가로:세로 2:1인 360° 사진·영상만 목록에 올립니다.
  2. `📂 폴더 추가`로 고른 폴더(하위 폴더 포함, 권한 유지).
  3. 예전 방식인 `adb push` 폴더 `/sdcard/Android/media/com.panocalm.xr/content/` + `manifest.json`.
- 사진의 소리는 같은 이름의 오디오 파일입니다 (`forest_morning_p1.jpg` + `forest_morning_p1.m4a`). 파일 이름 앞부분으로 테마 이름과 분류를 붙입니다.
- 빌드: `cd app && gradle assembleRelease` (compileSdk 36, AGP 8.10.1, JDK 17). `local.properties`의 `sdk.dir`은 직접 지정하세요.

## 외부 코드와 모델

이 저장소에는 모델 가중치와 외부 저장소 코드가 들어 있지 않습니다. 아래를 각자 받아 쓰고, **각 라이선스를 확인하세요** (일부는 비상업 전용입니다).

| 구성 요소 | 출처 | 라이선스 (확인한 것) |
|---|---|---|
| FLUX 3 Image Klein | black-forest-labs/flux-3-image-klein | FLUX Kommunity License (비상업 기준, 조건부 예외) |
| FLUX.2 klein base 9B | black-forest-labs/FLUX.2-klein-base-9B | FLUX Non-Commercial License |
| 360 ERP outpaint LoRA | nomadoor/flux-2-klein-9B-360-erp-outpaint-lora | FLUX Non-Commercial License v2.1 |
| Wan2.2 I2V A14B | Wan-AI/Wan2.2-I2V-A14B | 모델 카드 확인 |
| CubeComposer | TencentARC/CubeComposer (GitHub, HF) | License Terms of CubeComposer (EU 사용 불가 명시) |
| SeedVR2 | ByteDance-Seed/SeedVR2, numz/ComfyUI-SeedVR2_VideoUpscaler | Apache-2.0 |
| HunyuanVideo-Foley | tencent/HunyuanVideo-Foley | 모델 카드 확인 |
| CLAP | laion/larger_clap_general | 모델 카드 확인 |
| RIFE 4.25 | hzwer/Practical-RIFE | 저장소 확인 |
| Spatial Media Metadata | google/spatial-media | 저장소 확인 |

`scripts/cube_custom.py`는 CubeComposer를 공식 테스트셋이 아닌 **임의의 원근 영상**에 쓰기 위한 실행기입니다. 공식 `remap_perspective_to_equirectangular`의 마스크가 이 용도에서는 전체를 1로 돌려주어서, 학습 때와 같은 방식(equi2pers 샘플 마스크 + blur 31/σ1 + 0.05 임계값)으로 마스크를 만들고, 고정 카메라용 샘플링 그리드를 GPU에서 한 번만 계산합니다.

## 참고한 기기 사양

Galaxy XR 디스플레이는 한쪽 눈 3552×3840, 가로 시야각 약 109°입니다. 360° 콘텐츠를 패널 선명도에 맞추려면 가로 약 12K가 필요하고, 8K(7680/8192)는 약 21–23 px/°입니다.
