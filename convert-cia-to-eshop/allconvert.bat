@echo off
setlocal enabledelayedexpansion

REM Vérifier si le fichier cia-helper.py existe, sinon le télécharger
if not exist cia-helper.py (
    echo Téléchargement de cia-helper.py...
    curl -o cia-helper.py https://raw.githubusercontent.com/ghost-land/3dserver/main/cia-helper.py
)

REM Vérifier si le fichier cia-helper.py a été téléchargé avec succès
if not exist cia-helper.py (
    echo Erreur : Impossible de télécharger cia-helper.py. Vérifiez votre connexion Internet et réessayez.
    pause
    exit /b
)

REM Obtient la date et l'heure actuelles pour le nom du fichier journal
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (
    set "date=%%a-%%b-%%c"
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set "time=%%a-%%b"
)
set "timestamp=!date!_!time!"

REM Vérifier si le dossier log existe, sinon le créer
if not exist log (
    mkdir log
)

REM Vérifier si le dossier CIAs existe, sinon le créer
if not exist CIAs (
    mkdir CIAs
)

REM Créer un fichier journal complet avec la date et l'heure dans son nom
set "full_log_file=log\FullLog_!timestamp!.log"
echo Traitement commencé à : %timestamp% > %full_log_file%
echo Traitement commencé à : %timestamp%

REM Boucle à travers tous les fichiers .cia dans le répertoire actuel
for %%F in (*.cia) do (
    REM Créer un fichier journal pour chaque fichier .cia
    set "log_file=log\%%~nF_!timestamp!.log"
    echo Traitement de %%F à : !time! > !log_file!
    echo Traitement de %%F à : !time!

    REM Exécuter la commande Python pour chaque fichier .cia
    python cia-helper.py "%%F" >> !log_file! 2>&1
    
    REM Déplacer le fichier .cia traité dans le dossier CIAs
    move "%%F" CIAs\
)

echo Traitement terminé. Les fichiers .cia ont été déplacés dans le dossier CIAs. Voir le journal complet pour plus de détails.
echo Traitement terminé. Les fichiers .cia ont été déplacés dans le dossier CIAs. Voir le journal complet pour plus de détails. >> %full_log_file%
pause
