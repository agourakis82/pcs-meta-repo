<#
Atualiza automaticamente o portproxy do Windows para encaminhar:
  - 0.0.0.0:8443 -> WSL:8443
  - 0.0.0.0:10443 -> WSL:8443 (opcional com -EnableAlt)

Pré-requisitos:
- Executar como Administrador (elevado)
- Serviço iphlpsvc ativo para portproxy
- WSL instalado e com IP IPv4 acessível (wsl hostname -I)

Uso:
  .\\update_wsl_portproxy.ps1                # atualiza 8443
  .\\update_wsl_portproxy.ps1 -EnableAlt      # atualiza 8443 e 10443
  .\\update_wsl_portproxy.ps1 -Remove         # remove regras 8443/10443

Agendamento (executar em PowerShell Admin):
  $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"C:\\caminho\\update_wsl_portproxy.ps1`" -EnableAlt"
  $trigger = New-ScheduledTaskTrigger -AtLogOn
  Register-ScheduledTask -TaskName 'UpdateWSLPortProxy' -Action $action -Trigger $trigger -RunLevel Highest -Force
#>

[CmdletBinding()]
param(
  [switch]$EnableAlt,
  [switch]$EnableHttp,
  [switch]$Remove,
  [switch]$RemoveHttp
)

function Assert-Admin {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $isAdmin) { throw 'Execute em PowerShell como Administrador.' }
}

function Ensure-IpHelpSvc {
  $svc = Get-Service -Name iphlpsvc -ErrorAction SilentlyContinue
  if (-not $svc) { throw 'Serviço iphlpsvc não encontrado.' }
  if ($svc.Status -ne 'Running') { Start-Service iphlpsvc | Out-Null }
}

function Get-WSLIPv4 {
  $raw = wsl hostname -I 2>$null
  if (-not $raw) { throw 'Falha ao obter IP do WSL (hostname -I).' }
  $ip = ($raw.Trim().Split() | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' })[0]
  if (-not $ip) { throw "Nenhum IPv4 válido detectado no WSL: '$raw'" }
  return $ip
}

function Ensure-FirewallRule($Port) {
  $name = "Nginx ${Port} WSL"
  if (-not (Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $name -Direction Inbound -LocalPort $Port -Protocol TCP -Action Allow -Profile Any | Out-Null
  }
}

function Add-PortProxy($ListenAddress, $ListenPort, $ConnectAddress, $ConnectPort) {
  # Remove entradas conflitantes
  foreach ($addr in @('127.0.0.1','0.0.0.0',$ListenAddress)) {
    netsh interface portproxy delete v4tov4 listenaddress=$addr listenport=$ListenPort 2>$null | Out-Null
  }
  # Adiciona mapeamento
  netsh interface portproxy add v4tov4 listenaddress=$ListenAddress listenport=$ListenPort connectaddress=$ConnectAddress connectport=$ConnectPort | Out-Null
}

function Remove-PortProxy($ListenPort) {
  foreach ($addr in @('127.0.0.1','0.0.0.0','192.168.4.198')) {
    netsh interface portproxy delete v4tov4 listenaddress=$addr listenport=$ListenPort 2>$null | Out-Null
  }
}

try {
  Assert-Admin
  Ensure-IpHelpSvc

  if ($Remove) {
    Remove-PortProxy -ListenPort 8443
    Remove-PortProxy -ListenPort 10443
    if ($RemoveHttp) { Remove-PortProxy -ListenPort 80 }
    Write-Host '[portproxy] Regras 8443/10443 removidas.'
    if ($RemoveHttp) { Write-Host '[portproxy] Regra 80 removida.' }
    exit 0
  }

  $wslIp = Get-WSLIPv4
  $listenAddr = '0.0.0.0'   # ouvir em todas as interfaces

  Ensure-FirewallRule -Port 8443
  Add-PortProxy -ListenAddress $listenAddr -ListenPort 8443 -ConnectAddress $wslIp -ConnectPort 8443
  Write-Host "[portproxy] 0.0.0.0:8443 -> $wslIp:8443"

  if ($EnableAlt) {
    Ensure-FirewallRule -Port 10443
    Add-PortProxy -ListenAddress $listenAddr -ListenPort 10443 -ConnectAddress $wslIp -ConnectPort 8443
    Write-Host "[portproxy] 0.0.0.0:10443 -> $wslIp:8443"
  }

  if ($EnableHttp) {
    Ensure-FirewallRule -Port 80
    Add-PortProxy -ListenAddress $listenAddr -ListenPort 80 -ConnectAddress $wslIp -ConnectPort 80
    Write-Host "[portproxy] 0.0.0.0:80 -> $wslIp:80"
  }

  Write-Host '[portproxy] Estado atual:'
  netsh interface portproxy show v4tov4
}
catch {
  Write-Error $_
  exit 1
}
