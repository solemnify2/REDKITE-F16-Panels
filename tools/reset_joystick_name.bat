<# :
@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([scriptblock]::Create((Get-Content -LiteralPath '%~f0' -Raw -Encoding UTF8)))"
pause
goto :eof
#>

$VID = "VID_16C0"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "Teensy ($VID) joystick cache reset" -ForegroundColor Cyan
Write-Host ""

# --- check if Teensy is plugged in ---
$plugged = Get-PnpDevice | Where-Object { $_.InstanceId -like "*$VID*" -and $_.Status -eq "OK" }
if ($plugged) {
    Write-Host "[!] Teensy connected. Unplug all devices first." -ForegroundColor Red
    Write-Host ""
    $plugged | Format-Table InstanceId, FriendlyName -AutoSize
    exit 1
}

$count = 0

# === 1. Joystick OEM cache (HKCU + HKLM) ===
Write-Host "--- 1. Joystick OEM cache ---" -ForegroundColor Yellow
foreach ($hive in @("HKCU", "HKLM")) {
    $base = "${hive}:\System\CurrentControlSet\Control\MediaProperties\PrivateProperties\Joystick\OEM"
    if (Test-Path $base) {
        Get-ChildItem $base | Where-Object { $_.PSChildName -like "*$VID*" } | ForEach-Object {
            $name = $_.PSChildName
            $oemName = (Get-ItemProperty $_.PSPath -Name OEMName -ErrorAction SilentlyContinue).OEMName
            Remove-Item $_.PSPath -Recurse -Force -ErrorAction SilentlyContinue
            $label = if ($oemName) { "$name `"$oemName`"" } else { $name }
            Write-Host "  [OK] $hive $label" -ForegroundColor Green
            $script:count++
        }
    }
}

# === 2. PnP device removal ===
Write-Host "--- 2. PnP device removal ---" -ForegroundColor Yellow
$devices = Get-PnpDevice | Where-Object { $_.InstanceId -like "*$VID*" }
foreach ($dev in $devices) {
    $id = $dev.InstanceId
    $null = & pnputil /remove-device "$id" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] $id" -ForegroundColor Green
        $count++
    } else {
        Write-Host "  [FAIL] $id" -ForegroundColor Red
    }
}

Write-Host ""
if ($count -eq 0) {
    Write-Host "Nothing to clean."
} else {
    Write-Host "$count items removed." -ForegroundColor Cyan
    Write-Host "Replug devices to register with new names."
}
