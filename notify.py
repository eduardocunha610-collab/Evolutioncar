import os
import json
import urllib.request
import urllib.parse
from datetime import date, datetime

# ==========================================
# CONFIGURAÇÕES
# ==========================================
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID        = os.environ['CHAT_ID']
SUPA_URL       = os.environ['SUPA_URL']
SUPA_KEY       = os.environ['SUPA_KEY']

TODAY = date.today().isoformat()  # ex: 2026-11-12

# ==========================================
# HELPERS
# ==========================================
def supa_get(table, filters=''):
    url = f"{SUPA_URL}/rest/v1/{table}?{filters}"
    req = urllib.request.Request(url, headers={
        'apikey': SUPA_KEY,
        'Authorization': f'Bearer {SUPA_KEY}',
        'Content-Type': 'application/json'
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def telegram_send(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'
    }).encode()
    req = urllib.request.Request(url, data=data)
    urllib.request.urlopen(req)

# ==========================================
# CONTAS A PAGAR — vencimento hoje
# ==========================================
def check_contas():
    rows = supa_get('contas_pagar', 'select=descricao,valor,vencimento,status')
    hoje = [r for r in rows if r.get('vencimento') == TODAY and r.get('status', '').lower() != 'pago']

    if not hoje:
        return

    linhas = []
    for c in hoje:
        valor = f"R$ {c['valor']}" if c.get('valor') else 'Valor não informado'
        linhas.append(f"  • {c['descricao']} — {valor}")

    msg = (
        "🔔 <b>EVOLUTIONCAR — Contas a Pagar</b>\n"
        f"📅 Vencimento <b>hoje</b> ({_fmt(TODAY)}):\n\n"
        + "\n".join(linhas)
        + "\n\n⚠️ Não esqueça de realizar os pagamentos!"
    )
    telegram_send(msg)

# ==========================================
# AGENDAMENTOS — marcados para hoje
# ==========================================
def check_agendamentos():
    rows = supa_get('agendamentos', 'select=nome,veiculo,placa,servico,horario,data')
    hoje = [r for r in rows if r.get('data') == TODAY]

    if not hoje:
        return

    # Ordena por horário
    hoje.sort(key=lambda x: x.get('horario') or '00:00')

    linhas = []
    for a in hoje:
        horario = a.get('horario') or '--:--'
        nome    = a.get('nome') or 'Cliente'
        veiculo = a.get('veiculo') or ''
        placa   = a.get('placa') or ''
        servico = a.get('servico') or ''
        detalhe = ' | '.join(filter(None, [veiculo, placa, servico]))
        linhas.append(f"  🕐 {horario} — <b>{nome}</b>\n      {detalhe}")

    msg = (
        "📅 <b>EVOLUTIONCAR — Agenda do Dia</b>\n"
        f"Data: <b>{_fmt(TODAY)}</b>\n\n"
        + "\n\n".join(linhas)
        + f"\n\n✅ Total: {len(hoje)} agendamento(s) hoje"
    )
    telegram_send(msg)

# ==========================================
# HELPER DE DATA
# ==========================================
def _fmt(iso):
    try:
        d = date.fromisoformat(iso)
        return d.strftime('%d/%m/%Y')
    except:
        return iso

# ==========================================
# MAIN
# ==========================================
if __name__ == '__main__':
    print(f"Verificando para {TODAY}...")
    check_agendamentos()
    check_contas()
    print("Notificações enviadas com sucesso!")
