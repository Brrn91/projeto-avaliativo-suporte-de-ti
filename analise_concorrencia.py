"""Cruza janelas do backup com a execucao do job do relatorio (dados sinteticos, somente leitura)."""
import csv
from datetime import datetime

def t(data, hhmm):
    return datetime.fromisoformat(f"{data} {hhmm}")

with open("log_backup.csv") as f:
    backup = {r["data"]: r for r in csv.DictReader(f)}
with open("log_relatorio.csv") as f:
    job = list(csv.DictReader(f))

NOMES = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
linhas, falhas_dia = [], {}
for r in job:
    dia = r["data_execucao"]
    b = backup[dia]
    sobrepos = max(0, int((t(dia, b["fim"]) - t(dia, r["inicio"])).total_seconds() // 60))
    nome = NOMES[datetime.fromisoformat(dia).weekday()]
    if r["status"] == "FALHA":
        falhas_dia[nome] = falhas_dia.get(nome, 0) + 1
    if nome == "dom":
        linhas.append((dia, b["tipo"], b["fim"], b["verificacao_integridade"], sobrepos, r["status"], r["data_consolidada"]))

print(f"{'data':<11}{'backup':<10}{'fim_bkp':<8}{'verif':<6}{'sobrep_min':<11}{'job':<6}{'dado_consolidado'}")
for l in linhas:
    print(f"{l[0]:<11}{l[1]:<10}{l[2]:<8}{l[3]:<6}{l[4]:<11}{l[5]:<6}{l[6]}")

total = len(job)
falhas = sum(1 for r in job if r["status"] == "FALHA")
print(f"\nExecucoes analisadas: {total} | falhas: {falhas} | falhas por dia da semana: {falhas_dia}")
dom_pos = [l for l in linhas if l[3] == "sim"]
dom_pre = [l for l in linhas if l[3] == "nao"]
print(f"Domingos antes da mudanca: {len(dom_pre)} (falhas: {sum(l[5]=='FALHA' for l in dom_pre)})")
print(f"Domingos depois da mudanca: {len(dom_pos)} (falhas: {sum(l[5]=='FALHA' for l in dom_pos)})")
print("Datas sem consolidacao:", [r["data_consolidada"] for r in job if r["status"] == "FALHA"])
