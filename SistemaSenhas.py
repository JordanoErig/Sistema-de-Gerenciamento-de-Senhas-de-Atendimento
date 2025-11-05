import tkinter as tk
from collections import deque
import random

try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
except Exception:
    raise RuntimeError("ttkbootstrap não encontrado. Instale com: py -m pip install ttkbootstrap")

# Configurações
POSTOS_MAX = 5
MIN_AT = 3
STATUS_PADRAO = "Sistema de Atendimento Ativo."
TIMEOUT_STATUS_MS = 5000

random.seed(None)

# Estado
filaN: deque = deque()
filaP: deque = deque()
pilha: list = []
cont = {"emitN": 0, "emitP": 0, "atend": 0, "desist": 0}

postos = []
for i in range(POSTOS_MAX):
    postos.append({"id": i + 1, "ativo": (i < MIN_AT), "atual": None})

ciclo = ["N", "N", "P"]
idx_ciclo = 0
proxN = 1
proxP = 1

# Motor de regras
def emitir(tipo: str) -> str:
    global proxN, proxP
    if tipo == "N":
        cod = f"N{proxN:03d}"
        filaN.append(cod)
        cont["emitN"] += 1
        proxN += 1
        return cod
    cod = f"P{proxP:03d}"
    filaP.append(cod)
    cont["emitP"] += 1
    proxP += 1
    return cod

def proximos_tipos(n: int = 2) -> list:
    temp = []
    temp_idx = idx_ciclo
    nN = len(filaN)
    nP = len(filaP)
    checks = 0
    while len(temp) < n and checks < 12:
        t = ciclo[temp_idx % len(ciclo)]
        if t == "N" and nN > 0:
            temp.append("N")
            nN -= 1
            temp_idx += 1
        elif t == "P" and nP > 0:
            temp.append("P")
            nP -= 1
            temp_idx += 1
        else:
            temp_idx += 1
        checks += 1
    while len(temp) < n:
        if len(filaP) > 0:
            temp.append("P")
        elif len(filaN) > 0:
            temp.append("N")
        else:
            temp.append(None)
    return temp

def proximas_senhas(n: int = 2) -> list:
    tempN = deque(filaN)
    tempP = deque(filaP)
    temp_idx = idx_ciclo
    res = []
    checks = 0
    while len(res) < n and checks < 12:
        t = ciclo[temp_idx % len(ciclo)]
        if t == "N" and len(tempN) > 0:
            res.append(tempN.popleft())
            temp_idx += 1
        elif t == "P" and len(tempP) > 0:
            res.append(tempP.popleft())
            temp_idx += 1
        else:
            temp_idx += 1
        checks += 1
    while len(res) < n:
        if len(tempP) > 0:
            res.append(tempP.popleft())
        elif len(tempN) > 0:
            res.append(tempN.popleft())
        else:
            res.append(None)
    return res

def chamar():
    global idx_ciclo
    tent = 0
    while tent < 6:
        t = ciclo[idx_ciclo % len(ciclo)]
        if t == "N" and len(filaN) > 0:
            idx_ciclo = (idx_ciclo + 1) % len(ciclo)
            return filaN.popleft(), "N"
        if t == "P" and len(filaP) > 0:
            idx_ciclo = (idx_ciclo + 1) % len(ciclo)
            return filaP.popleft(), "P"
        idx_ciclo = (idx_ciclo + 1) % len(ciclo)
        tent += 1
    if len(filaP) > 0:
        return filaP.popleft(), "P"
    if len(filaN) > 0:
        return filaN.popleft(), "N"
    return None, None

def atribuir_posto_livre(senha: str):
    for p in postos:
        if p["ativo"] and p["atual"] is None:
            p["atual"] = senha
            return p["id"]
    return None

def finalizar_posto(posto_id: int) -> bool:
    idx = posto_id - 1
    p = postos[idx]
    if p["atual"] is None:
        return False
    s = p["atual"]
    pilha.append(s)
    cont["atend"] += 1
    p["atual"] = None
    return True

def desistir_aleatorio():
    total = len(filaN) + len(filaP)
    if total == 0:
        return None
    if len(filaN) == 0:
        c = filaP.popleft()
        cont["desist"] += 1
        return c
    if len(filaP) == 0:
        c = filaN.popleft()
        cont["desist"] += 1
        return c
    r = random.random()
    probN = len(filaN) / (len(filaN) + len(filaP))
    if r < probN:
        c = filaN.popleft()
    else:
        c = filaP.popleft()
    cont["desist"] += 1
    return c

def alternar_posto(posto_id: int) -> tuple:
    idx = posto_id - 1
    if postos[idx]["atual"] is not None:
        return False, "Posto ocupado — finalize antes de desativar."
    ativos = sum(1 for x in postos if x["ativo"])
    if postos[idx]["ativo"]:
        if ativos <= MIN_AT:
            return False, f"Não é permitido ter menos que {MIN_AT} postos ativos."
        postos[idx]["ativo"] = False
        return True, "Posto desativado."
    postos[idx]["ativo"] = True
    return True, "Posto ativado."


class App(tb.Window):
    def __init__(self):
        super().__init__(themename="solar")
        self.title("Sistema de Senhas — EDL 2025/2")
        self.geometry("1220x760")
        self.minsize(1000, 620)

        self.fnt_grande = ("Segoe UI", 56, "bold")
        self.fnt_med = ("Segoe UI", 12)
        self.fnt_peq = ("Segoe UI", 10)

        self._montar()
        self.atualizar()

    def set_status(self, msg: str, nivel: str = "secondary"):
        mapa = {"success": "success", "warning": "warning", "danger": "danger", "secondary": "secondary"}
        boot = mapa.get(nivel, "secondary")
        try:
            self.status_lbl.configure(text=msg)
            try:
                self.status_lbl.configure(bootstyle=boot)
            except Exception:
                pass
            if hasattr(self, "_after_id") and self._after_id is not None:
                try:
                    self.after_cancel(self._after_id)
                except Exception:
                    pass
            self._after_id = self.after(TIMEOUT_STATUS_MS, self.clear_status)
        except Exception:
            pass

    def clear_status(self):
        if hasattr(self, "status_lbl"):
            try:
                self.status_lbl.configure(text=STATUS_PADRAO)
                try:
                    self.status_lbl.configure(bootstyle="secondary")
                except Exception:
                    pass
            except Exception:
                pass
        if hasattr(self, "_after_id"):
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _montar(self):
        top = tb.Frame(self, padding=10)
        top.pack(side="top", fill="x")

        banner = tb.Frame(top)
        banner.pack(side="top", fill="x")

        self.status_frame = tb.Frame(top, padding=(4, 4, 4, 4))
        self.status_frame.pack(side="top", fill="x", padx=12, pady=(6, 0))
        self.status_lbl = tb.Label(self.status_frame, text=STATUS_PADRAO, font=("Segoe UI", 10), bootstyle="secondary")
        self.status_lbl.pack(side="left", anchor="w", padx=6, pady=2)
        self._after_id = None

        card = tb.Frame(banner, bootstyle="primary", padding=16, relief="ridge")
        card.pack(side="left", padx=12, pady=8, ipadx=8, ipady=8, fill="x", expand=True)

        tb.Label(card, text="PRÓXIMA SENHA", font=("Segoe UI", 12, "bold"), bootstyle="inverse").pack(anchor="nw")
        self.lbl_grande = tb.Label(card, text="-", font=self.fnt_grande, bootstyle="inverse")
        self.lbl_grande.pack(anchor="center", pady=(6, 4))
        self.lbl_dir = tb.Label(card, text="Aguardando chamada...", font=("Segoe UI", 11), bootstyle="inverse")
        self.lbl_dir.pack(anchor="s", pady=(2, 0))

        stats = tb.Frame(banner, bootstyle="secondary", padding=12, relief="ridge", width=380)
        stats.pack(side="right", padx=12, pady=8)
        stats.pack_propagate(False)

        self.lbl_total = tb.Label(stats, text="Fila total: 0", font=self.fnt_med)
        self.lbl_total.pack(anchor="nw")
        self.lbl_prox2 = tb.Label(stats, text="Próximas: - , -", font=self.fnt_peq)
        self.lbl_prox2.pack(anchor="nw", pady=(8, 0))
        self.lbl_para = tb.Label(stats, text="Próxima deve ir: -", font=self.fnt_peq)
        self.lbl_para.pack(anchor="nw", pady=(6, 0))
        self.lbl_emit = tb.Label(stats, text="Emitidas N: 0   P: 0", font=self.fnt_peq)
        self.lbl_emit.pack(anchor="nw", pady=(8, 0))
        self.lbl_extras = tb.Label(stats, text="Atendidas: 0   Desist.: 0", font=self.fnt_peq)
        self.lbl_extras.pack(anchor="nw", pady=(4, 0))

        main = tb.Frame(self, padding=10)
        main.pack(side="top", fill="both", expand=True)

        left = tb.Frame(main, width=360)
        left.pack(side="left", fill="y", padx=(6, 12))
        left.pack_propagate(False)

        tb.Label(left, text="Controles do Operador", font=("Segoe UI", 14, "bold")).pack(anchor="nw", pady=(6, 10))

        tb.Button(left, text="Emitir Senha NORMAL (N)", bootstyle="success-outline", width=30, command=self.emitirN).pack(pady=8)
        tb.Button(left, text="Emitir Senha PRIORITÁRIA (P)", bootstyle="warning-outline", width=30, command=self.emitirP).pack(pady=8)

        tb.Separator(left).pack(fill="x", pady=10)

        tb.Button(left, text="Chamar Próxima (2N : 1P)", bootstyle="info", width=30, command=self.chamar_ui).pack(pady=6)
        tb.Button(left, text="Desistência Aleatória (D1)", bootstyle="danger-outline", width=30, command=self.desistir_ui).pack(pady=6)

        tb.Separator(left).pack(fill="x", pady=10)

        tb.Label(left, text="Gerenciar Postos", font=self.fnt_med).pack(anchor="nw", pady=(4, 6))

        self.toggle_btns = []
        for p in postos:
            row = tb.Frame(left)
            row.pack(fill="x", pady=4)
            tb.Label(row, text=f"Posto {p['id']}", width=8).pack(side="left", padx=(4, 8))
            btn = tb.Button(row, text="Ativar/Desativar", bootstyle="secondary", width=18, command=lambda pid=p['id']: self.alternar_posto_ui(pid))
            btn.pack(side="left")
            self.toggle_btns.append(btn)

        tb.Separator(left).pack(fill="x", pady=10)

        tb.Button(left, text="Encerrar Atendimento (Mostrar Pilha)", bootstyle="dark", width=30, command=self.encerrar_ui).pack(pady=6)

        right = tb.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        filas = tb.Frame(right)
        filas.pack(side="top", fill="x", pady=(0, 10))

        cardN = tb.Frame(filas, bootstyle="light", padding=8, relief="ridge")
        cardN.pack(side="left", fill="both", expand=True, padx=6)
        tb.Label(cardN, text="Fila - Normais (N)", font=("Segoe UI", 12, "bold")).pack(anchor="nw")
        self.listN = tk.Listbox(cardN, height=8, font=("Consolas", 11))
        self.listN.pack(fill="both", expand=True, pady=6)

        cardP = tb.Frame(filas, bootstyle="light", padding=8, relief="ridge")
        cardP.pack(side="left", fill="both", expand=True, padx=6)
        tb.Label(cardP, text="Fila - Prioritárias (P)", font=("Segoe UI", 12, "bold")).pack(anchor="nw")
        self.listP = tk.Listbox(cardP, height=8, font=("Consolas", 11))
        self.listP.pack(fill="both", expand=True, pady=6)

        postos_card = tb.Frame(right, bootstyle="secondary", padding=8, relief="ridge")
        postos_card.pack(side="top", fill="both", expand=True, pady=(0, 8))
        tb.Label(postos_card, text="Postos de Atendimento", font=("Segoe UI", 12, "bold")).pack(anchor="nw")

        self.postos_box = tb.Frame(postos_card)
        self.postos_box.pack(fill="both", expand=True, pady=8)

        self.posto_widgets = []
        for p in postos:
            f = tb.Frame(self.postos_box, bootstyle="light", padding=8, relief="flat")
            tb.Label(f, text=f"Posto {p['id']}", font=("Segoe UI", 11, "bold")).pack(anchor="nw")
            st = tk.StringVar()
            tb.Label(f, textvariable=st).pack(anchor="nw", pady=(6, 4))
            btnf = tb.Button(f, text="Finalizar Atendimento", bootstyle="success", width=16, command=lambda pid=p['id']: self.finalizar_posto_ui(pid))
            btnf.pack(anchor="se", pady=(6, 0))
            self.posto_widgets.append({"frame": f, "st": st, "btn": btnf})

        self._arranjar()

        atend_card = tb.Frame(right, bootstyle="light", padding=8, relief="ridge")
        atend_card.pack(side="bottom", fill="x")
        tb.Label(atend_card, text="Atendimentos (pilha - topo = último atendido)", font=("Segoe UI", 12, "bold")).pack(anchor="nw")
        self.txt_atendidos = tk.Text(atend_card, height=8, state="disabled", font=("Consolas", 11))
        self.txt_atendidos.pack(fill="both", expand=True, pady=6)

        footer = tb.Frame(self, padding=6)
        footer.pack(side="bottom", fill="x")
        self.lbl_contadores = tb.Label(footer, text="Atendidas: 0    Desistências: 0    Emitidas N: 0    Emitidas P: 0", font=self.fnt_peq)
        self.lbl_contadores.pack(side="left", padx=8)

    def _arranjar(self):
        for w in self.posto_widgets:
            w["frame"].pack_forget()
        for idx, w in enumerate(self.posto_widgets):
            w["frame"].pack(side="left", padx=8, pady=8, ipadx=10, ipady=6)

    def emitirN(self):
        c = emitir("N")
        self.set_status(f"Emitida {c}", nivel="success")
        self.atualizar()

    def emitirP(self):
        c = emitir("P")
        self.set_status(f"Emitida {c}", nivel="success")
        self.atualizar()

    def chamar_ui(self):
        s, t = chamar()
        if s is None:
            self.set_status("Nenhuma senha para chamar.", nivel="warning")
            return
        pid = atribuir_posto_livre(s)
        if pid is None:
            if t == "N":
                filaN.appendleft(s)
            else:
                filaP.appendleft(s)
            self.set_status("Sem posto livre. Finalize um atendimento para liberar.", nivel="warning")
        else:
            self.set_status(f"Chamado {s} -> Posto {pid}", nivel="secondary")
        self.atualizar()

    def desistir_ui(self):
        c = desistir_aleatorio()
        if c is None:
            self.set_status("Nenhuma pessoa na fila para desistir.", nivel="warning")
        else:
            self.set_status(f"Desistência: {c}", nivel="warning")
        self.atualizar()

    def alternar_posto_ui(self, pid):
        ok, msg = alternar_posto(pid)
        if not ok:
            self.set_status(msg, nivel="warning")
        else:
            self.set_status(msg, nivel="success")
        self.atualizar()

    def finalizar_posto_ui(self, pid):
        ok = finalizar_posto(pid)
        if not ok:
            self.set_status(f"Posto {pid} está livre.", nivel="warning")
        else:
            self.set_status(f"Atendimento finalizado no Posto {pid}.", nivel="success")
        self.atualizar()

    def encerrar_ui(self):
        if len(pilha) == 0:
            self.set_status("Nenhuma senha atendida ainda.", nivel="warning")
            return
        texto = "ATENDIMENTOS (do último para o primeiro):\n"
        for i, s in enumerate(reversed(pilha), start=1):
            texto += f"{i:03d}: {s}\n"
        texto += f"\nTotal atendidos: {cont['atend']}\nDesistências: {cont['desist']}"
        top = tb.Toplevel(self)
        top.title("Encerramento - Pilha de Atendidos")
        txt = tk.Text(top, width=60, height=30)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", texto)
        txt.configure(state="disabled")

    # atualizar interface
    def atualizar(self):
        self.listN.delete(0, tk.END)
        for s in list(filaN):
            self.listN.insert(tk.END, s)
        self.listP.delete(0, tk.END)
        for s in list(filaP):
            self.listP.insert(tk.END, s)

        total = len(filaN) + len(filaP)
        self.lbl_total.configure(text=f"Fila total: {total}")

        prox = proximas_senhas(2)
        prox_txt = ", ".join([p if p is not None else "-" for p in prox])
        self.lbl_prox2.configure(text=f"Próximas: {prox_txt}")

        self.lbl_grande.configure(text=prox[0] if prox and prox[0] is not None else "-")

        primeiro_livre = None
        for p in postos:
            if p["ativo"] and p["atual"] is None:
                primeiro_livre = p["id"]
                break
        para = f"Posto {primeiro_livre}" if primeiro_livre is not None else "Nenhum posto livre"
        self.lbl_para.configure(text=f"Próxima deve ir: {para}")
        if primeiro_livre is not None and self.lbl_grande.cget("text") != "-":
            self.lbl_dir.configure(text=f"Dirija-se ao Posto {primeiro_livre}")
        else:
            self.lbl_dir.configure(text=("Aguardando chamada..." if self.lbl_grande.cget("text") == "-" else f"Aguardando liberação do posto {para}"))

        for i, p in enumerate(postos):
            w = self.posto_widgets[i]
            st = "Inativo"
            if p["ativo"]:
                if p["atual"] is None:
                    st = "Ativo - Livre"
                else:
                    st = f"Ativo - Ocupado (senha {p['atual']})"
            w["st"].set(st)
            if not p["ativo"]:
                w["frame"].configure(bootstyle="danger-border")
                try:
                    w["btn"].state(["disabled"])
                except Exception:
                    w["btn"].configure(state="disabled")
            else:
                w["frame"].configure(bootstyle="secondary-border")
                if p["atual"] is None:
                    try:
                        w["btn"].state(["disabled"])
                    except Exception:
                        w["btn"].configure(state="disabled")
                else:
                    try:
                        w["btn"].state(["!disabled"])
                    except Exception:
                        w["btn"].configure(state="normal")

        self.txt_atendidos.configure(state="normal")
        self.txt_atendidos.delete("1.0", tk.END)
        if len(pilha) == 0:
            self.txt_atendidos.insert(tk.END, "(nenhum atendimento ainda)\n")
        else:
            for i, s in enumerate(reversed(pilha), start=1):
                self.txt_atendidos.insert(tk.END, f"{i:03d}: {s}\n")
        self.txt_atendidos.configure(state="disabled")

        self.lbl_contadores.configure(text=f"Atendidas: {cont['atend']}    Desistências: {cont['desist']}    Emitidas N: {cont['emitN']}    Emitidas P: {cont['emitP']}")
        self.lbl_emit.configure(text=f"Emitidas N: {cont['emitN']}   P: {cont['emitP']}")
        self.lbl_extras.configure(text=f"Atendidas: {cont['atend']}   Desist.: {cont['desist']}")


# Main
def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":

    main()
