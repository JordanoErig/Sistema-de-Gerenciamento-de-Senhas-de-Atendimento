# sistema_tkinter_operador_ttboost_final.py
# Sistema de Gerenciamento de Senhas — Modo Operador (Tkinter + ttkbootstrap, tema flat)
# Layout: L1 (lado esquerdo = controles; painel superior = próxima senha em destaque grande; lado direito = status/fila/postos)
# Arquitetura: A (mantida a lógica original, GUI empacota a lógica)
# Requisitos: pip install ttkbootstrap
# Autor: gerado por assistente (PT-BR)
# Execute: python sistema_tkinter_operador_ttboost_final.py

import tkinter as tk
from tkinter import messagebox, filedialog
from collections import deque
import random
import json
import datetime
import sys

# ---- Dependência ttkbootstrap ----
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
except Exception as e:
    raise RuntimeError("ttkbootstrap não encontrado. Instale com: py -m pip install ttkbootstrap") from e

# -------------------------
# Configuração / Parâmetros
# -------------------------
MAX_POSTOS = 5
MIN_ATIVOS = 3

# seed opcional; usar None para aleatoriedade real
random.seed(None)

# -------------------------
# Estruturas de Dados (motor)
# -------------------------
fila_normal = deque()
fila_prior = deque()
pilha_atendidos = []  # pilha LIFO
contadores = {"emitidas_N": 0, "emitidas_P": 0, "atendidas": 0, "desistencias": 0}

postos = []
for i in range(MAX_POSTOS):
    postos.append({
        "id": i + 1,
        "active": (i < MIN_ATIVOS),  # primeiros MIN_ATIVOS ativos
        "current": None  # senha em atendimento (None se livre)
    })

altern_cycle = ["N", "N", "P"]
altern_index = 0
next_N = 1
next_P = 1

# -------------------------
# Funções do motor (mesma lógica)
# -------------------------
def emitir_senha(tipo):
    """Emite uma senha ('N' ou 'P') e adiciona na fila."""
    global next_N, next_P
    if tipo == "N":
        codigo = f"N{next_N:03d}"
        fila_normal.append(codigo)
        contadores["emitidas_N"] += 1
        next_N += 1
        return codigo
    else:
        codigo = f"P{next_P:03d}"
        fila_prior.append(codigo)
        contadores["emitidas_P"] += 1
        next_P += 1
        return codigo

def peek_next_types(n=2):
    """Retorna lista com os próximos n tipos previstos pela alternância (sem remover)."""
    temp_idx = altern_index
    temp_NQ = len(fila_normal)
    temp_PQ = len(fila_prior)
    result = []
    checks = 0
    while len(result) < n and checks < 12:
        tipo = altern_cycle[temp_idx % len(altern_cycle)]
        if tipo == "N" and temp_NQ > 0:
            result.append("N")
            temp_NQ -= 1
            temp_idx += 1
        elif tipo == "P" and temp_PQ > 0:
            result.append("P")
            temp_PQ -= 1
            temp_idx += 1
        else:
            temp_idx += 1
        checks += 1
    while len(result) < n:
        if len(fila_prior) > 0:
            result.append("P")
        elif len(fila_normal) > 0:
            result.append("N")
        else:
            result.append(None)
    return result

def chamar_proxima():
    """Chama (remove) a próxima senha seguindo 2N:1P. Retorna (senha, tipo) ou (None, None)."""
    global altern_index
    attempts = 0
    while attempts < 6:
        tipo = altern_cycle[altern_index % len(altern_cycle)]
        if tipo == "N" and len(fila_normal) > 0:
            altern_index = (altern_index + 1) % len(altern_cycle)
            return fila_normal.popleft(), "N"
        if tipo == "P" and len(fila_prior) > 0:
            altern_index = (altern_index + 1) % len(altern_cycle)
            return fila_prior.popleft(), "P"
        altern_index = (altern_index + 1) % len(altern_cycle)
        attempts += 1
    # se falhar por falta de filas, pega o que houver
    if len(fila_prior) > 0:
        return fila_prior.popleft(), "P"
    if len(fila_normal) > 0:
        return fila_normal.popleft(), "N"
    return None, None

def atribuir_a_primeiro_posto_livre(senha):
    """Atribui a senha ao primeiro posto ativo e livre; retorna id do posto ou None."""
    for posto in postos:
        if posto["active"] and posto["current"] is None:
            posto["current"] = senha
            return posto["id"]
    return None

def finalizar_atendimento_no_posto(posto_id):
    """Finaliza atendimento do posto e empilha a senha atendida."""
    idx = posto_id - 1
    posto = postos[idx]
    if posto["current"] is None:
        return False
    senha = posto["current"]
    pilha_atendidos.append(senha)
    contadores["atendidas"] += 1
    posto["current"] = None
    return True

def desistencia_aleatoria():
    """Remove aleatoriamente uma pessoa de qualquer fila (D1)."""
    total = len(fila_normal) + len(fila_prior)
    if total == 0:
        return None
    if len(fila_normal) == 0:
        codigo = fila_prior.popleft()
        contadores["desistencias"] += 1
        return codigo
    if len(fila_prior) == 0:
        codigo = fila_normal.popleft()
        contadores["desistencias"] += 1
        return codigo
    # escolher proporcionalmente
    escolha = random.random()
    prob_N = len(fila_normal) / (len(fila_normal) + len(fila_prior))
    if escolha < prob_N:
        codigo = fila_normal.popleft()
    else:
        codigo = fila_prior.popleft()
    contadores["desistencias"] += 1
    return codigo

def ativar_desativar_posto(posto_id):
    """Alterna ativo/inativo de um posto. Garante pelo menos MIN_ATIVOS ativos e não permite desativar posto ocupado."""
    idx = posto_id - 1
    if postos[idx]["current"] is not None:
        return False, "Posto ocupado — finalize antes de desativar."
    ativos = sum(1 for p in postos if p["active"])
    if postos[idx]["active"]:
        if ativos <= MIN_ATIVOS:
            return False, f"Não é permitido ter menos que {MIN_ATIVOS} postos ativos."
        postos[idx]["active"] = False
        return True, "Posto desativado."
    else:
        postos[idx]["active"] = True
        return True, "Posto ativado."

# -------------------------
# UI Avançada (ttkbootstrap - flat)
# -------------------------
class SistemaSenhaApp(tb.Window):
    def __init__(self):
        # tema flatly (flat)
        super().__init__(themename="flatly")
        self.title("Sistema de Senhas — Modo Operador")
        # definir tamanho e permitir redimensionamento
        self.geometry("1220x760")
        self.minsize(1000, 620)

        # fontes
        self.font_big = ("Segoe UI", 56, "bold")   # senha gigante (S1)
        self.font_mid = ("Segoe UI", 12)
        self.font_small = ("Segoe UI", 10)

        # construir layout L1
        self._build_layout()
        self.atualizar_interface()

    def _build_layout(self):
        # top banner (próxima senha destacada)
        top_frame = tb.Frame(self, padding=10)
        top_frame.pack(side="top", fill="x")

        banner_frame = tb.Frame(top_frame)
        banner_frame.pack(side="top", fill="x")

        # cartão grande da próxima senha (S1 - gigante)
        card_next = tb.Frame(banner_frame, bootstyle="primary", padding=16, relief="ridge")
        card_next.pack(side="left", padx=12, pady=8, ipadx=8, ipady=8, fill="x", expand=True)

        lbl_label = tb.Label(card_next, text="PRÓXIMA SENHA", font=("Segoe UI", 12, "bold"), bootstyle="inverse")
        lbl_label.pack(anchor="nw")
        self.lbl_next_big = tb.Label(card_next, text="-", font=self.font_big, bootstyle="inverse")
        self.lbl_next_big.pack(anchor="center", pady=(6,4))
        # indicação de orientação (ex: "Dirija-se ao Posto X")
        self.lbl_dirija = tb.Label(card_next, text="Aguardando chamada...", font=("Segoe UI", 11), bootstyle="inverse")
        self.lbl_dirija.pack(anchor="s", pady=(2,0))

        # painel de estatísticas rápidas (à direita do banner)
        stats_card = tb.Frame(banner_frame, bootstyle="secondary", padding=12, relief="ridge", width=380)
        stats_card.pack(side="right", padx=12, pady=8)
        stats_card.pack_propagate(False)

        self.lbl_total_fila = tb.Label(stats_card, text="Fila total: 0", font=self.font_mid)
        self.lbl_total_fila.pack(anchor="nw")
        self.lbl_prox_duas = tb.Label(stats_card, text="Próximas: - , -", font=self.font_small)
        self.lbl_prox_duas.pack(anchor="nw", pady=(8,0))
        self.lbl_para_onde = tb.Label(stats_card, text="Próxima deve ir: -", font=self.font_small)
        self.lbl_para_onde.pack(anchor="nw", pady=(6,0))
        # pequenas métricas adicionais
        self.lbl_emitidas = tb.Label(stats_card, text="Emitidas N: 0   P: 0", font=self.font_small)
        self.lbl_emitidas.pack(anchor="nw", pady=(8,0))
        self.lbl_counts_extra = tb.Label(stats_card, text="Atendidas: 0   Desist.: 0", font=self.font_small)
        self.lbl_counts_extra.pack(anchor="nw", pady=(4,0))

        # corpo principal: left controls / right status
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(side="top", fill="both", expand=True)

        # LEFT: painel de controles (largura fixa, estilo balcão)
        left_ctrl = tb.Frame(main_frame, width=360)
        left_ctrl.pack(side="left", fill="y", padx=(6,12))
        left_ctrl.pack_propagate(False)

        title_ctrl = tb.Label(left_ctrl, text="Controles do Operador", font=("Segoe UI", 14, "bold"))
        title_ctrl.pack(anchor="nw", pady=(6,10))

        # Botões principais (em destaque)
        btn_emit_n = tb.Button(left_ctrl, text="Emitir Senha NORMAL (N)", bootstyle="success-outline", width=30, command=self.ui_emitir_N)
        btn_emit_n.pack(pady=8)
        btn_emit_p = tb.Button(left_ctrl, text="Emitir Senha PRIORITÁRIA (P)", bootstyle="warning-outline", width=30, command=self.ui_emitir_P)
        btn_emit_p.pack(pady=8)

        # separador
        tb.Separator(left_ctrl).pack(fill="x", pady=10)

        btn_chamar = tb.Button(left_ctrl, text="Chamar Próxima (2N : 1P)", bootstyle="info", width=30, command=self.ui_chamar_proxima)
        btn_chamar.pack(pady=6)
        btn_desist = tb.Button(left_ctrl, text="Desistência Aleatória (D1)", bootstyle="danger-outline", width=30, command=self.ui_desistencia)
        btn_desist.pack(pady=6)

        tb.Separator(left_ctrl).pack(fill="x", pady=10)

        lbl_manage = tb.Label(left_ctrl, text="Gerenciar Postos", font=self.font_mid)
        lbl_manage.pack(anchor="nw", pady=(4,6))

        # botões para ativar/desativar postos
        self.toggle_buttons = []
        for p in postos:
            row = tb.Frame(left_ctrl)
            row.pack(fill="x", pady=4)
            lbl = tb.Label(row, text=f"Posto {p['id']}", width=8)
            lbl.pack(side="left", padx=(4,8))
            btn = tb.Button(row, text="Ativar/Desativar", bootstyle="secondary", width=18, command=lambda pid=p['id']: self.ui_toggle_posto(pid))
            btn.pack(side="left")
            self.toggle_buttons.append(btn)

        tb.Separator(left_ctrl).pack(fill="x", pady=10)

        btn_enc = tb.Button(left_ctrl, text="Encerrar Atendimento (Mostrar Pilha)", bootstyle="dark", width=30, command=self.ui_encerrar)
        btn_enc.pack(pady=6)
        btn_export = tb.Button(left_ctrl, text="Exportar log (JSON)", bootstyle="outline", width=30, command=self.ui_exportar_log)
        btn_export.pack(pady=6)

        # RIGHT: painel de status, filas e postos
        right_panel = tb.Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        # painel de filas (superior)
        filas_frame = tb.Frame(right_panel)
        filas_frame.pack(side="top", fill="x", pady=(0,10))

        filaN_card = tb.Frame(filas_frame, bootstyle="light", padding=8, relief="ridge")
        filaN_card.pack(side="left", fill="both", expand=True, padx=6)
        tb.Label(filaN_card, text="Fila - Normais (N)", font=("Segoe UI", 12, "bold")).pack(anchor="nw")
        self.list_fila_n = tk.Listbox(filaN_card, height=8, font=("Consolas", 11))
        self.list_fila_n.pack(fill="both", expand=True, pady=6)

        filaP_card = tb.Frame(filas_frame, bootstyle="light", padding=8, relief="ridge")
        filaP_card.pack(side="left", fill="both", expand=True, padx=6)
        tb.Label(filaP_card, text="Fila - Prioritárias (P)", font=("Segoe UI", 12, "bold")).pack(anchor="nw")
        self.list_fila_p = tk.Listbox(filaP_card, height=8, font=("Consolas", 11))
        self.list_fila_p.pack(fill="both", expand=True, pady=6)

        # postos (cards em grid) abaixo das filas
        postos_card = tb.Frame(right_panel, bootstyle="secondary", padding=8, relief="ridge")
        postos_card.pack(side="top", fill="both", expand=True, pady=(0,8))
        tb.Label(postos_card, text="Postos de Atendimento", font=("Segoe UI", 12, "bold")).pack(anchor="nw")

        self.postos_container = tb.Frame(postos_card)
        self.postos_container.pack(fill="both", expand=True, pady=8)

        self.posto_widgets = []
        for p in postos:
            frame = tb.Frame(self.postos_container, bootstyle="light", padding=8, relief="flat")
            lbl = tb.Label(frame, text=f"Posto {p['id']}", font=("Segoe UI", 11, "bold"))
            lbl.pack(anchor="nw")
            status_var = tk.StringVar()
            status_lbl = tb.Label(frame, textvariable=status_var)
            status_lbl.pack(anchor="nw", pady=(6,4))
            btn_fin = tb.Button(frame, text="Finalizar Atendimento", bootstyle="success", width=16, command=lambda pid=p['id']: self.ui_finalizar_posto(pid))
            btn_fin.pack(anchor="se", pady=(6,0))
            self.posto_widgets.append({"frame": frame, "status_var": status_var, "btn_fin": btn_fin})

        self._arranjar_postos_grid()

        # atendidos (rodapé)
        atendidos_card = tb.Frame(right_panel, bootstyle="light", padding=8, relief="ridge")
        atendidos_card.pack(side="bottom", fill="x")
        tb.Label(atendidos_card, text="Atendimentos (pilha - topo = último atendido)", font=("Segoe UI", 12, "bold")).pack(anchor="nw")
        self.txt_atendidos = tk.Text(atendidos_card, height=8, state="disabled", font=("Consolas", 11))
        self.txt_atendidos.pack(fill="both", expand=True, pady=6)

        # footer
        footer = tb.Frame(self, padding=6)
        footer.pack(side="bottom", fill="x")
        self.lbl_contadores = tb.Label(footer, text="Atendidas: 0    Desistências: 0    Emitidas N: 0    Emitidas P: 0", font=self.font_small)
        self.lbl_contadores.pack(side="left", padx=8)

    def _arranjar_postos_grid(self):
        # organiza os frames de postos em até 3 colunas com espaçamento
        for w in self.posto_widgets:
            w["frame"].pack_forget()
        cols = 3
        for idx, w in enumerate(self.posto_widgets):
            w["frame"].pack(side="left", padx=8, pady=8, ipadx=10, ipady=6)

    # -------------------------
    # Métodos UI que chamam o motor
    # -------------------------
    def ui_emitir_N(self):
        codigo = emitir_senha("N")
        messagebox.showinfo("Emitir Senha", f"Emitida: {codigo}")
        self.atualizar_interface()

    def ui_emitir_P(self):
        codigo = emitir_senha("P")
        messagebox.showinfo("Emitir Senha", f"Emitida: {codigo}")
        self.atualizar_interface()

    def ui_chamar_proxima(self):
        senha, tipo = chamar_proxima()
        if senha is None:
            messagebox.showinfo("Chamar", "Não há senhas para chamar.")
            return
        posto_id = atribuir_a_primeiro_posto_livre(senha)
        if posto_id is None:
            # recoloca na fila correta para não perder
            if tipo == "N":
                fila_normal.appendleft(senha)
            else:
                fila_prior.appendleft(senha)
            messagebox.showwarning("Sem posto livre", "Não há postos livres. Finalize um atendimento para liberar.")
        else:
            # atualiza mensagem grande e orientação
            messagebox.showinfo("Chamar", f"Chamado: {senha} (tipo {tipo}) → Dirija-se ao Posto {posto_id}.")
        self.atualizar_interface()

    def ui_desistencia(self):
        codigo = desistencia_aleatoria()
        if codigo is None:
            messagebox.showinfo("Desistência", "Não há pessoas na fila para desistir.")
        else:
            messagebox.showinfo("Desistência", f"Desistência: {codigo}")
        self.atualizar_interface()

    def ui_toggle_posto(self, posto_id):
        ok, msg = ativar_desativar_posto(posto_id)
        if not ok:
            messagebox.showwarning("Operação inválida", msg)
        else:
            messagebox.showinfo("Posto", msg)
        self.atualizar_interface()

    def ui_finalizar_posto(self, posto_id):
        ok = finalizar_atendimento_no_posto(posto_id)
        if not ok:
            messagebox.showwarning("Finalizar", f"Posto {posto_id} está livre.")
        else:
            messagebox.showinfo("Finalizar", f"Atendimento finalizado no Posto {posto_id}.")
        self.atualizar_interface()

    def ui_encerrar(self):
        if len(pilha_atendidos) == 0:
            messagebox.showinfo("Encerrar", "Nenhuma senha atendida ainda.")
            return
        texto = "ATENDIMENTOS (do último para o primeiro):\n\n"
        for i, s in enumerate(reversed(pilha_atendidos), start=1):
            texto += f"{i:03d}: {s}\n"
        texto += f"\nTotal atendidos: {contadores['atendidas']}\nDesistências: {contadores['desistencias']}"
        top = tb.Toplevel(self)
        top.title("Encerramento - Pilha de Atendidos")
        txt = tk.Text(top, width=60, height=30)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", texto)
        txt.configure(state="disabled")

    def ui_exportar_log(self):
        """Exporta estado atual (filas, pilha, contadores) para JSON."""
        log = {
            "timestamp": datetime.datetime.now().isoformat(),
            "fila_normal": list(fila_normal),
            "fila_prior": list(fila_prior),
            "pilha_atendidos": list(pilha_atendidos),
            "contadores": contadores,
            "postos": [{"id": p["id"], "active": p["active"], "current": p["current"]} for p in postos]
        }
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title="Salvar log como...")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(log, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exportar", f"Log salvo em:\n{path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    # -------------------------
    # Atualização visual (sincroniza UI com dados)
    # -------------------------
    def atualizar_interface(self):
        # atualizar listas de fila
        self.list_fila_n.delete(0, tk.END)
        for s in list(fila_normal):
            self.list_fila_n.insert(tk.END, s)
        self.list_fila_p.delete(0, tk.END)
        for s in list(fila_prior):
            self.list_fila_p.insert(tk.END, s)

        total_fila = len(fila_normal) + len(fila_prior)
        self.lbl_total_fila.configure(text=f"Fila total: {total_fila}")

        prox_two = peek_next_types(2)
        prox_two_text = ", ".join([t if t is not None else "-" for t in prox_two])
        self.lbl_prox_duas.configure(text=f"Próximas: {prox_two_text}")

        # label grande da próxima senha (tentativa de mostrar código real)
        next_label = "-"
        temp_idx = altern_index
        checks = 0
        temp_N = deque(fila_normal)
        temp_P = deque(fila_prior)
        while checks < 6:
            tipo = altern_cycle[temp_idx % len(altern_cycle)]
            if tipo == "N" and len(temp_N) > 0:
                next_label = temp_N[0]
                break
            if tipo == "P" and len(temp_P) > 0:
                next_label = temp_P[0]
                break
            temp_idx = (temp_idx + 1) % len(altern_cycle)
            checks += 1
        if next_label == "-" and len(fila_prior) > 0:
            next_label = fila_prior[0]
        if next_label == "-" and len(fila_normal) > 0:
            next_label = fila_normal[0]
        self.lbl_next_big.configure(text=next_label)

        # orientação para qual posto (primeiro livre ativo)
        first_free = None
        for p in postos:
            if p["active"] and p["current"] is None:
                first_free = p["id"]
                break
        para_onde = f"Posto {first_free}" if first_free is not None else "Nenhum posto livre"
        self.lbl_para_onde.configure(text=f"Próxima deve ir: {para_onde}")
        self.lbl_dirija.configure(text=f"Dirija-se ao {para_onde}" if first_free is not None and next_label != "-" else ("Aguardando chamada..." if next_label == "-" else f"Aguardando liberação do posto {para_onde}"))

        # atualizar postos
        for i, p in enumerate(postos):
            w = self.posto_widgets[i]
            status_text = "Inativo"
            if p["active"]:
                if p["current"] is None:
                    status_text = "Ativo - Livre"
                else:
                    status_text = f"Ativo - Ocupado (senha {p['current']})"
            w["status_var"].set(status_text)
            # estilos visuais
            if not p["active"]:
                w["frame"].configure(bootstyle="danger-border")
                w["btn_fin"].state(["disabled"])
            else:
                w["frame"].configure(bootstyle="secondary-border")
                if p["current"] is None:
                    w["btn_fin"].state(["disabled"])
                else:
                    w["btn_fin"].state(["!disabled"])

        # atualizar pilha de atendidos (topo primeiro)
        self.txt_atendidos.configure(state="normal")
        self.txt_atendidos.delete("1.0", tk.END)
        if len(pilha_atendidos) == 0:
            self.txt_atendidos.insert(tk.END, "(nenhum atendimento ainda)\n")
        else:
            for i, s in enumerate(reversed(pilha_atendidos), start=1):
                self.txt_atendidos.insert(tk.END, f"{i:03d}: {s}\n")
        self.txt_atendidos.configure(state="disabled")

        # contadores rodapé
        self.lbl_contadores.configure(text=f"Atendidas: {contadores['atendidas']}    Desistências: {contadores['desistencias']}    Emitidas N: {contadores['emitidas_N']}    Emitidas P: {contadores['emitidas_P']}")
        self.lbl_emitidas.configure(text=f"Emitidas N: {contadores['emitidas_N']}   P: {contadores['emitidas_P']}")
        self.lbl_counts_extra.configure(text=f"Atendidas: {contadores['atendidas']}   Desist.: {contadores['desistencias']}")

# -------------------------
# Main
# -------------------------
def main():
    app = SistemaSenhaApp()
    app.mainloop()

if __name__ == "__main__":
    main()
