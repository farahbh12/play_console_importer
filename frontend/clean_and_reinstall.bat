@echo off
ECHO Nettoyage du projet frontend...

REM Se deplace dans le repertoire du frontend
cd "c:\Users\halab\OneDrive - ESPRIT\Bureau\projet\play_console_importer\frontend"

REM Supprime le dossier node_modules s'il existe
IF EXIST node_modules (
    ECHO Suppression de node_modules...
    RMDIR /S /Q node_modules
)

REM Supprime le fichier package-lock.json s'il existe
IF EXIST package-lock.json (
    ECHO Suppression de package-lock.json...
    DEL package-lock.json
)

ECHO Reinstallation des dependances...
npm install

ECHO Nettoyage termine. Vous pouvez maintenant relancer le serveur de developpement avec 'npm start'.
