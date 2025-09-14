#!/bin/bash
#
# UDM/UDM Pro - Port Forward 8443 -> LAN backend via iptables (DNAT + FORWARD)
# Uso:
#   ./udm_port_forward_8443.sh
#   ./udm_port_forward_8443.sh --enable-alt
#   ./udm_port_forward_8443.sh --install-onboot
#   ./udm_port_forward_8443.sh --status
#   ./udm_port_forward_8443.sh --sniff
#   ./udm_port_forward_8443.sh --remove
#
# Validação externa (ex.: via 4G):
#   curl -Iv https://mcp.agourakis.med.br:${PUBLIC_PORT:-8443}/health
# Dica: em paralelo, use --sniff para ver pacotes na bridge LAN.

set -euo pipefail

# ===== Config Padrão (pode sobrescrever via env) =====
SERVER_IP="${SERVER_IP:-192.168.4.198}"
WAN_IF="${WAN_IF:-ppp0}"
PUBLIC_PORT="${PUBLIC_PORT:-8443}"
ALT_PUBLIC_PORT="${ALT_PUBLIC_PORT:-10443}"
BACKEND_PORT="${BACKEND_PORT:-8443}"

# Flags (CLI)
ENABLE_ALT=0         # --enable-alt
DO_INSTALL=0         # --install-onboot
DO_REMOVE=0          # --remove
DO_STATUS=0          # --status
DO_SNIFF=0           # --sniff
DO_TEMP80_ADD=0      # --temp80-add
DO_TEMP80_REMOVE=0   # --temp80-remove

LAN_IF=""

log() { echo "[udm-portfwd] $*"; }
err() { echo "[udm-portfwd][ERRO] $*" >&2; }

usage() {
  cat <<EOF
UDM/UDM Pro: Port Forward HTTPS 8443 -> ${SERVER_IP}:${BACKEND_PORT}

Uso:
  $0                 # aplica DNAT ${PUBLIC_PORT} e regras FORWARD
  $0 --enable-alt    # adiciona DNAT alternativo ${ALT_PUBLIC_PORT} -> ${BACKEND_PORT}
  $0 --install-onboot# instala script persistente em /data/on_boot.d/
  $0 --status        # mostra contadores das regras
  $0 --sniff         # tcpdump na bridge LAN detectada
  $0 --remove        # remove regras DNAT/FORWARD criadas
  $0 --temp80-add    # adiciona DNAT/FORWARD temporários para porta 80 -> backend:80
  $0 --temp80-remove # remove regras temporárias da porta 80
  $0 -h | --help     # ajuda

Variáveis (sobrescreva via env se quiser):
  SERVER_IP=${SERVER_IP}  WAN_IF=${WAN_IF}  PUBLIC_PORT=${PUBLIC_PORT}
  ALT_PUBLIC_PORT=${ALT_PUBLIC_PORT}  BACKEND_PORT=${BACKEND_PORT}

Validação externa (ex.: 4G):
  curl -Iv https://mcp.agourakis.med.br:${PUBLIC_PORT}/health
EOF
}

require_root() {
  if [[ $(id -u) -ne 0 ]]; then
    err "Execute como root (ex.: via SSH no UDM).";
    exit 1
  fi
}

detect_lan_if() {
  # Detecta a bridge/interface LAN usada para alcançar SERVER_IP
  # Exemplo: ip -o route get 192.168.4.198 => ... dev br2 src ...
  local dev
  if ! dev=$(ip -o route get "$SERVER_IP" 2>/dev/null | awk '{for(i=1;i<=NF;i++){if($i=="dev"){print $(i+1); exit}}}') || [[ -z "${dev:-}" ]]; then
    err "Não foi possível detectar LAN_IF via 'ip route get'. Verifique SERVER_IP=${SERVER_IP}."
    exit 1
  fi
  LAN_IF="$dev"
  log "LAN_IF detectada: ${LAN_IF} (via rota para ${SERVER_IP})"
}

ensure_dnat() {
  local port="$1"
  # DNAT: tráfego WAN ppp0 TCP dport:port -> SERVER_IP:BACKEND_PORT
  if iptables -t nat -C PREROUTING -i "$WAN_IF" -p tcp --dport "$port" -j DNAT --to-destination "${SERVER_IP}:${BACKEND_PORT}" 2>/dev/null; then
    log "DNAT já existe: WAN(${WAN_IF}) :${port} -> ${SERVER_IP}:${BACKEND_PORT}"
  else
    log "Adicionando DNAT: WAN(${WAN_IF}) :${port} -> ${SERVER_IP}:${BACKEND_PORT}"
    iptables -t nat -I PREROUTING -i "$WAN_IF" -p tcp --dport "$port" -j DNAT --to-destination "${SERVER_IP}:${BACKEND_PORT}"
  fi
}

ensure_forward() {
  # Ida: permitir conexões novas/estabelecidas para o backend
  if iptables -C FORWARD -p tcp -d "$SERVER_IP" --dport "$BACKEND_PORT" -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; then
    log "FORWARD ida já existe (dst ${SERVER_IP}:${BACKEND_PORT})."
  else
    log "Adicionando FORWARD ida (dst ${SERVER_IP}:${BACKEND_PORT})."
    iptables -I FORWARD -p tcp -d "$SERVER_IP" --dport "$BACKEND_PORT" -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT
  fi

  # Volta: permitir pacotes de retorno do backend
  if iptables -C FORWARD -p tcp -s "$SERVER_IP" --sport "$BACKEND_PORT" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; then
    log "FORWARD volta já existe (src ${SERVER_IP}:${BACKEND_PORT})."
  else
    log "Adicionando FORWARD volta (src ${SERVER_IP}:${BACKEND_PORT})."
    iptables -I FORWARD -p tcp -s "$SERVER_IP" --sport "$BACKEND_PORT" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  fi
}

# ---- Regras temporárias para HTTP-01 (porta 80) ----
ensure_dnat_80() {
  if iptables -t nat -C PREROUTING -i "$WAN_IF" -p tcp --dport 80 -j DNAT --to-destination "${SERVER_IP}:80" 2>/dev/null; then
    log "DNAT 80 já existe: WAN(${WAN_IF}) :80 -> ${SERVER_IP}:80"
  else
    log "Adicionando DNAT 80: WAN(${WAN_IF}) :80 -> ${SERVER_IP}:80"
    iptables -t nat -I PREROUTING -i "$WAN_IF" -p tcp --dport 80 -j DNAT --to-destination "${SERVER_IP}:80"
  fi
}

ensure_forward_80() {
  if iptables -C FORWARD -p tcp -d "$SERVER_IP" --dport 80 -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; then
    :
  else
    log "Adicionando FORWARD ida 80 (dst ${SERVER_IP}:80)."
    iptables -I FORWARD -p tcp -d "$SERVER_IP" --dport 80 -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT
  fi
  if iptables -C FORWARD -p tcp -s "$SERVER_IP" --sport 80 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; then
    :
  else
    log "Adicionando FORWARD volta 80 (src ${SERVER_IP}:80)."
    iptables -I FORWARD -p tcp -s "$SERVER_IP" --sport 80 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  fi
}

remove_80_rules() {
  while iptables -t nat -C PREROUTING -i "$WAN_IF" -p tcp --dport 80 -j DNAT --to-destination "${SERVER_IP}:80" 2>/dev/null; do
    log "-D DNAT 80 $WAN_IF:80 -> ${SERVER_IP}:80"
    iptables -t nat -D PREROUTING -i "$WAN_IF" -p tcp --dport 80 -j DNAT --to-destination "${SERVER_IP}:80"
  done
  while iptables -C FORWARD -p tcp -d "$SERVER_IP" --dport 80 -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; do
    log "-D FORWARD ida 80 (dst ${SERVER_IP}:80)"
    iptables -D FORWARD -p tcp -d "$SERVER_IP" --dport 80 -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT
  done
  while iptables -C FORWARD -p tcp -s "$SERVER_IP" --sport 80 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; do
    log "-D FORWARD volta 80 (src ${SERVER_IP}:80)"
    iptables -D FORWARD -p tcp -s "$SERVER_IP" --sport 80 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  done
}

show_status() {
  log "Status das regras relevantes (NAT PREROUTING):"
  iptables -t nat -nvL PREROUTING | grep -E "dpt:(${PUBLIC_PORT}|${ALT_PUBLIC_PORT}|${BACKEND_PORT}|80)" || true
  echo
  log "Status das regras FORWARD (filtro):"
  iptables -nvL FORWARD | grep -E "(${SERVER_IP}|${BACKEND_PORT}|spt:80|dpt:80)" || true
}

test_backend() {
  log "Testando backend na LAN: ${SERVER_IP}:${BACKEND_PORT} (nc/curl)"
  nc -zv "$SERVER_IP" "$BACKEND_PORT" || true
  curl -skI "https://${SERVER_IP}:${BACKEND_PORT}/health" || true
}

sniff_lan() {
  detect_lan_if
  log "Sniffando no LAN_IF=${LAN_IF} para ${SERVER_IP}:${BACKEND_PORT} (Ctrl+C para sair)"
  tcpdump -ni "$LAN_IF" host "$SERVER_IP" and tcp port "$BACKEND_PORT"
}

install_onboot() {
  detect_lan_if
  local dir="/data/on_boot.d"
  local fpath="${dir}/10-portforward-8443.sh"
  mkdir -p "$dir"

  log "Gravando script persistente em ${fpath} (ENABLE_ALT_PUBLIC=${ENABLE_ALT})"
  cat > "$fpath" <<'ONSCRIPT'
#!/bin/sh
# UDM/UDM Pro on-boot: DNAT 8443 (e opcional 10443) -> SERVER_IP:BACKEND_PORT + FORWARD
set -e
PATH=/sbin:/usr/sbin:/bin:/usr/bin

SERVER_IP="__SERVER_IP__"
WAN_IF="__WAN_IF__"
PUBLIC_PORT="__PUBLIC_PORT__"
ALT_PUBLIC_PORT="__ALT_PUBLIC_PORT__"
BACKEND_PORT="__BACKEND_PORT__"
ENABLE_ALT_PUBLIC="__ENABLE_ALT_PLACEHOLDER__"

log() { echo "[on_boot-portfwd] $*"; }

detect_lan_if() {
  dev=""
  LAN_IF=""
  dev=$(ip -o route get "$SERVER_IP" 2>/dev/null | awk '{for(i=1;i<=NF;i++){if($i=="dev"){print $(i+1); exit}}}') || dev=""
  [ "${dev}" != "" ] || { log "Falha ao detectar LAN_IF"; exit 1; }
  LAN_IF="${dev}"
  log "LAN_IF: $LAN_IF"
}

ensure_dnat() {
  port="$1"
  if iptables -t nat -C PREROUTING -i "$WAN_IF" -p tcp --dport "$port" -j DNAT --to-destination "$SERVER_IP:$BACKEND_PORT" 2>/dev/null; then
    log "DNAT existe: $WAN_IF:$port -> $SERVER_IP:$BACKEND_PORT"
  else
    log "Add DNAT: $WAN_IF:$port -> $SERVER_IP:$BACKEND_PORT"
    iptables -t nat -I PREROUTING -i "$WAN_IF" -p tcp --dport "$port" -j DNAT --to-destination "$SERVER_IP:$BACKEND_PORT"
  fi
}

ensure_forward() {
  if iptables -C FORWARD -p tcp -d "$SERVER_IP" --dport "$BACKEND_PORT" -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; then :; else
    iptables -I FORWARD -p tcp -d "$SERVER_IP" --dport "$BACKEND_PORT" -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT
  fi
  if iptables -C FORWARD -p tcp -s "$SERVER_IP" --sport "$BACKEND_PORT" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; then :; else
    iptables -I FORWARD -p tcp -s "$SERVER_IP" --sport "$BACKEND_PORT" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  fi
}

detect_lan_if
ensure_dnat "$PUBLIC_PORT"
[ "$ENABLE_ALT_PUBLIC" = "1" ] && ensure_dnat "$ALT_PUBLIC_PORT" || true
ensure_forward
exit 0
ONSCRIPT

  # Preenche placeholders com valores atuais
  sed -i \
    -e "s/__SERVER_IP__/${SERVER_IP}/" \
    -e "s/__WAN_IF__/${WAN_IF}/" \
    -e "s/__PUBLIC_PORT__/${PUBLIC_PORT}/" \
    -e "s/__ALT_PUBLIC_PORT__/${ALT_PUBLIC_PORT}/" \
    -e "s/__BACKEND_PORT__/${BACKEND_PORT}/" \
    -e "s/__ENABLE_ALT_PLACEHOLDER__/${ENABLE_ALT}/" \
    "$fpath"
  chmod +x "$fpath"
  log "Executando script on-boot para validar imediatamente..."
  "$fpath" || true
  log "Instalação concluída. Regras aplicadas e serão re-aplicadas no boot."
}

remove_rules() {
  log "Removendo regras DNAT/FORWARD correspondentes..."

  # Remove DNAT (ambos ports, se existirem)
  for port in "$PUBLIC_PORT" "$ALT_PUBLIC_PORT"; do
    while iptables -t nat -C PREROUTING -i "$WAN_IF" -p tcp --dport "$port" -j DNAT --to-destination "${SERVER_IP}:${BACKEND_PORT}" 2>/dev/null; do
      log "-D DNAT $WAN_IF:$port -> ${SERVER_IP}:${BACKEND_PORT}"
      iptables -t nat -D PREROUTING -i "$WAN_IF" -p tcp --dport "$port" -j DNAT --to-destination "${SERVER_IP}:${BACKEND_PORT}"
    done
  done

  # Remove FORWARD ida/volta
  while iptables -C FORWARD -p tcp -d "$SERVER_IP" --dport "$BACKEND_PORT" -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; do
    log "-D FORWARD ida (dst ${SERVER_IP}:${BACKEND_PORT})"
    iptables -D FORWARD -p tcp -d "$SERVER_IP" --dport "$BACKEND_PORT" -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT
  done
  while iptables -C FORWARD -p tcp -s "$SERVER_IP" --sport "$BACKEND_PORT" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; do
    log "-D FORWARD volta (src ${SERVER_IP}:${BACKEND_PORT})"
    iptables -D FORWARD -p tcp -s "$SERVER_IP" --sport "$BACKEND_PORT" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  done

  log "Remoção concluída."
}

main() {
  require_root

  # Parse args
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --enable-alt) ENABLE_ALT=1; shift ;;
      --install-onboot) DO_INSTALL=1; shift ;;
      --remove) DO_REMOVE=1; shift ;;
      --temp80-add) DO_TEMP80_ADD=1; shift ;;
      --temp80-remove) DO_TEMP80_REMOVE=1; shift ;;
      --status) DO_STATUS=1; shift ;;
      --sniff) DO_SNIFF=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) err "Flag desconhecida: $1"; usage; exit 1 ;;
    esac
  done

  if [[ "$DO_REMOVE" -eq 1 ]]; then
    remove_rules
    show_status
    exit 0
  fi

  if [[ "$DO_STATUS" -eq 1 ]]; then
    show_status
    exit 0
  fi

  if [[ "$DO_TEMP80_ADD" -eq 1 ]]; then
    detect_lan_if
    ensure_dnat_80
    ensure_forward_80
    show_status
    exit 0
  fi

  if [[ "$DO_TEMP80_REMOVE" -eq 1 ]]; then
    remove_80_rules
    show_status
    exit 0
  fi

  if [[ "$DO_SNIFF" -eq 1 ]]; then
    sniff_lan
    exit 0
  fi

  # Fluxo padrão: aplicar regras e testar
  detect_lan_if
  ensure_dnat "$PUBLIC_PORT"
  if [[ "$ENABLE_ALT" -eq 1 ]]; then
    ensure_dnat "$ALT_PUBLIC_PORT"
  fi
  ensure_forward
  test_backend
  show_status

  log "Para teste externo, rode (ex.: 4G):"
  echo "  curl -Iv https://mcp.agourakis.med.br:${PUBLIC_PORT}/health"
  if [[ "$ENABLE_ALT" -eq 1 ]]; then
    echo "  (alternativo) curl -Iv https://mcp.agourakis.med.br:${ALT_PUBLIC_PORT}/health"
  fi
  log "Dica: em paralelo, use '$0 --sniff' para observar pacotes na bridge ${LAN_IF}."

  if [[ "$DO_INSTALL" -eq 1 ]]; then
    install_onboot
    exit 0
  else
    echo
    log "Persistência: execute '$0 --install-onboot' para gravar em /data/on_boot.d/."
  fi
}

main "$@"
