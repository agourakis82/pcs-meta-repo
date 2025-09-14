@echo off
REM Script para migrar WSL para o disco D:
REM Execute como Administrador no Prompt de Comando do Windows

REM 1. Defina o nome da sua distribuição atual (veja com: wsl -l)
set DISTRO=Ubuntu
REM 2. Defina o novo nome da distribuição (pode ser igual ou diferente)
set NOVO=UbuntuNovo
REM 3. Defina o caminho de destino no D:
set DESTINO=D:\WSL-Ubuntu

REM 4. Crie a pasta de destino
mkdir "%DESTINO%"

REM 5. Exporte a distribuição atual
wsl --export %DISTRO% "%DESTINO%\%DISTRO%-backup.tar"

REM 6. Desinstale a distribuição antiga
wsl --unregister %DISTRO%

REM 7. Importe a distribuição para o D:
wsl --import %NOVO% "%DESTINO%" "%DESTINO%\%DISTRO%-backup.tar"

REM 8. Abra o novo WSL
echo Abra o novo WSL com: wsl -d %NOVO%

REM 9. (Opcional) Remova o backup após testar
echo Para remover o backup: del "%DESTINO%\%DISTRO%-backup.tar"

echo Migração concluída!
