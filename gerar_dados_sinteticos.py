"""Gera logs SINTETICOS do caso (nenhum dado real). Os dados codificam o cenario do caso:
backup completo aos domingos 01h00; verificacao de integridade ativada em 05/11/2026 (CHG-0457)."""
import csv
from datetime import date, datetime, timedelta

INI, FIM, MUDANCA = date(2026, 10, 25), date(2026, 11, 23), date(2026, 11, 5)

def hm(d, h, m):
    return datetime(d.year, d.month, d.day, h, m)

backup, job = [], []
d = INI
while d <= FIM:
    domingo = d.weekday() == 6
    pos = d > MUDANCA
    if domingo:
        fim_b = hm(d, 3, 15) if pos else hm(d, 2, 20)
        tipo = "completo"
    else:
        fim_b = hm(d, 1, 35) if pos else hm(d, 1, 25)
        tipo = "incremental"
    backup.append([d.isoformat(), tipo, hm(d, 1, 0).strftime("%H:%M"), fim_b.strftime("%H:%M"),
                   "sim" if pos else "nao"])
    # job do relatorio: 02h30, espera lock por no maximo 30 min (1800 s)
    ini_j = hm(d, 2, 30)
    alvo = (d - timedelta(days=1)).isoformat()
    if fim_b > ini_j + timedelta(minutes=30):
        job.append([d.isoformat(), alvo, "02:30", "03:00", "FALHA",
                    "LOCK_TIMEOUT: aguardando bloqueio em vendas_consolidadas (1800s)", 0])
    else:
        espera = max(0, int((fim_b - ini_j).total_seconds() // 60))
        fim_j = ini_j + timedelta(minutes=20 + espera)
        job.append([d.isoformat(), alvo, "02:30", fim_j.strftime("%H:%M"), "OK",
                    "consolidacao concluida", 1100 + (d.toordinal() * 37) % 260])
    d += timedelta(days=1)

with open("log_backup.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["data", "tipo", "inicio", "fim", "verificacao_integridade"]); w.writerows(backup)
with open("log_relatorio.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["data_execucao", "data_consolidada", "inicio", "fim", "status", "mensagem", "registros"])
    w.writerows(job)
print("Gerados: log_backup.csv, log_relatorio.csv")
