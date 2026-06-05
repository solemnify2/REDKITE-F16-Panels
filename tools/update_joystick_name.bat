@echo off
chcp 65001 >nul

set "BASE=HKCU\System\CurrentControlSet\Control\MediaProperties\PrivateProperties\Joystick\OEM"

reg query "%BASE%\VID_16C0&PID_0487" >nul 2>&1 && (
    reg add "%BASE%\VID_16C0&PID_0487" /v OEMName /t REG_SZ /d "REDKITE F16 Left Aux Misc" /f >nul
    echo [OK] Left Aux Misc
) || echo [SKIP] Left Aux Misc -- 키 없음

reg query "%BASE%\VID_16C0&PID_048E" >nul 2>&1 && (
    reg add "%BASE%\VID_16C0&PID_048E" /v OEMName /t REG_SZ /d "REDKITE F16 Left Console" /f >nul
    echo [OK] Left Console
) || echo [SKIP] Left Console -- 키 없음

echo.
echo joy.cpl을 다시 열어 확인하세요.
pause
