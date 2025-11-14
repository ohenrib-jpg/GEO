@echo off
REM ====================================
REM Script de démarrage GEOPOL + Mistral
REM ====================================

title GEOPOL - Lancement

echo ========================================
echo    GEOPOL v2.1 - Demarrage
echo ========================================
echo.

REM Configuration
set LLAMA_DIR=llama.cpp
set SERVER_EXE=llama-server.exe
set MODEL_FILE=mistral-7b-v0.2-q4_0.gguf
set LLAMA_PORT=8080
set FLASK_PORT=5000
set GEOPOL_URL=http://localhost:%FLASK_PORT%

echo [1/3] Verification de l'environnement...
echo.

REM Vérifications existantes...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)
echo   [OK] Python detecte

if not exist "%LLAMA_DIR%\%SERVER_EXE%" (
    echo [ERREUR] Serveur Llama introuvable: %LLAMA_DIR%\%SERVER_EXE%
    pause
    exit /b 1
)
echo   [OK] Llama.cpp trouve

if not exist "%LLAMA_DIR%\models\%MODEL_FILE%" (
    echo [ERREUR] Modele introuvable: %LLAMA_DIR%\models\%MODEL_FILE%
    pause
    exit /b 1
)
echo   [OK] Modele Mistral 7B trouve

echo.
echo [2/3] Demarrage du serveur IA Mistral 7B...
echo.

start "Serveur IA Mistral 7B" /D "%LLAMA_DIR%" cmd /k "%SERVER_EXE% -m models\%MODEL_FILE% --host 0.0.0.0 --port %LLAMA_PORT% --ctx-size 4096 --threads 10 --temp 0.1 --repeat-penalty 1.1"

echo   [OK] Serveur IA demarre sur http://localhost:%LLAMA_PORT%
echo   Patientez 15 secondes pour l'initialisation...
timeout /t 15 /nobreak >nul

echo.
echo [3/3] Demarrage de l'application GEOPOL...
echo.

start "GEOPOL Flask" cmd /k ".venv\Scripts\activate.bat && python run.py"

echo   [OK] Application GEOPOL demarree sur http://localhost:%FLASK_PORT%

echo.
echo Attente du demarrage de Flask...
echo Test de la connexion toutes les 5 secondes...

REM Attendre que Flask soit vraiment prêt
set MAX_ATTEMPTS=6
set ATTEMPT=1

:CHECK_FLASK
echo Tentative %ATTEMPT%/%MAX_ATTEMPTS%...
curl --silent --connect-timeout 5 "%GEOPOL_URL%/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [SUCCES] GEOPOL est accessible!
    goto :OPEN_BROWSER
)

if %ATTEMPT% geq %MAX_ATTEMPTS% (
    echo   [ATTENTION] GEOPOL ne repond pas, ouverture quand meme...
    goto :OPEN_BROWSER
)

set /a ATTEMPT+=1
timeout /t 5 /nobreak >nul
goto :CHECK_FLASK

:OPEN_BROWSER
echo.
echo Ouverture de %GEOPOL_URL%...
start "" "%GEOPOL_URL%"

echo.
echo ========================================
echo    GEOPOL est pret !
echo ========================================
echo.
echo  Interface Web : %GEOPOL_URL%
echo  Serveur IA    : http://localhost:%LLAMA_PORT%
echo  Modele        : Mistral 7B v0.2 Q4_0
echo.
echo  Fermez cette fenetre pour tout arreter
echo.
pause