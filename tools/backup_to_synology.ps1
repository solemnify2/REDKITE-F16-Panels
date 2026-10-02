<#
  REDKITE - Synology 백업 체크포인트

  저장소 전체(이력 포함)를 .bundle 파일 하나로 묶어 Synology 에 보관합니다.
  .git 폴더를 통째로 동기화하면 두 PC 가 동시에 건드려 깨질 수 있지만,
  번들은 파일 하나라 그런 문제가 없습니다.

  복원:  git clone REDKITE-20261002-1530.bundle 복원폴더
  검증:  git bundle verify <파일>

  사용:
    powershell -ExecutionPolicy Bypass -File tools\backup_to_synology.ps1
    powershell ... -IncludeUncommitted     # 커밋 안 한 수정분을 .patch 로 함께 보관
#>
param(
  [string]$Dest = "C:\Users\solem\SynologyDrive\개인\# 취미\Falcon4\Cockpit\Redkite Project\_git_backup",
  [int]$Keep = 5,
  [switch]$IncludeUncommitted
)

# 네이티브(git) 호출이 많으므로 ErrorActionPreference 는 기본값을 쓰고
# 성공/실패는 $LASTEXITCODE 로 판단합니다. (PS 5.1 에서 2>&1 은 stderr 를
# ErrorRecord 로 감싸 정상 출력까지 오류로 만들기 때문에 쓰지 않습니다.)

# 스크립트 위치 기준으로 저장소 최상위를 찾는다 (경로가 바뀌어도 동작)
Set-Location (Split-Path -Parent $PSScriptRoot)
$repo = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) { Write-Host "git 저장소가 아닙니다. 먼저 git init / clone 하세요." -ForegroundColor Red; exit 1 }

if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Force -Path $Dest | Out-Null }
$stamp  = Get-Date -Format "yyyyMMdd-HHmm"
$bundle = Join-Path $Dest "REDKITE-$stamp.bundle"

# --- 1) 이력 전체를 번들로 ---
git bundle create --quiet "$bundle" --all
if ($LASTEXITCODE -ne 0) { Write-Host "번들 생성 실패" -ForegroundColor Red; exit 1 }

# --- 2) 무결성 검증 (깨진 백업을 남기지 않기 위해) ---
git bundle verify --quiet "$bundle" 2>$null
if ($LASTEXITCODE -ne 0) {
  Remove-Item $bundle -Force
  Write-Host "번들 검증 실패 - 삭제함" -ForegroundColor Red
  exit 1
}
$size = [math]::Round((Get-Item $bundle).Length / 1MB, 1)
Write-Host ("번들 저장: {0}  ({1} MB)" -f (Split-Path $bundle -Leaf), $size)

# --- 3) 선택: 커밋되지 않은 수정분을 패치로 ---
if ($IncludeUncommitted) {
  $patch = Join-Path $Dest "REDKITE-$stamp-uncommitted.patch"
  git diff HEAD | Out-File -FilePath $patch -Encoding utf8
  if ((Get-Item $patch).Length -eq 0) {
    Remove-Item $patch -Force
    Write-Host "커밋 안 한 수정분 없음"
  } else {
    Write-Host ("미커밋 패치: {0}   (복원: git apply <파일>)" -f (Split-Path $patch -Leaf))
  }
}

# --- 4) 오래된 백업 정리 ---
foreach ($pat in @("REDKITE-*.bundle", "REDKITE-*-uncommitted.patch")) {
  Get-ChildItem $Dest -Filter $pat -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $Keep |
    ForEach-Object { Remove-Item $_.FullName -Force; Write-Host "삭제: $($_.Name)" }
}

# --- 5) 상태 알림 ---
$modified  = @(git diff --name-only HEAD).Count
$untracked = @(git ls-files --others --exclude-standard).Count
if ($modified -gt 0 -or $untracked -gt 0) {
  Write-Host ("[알림] 미커밋: 수정 {0}개, 새 파일(추적 안 됨) {1}개" -f $modified, $untracked) -ForegroundColor Yellow
  if ($untracked -gt 0) {
    Write-Host "       새 파일은 패치에 담기지 않습니다. 커밋 후 백업해야 완전히 보존됩니다." -ForegroundColor Yellow
  }
}
git rev-parse --abbrev-ref "@{u}" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
  $ahead = git rev-list --count "@{u}..HEAD"
  if ([int]$ahead -gt 0) {
    Write-Host "[알림] GitHub 에 올리지 않은 커밋이 $ahead 개 있습니다. git push 를 잊지 마세요." -ForegroundColor Yellow
  }
}
