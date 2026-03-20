@echo off
setlocal

REM Bu script proje klasorune gecer, bagimliliklari kurar ve uygulamayi baslatir.
cd /d "%~dp0"

REM Kullanilabilir Python komutunu otomatik bul.
set "PY_CMD="
python --version >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD (
  py --version >nul 2>nul && set "PY_CMD=py"
)
if not defined PY_CMD (
  if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PY_CMD=""%LocalAppData%\Programs\Python\Python311\python.exe"""
)
if not defined PY_CMD (
  if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY_CMD=""%LocalAppData%\Programs\Python\Python312\python.exe"""
)
if not defined PY_CMD (
  if exist "%ProgramFiles%\Python311\python.exe" set "PY_CMD=""%ProgramFiles%\Python311\python.exe"""
)
if not defined PY_CMD (
  if exist "%ProgramFiles%\Python312\python.exe" set "PY_CMD=""%ProgramFiles%\Python312\python.exe"""
)

if not defined PY_CMD (
  echo Python bulunamadi.
  echo Cozum:
  echo 1^) Python 3.11+ kurun: https://www.python.org/downloads/
  echo 2^) Kurulumda "Add python.exe to PATH" secenegini isaretleyin.
  echo 3^) Sonra bu .bat dosyasini tekrar calistirin.
  pause
  exit /b 1
)

echo Python komutu: %PY_CMD%

echo [1/3] Pip guncelleniyor...
%PY_CMD% -m pip install --upgrade pip
if errorlevel 1 (
  echo Pip guncellenemedi. Python kurulumunuzu kontrol edin.
  pause
  exit /b 1
)

echo [2/3] Temel gereksinimler kuruluyor...
%PY_CMD% -m pip install "customtkinter>=5.2.0" "nbtlib>=2.0.0"
if errorlevel 1 (
  echo Temel bagimlilik kurulumu basarisiz oldu.
  pause
  exit /b 1
)

echo [2.1/3] amulet-core kurulumu deneniyor (opsiyonel)...
%PY_CMD% -m pip install "amulet-core>=1.0.0"
if errorlevel 1 (
  echo UYARI: amulet-core kurulumu basarisiz oldu.
  echo Uygulama nbtlib fallback ile calismaya devam edecek.
)

echo [3/3] Uygulama baslatiliyor...
%PY_CMD% main.py

if errorlevel 1 (
  echo Uygulama calisirken hata olustu.
)

pause
