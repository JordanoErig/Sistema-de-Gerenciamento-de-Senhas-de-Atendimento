import random

class No:
    def __init__(self, valor):
        self.valor = valor
        self.proximo = None
        self.anterior = None

class Fila:
    def __init__(self):
        self.inicio = None
        self.fim = None
        self.tamanho = 0

    # enfileirar no fim
    def enfileirar(self, dado):
        novo = No(dado)

        if not self.fim:
            self.inicio = self.fim = novo
        else:
            self.fim.proximo = novo
            novo.anterior = self.fim
            self.fim = novo

        self.tamanho += 1

    def append(self, dado):
        self.enfileirar(dado)

    # inserir no início
    def appendleft(self, dado):
        novo = No(dado)

        if not self.inicio:
            self.inicio = self.fim = novo
        else:
            novo.proximo = self.inicio
            self.inicio.anterior = novo
            self.inicio = novo

        self.tamanho += 1

    # desenfileirar da frente
    def desenfileirar(self):
        if not self.inicio:
            return None
        val = self.inicio.valor
        self.inicio = self.inicio.proximo

        if not self.inicio:
            self.fim = None
        else:
            self.inicio.anterior = None

        self.tamanho -= 1
        return val

    def popleft(self):
        return self.desenfileirar()

    def vazia(self):
        return self.tamanho == 0

    def __len__(self):
        return self.tamanho

    # itera sobre valores
    def __iter__(self):
        cur = self.inicio
        while cur:
            yield cur.valor
            cur = cur.proximo

    def to_list(self):
        return [x for x in self]


class Pilha:
    def __init__(self):
        self.topo = None
        self.tamanho = 0

    def empilhar(self, valor):
        novo = No(valor)
        novo.proximo = self.topo
        
        if self.topo is not None:
            # mantem campo anterior
            self.topo.anterior = novo
        self.topo = novo
        self.tamanho += 1

    def desempilhar(self):
        if not self.topo:
            return None
        
        no = self.topo
        self.topo = no.proximo

        if self.topo is not None:
            self.topo.anterior = None

        self.tamanho -= 1
        return no.valor

    def vazia(self):
        return self.tamanho == 0

    def listar_topo_para_baixo(self):
        arr = []
        cur = self.topo

        while cur:
            arr.append(cur.valor)
            cur = cur.proximo
        return arr


class Posto:
    def __init__(self, id, ativo=True):
        self.id = id
        self.ativo = ativo
        self.atual = None

    def __repr__(self):
        return f"<Posto {self.id} ativo={self.ativo} atual={self.atual}>"

# sistema que encapsula toda a lógica
class SistemaAtendimento:
    def __init__(self, postos_max=5, min_ativos=3):
        self.filaN = Fila()
        self.filaP = Fila()
        self.pilha = Pilha()
        
        # contadores e estado
        self.cont = {"emitN": 0, "emitP": 0, "atend": 0, "desist": 0}

        # postos
        self.postos = [Posto(i+1, ativo=(i < min_ativos)) for i in range(postos_max)]
        self.POSTOS_MAX = postos_max
        self.MIN_AT = min_ativos

        # ciclo 2N:1P
        self.ciclo = ["N", "N", "P"]
        self.idx_ciclo = 0

        # próximos números
        self.proxN = 1
        self.proxP = 1

    # gerar senha
    def emitir(self, tipo):
        if tipo == "N":
            cod = f"N{self.proxN:03d}"
            self.filaN.append(cod); self.cont["emitN"] += 1; self.proxN += 1
            return cod
        cod = f"P{self.proxP:03d}"
        self.filaP.append(cod); self.cont["emitP"] += 1; self.proxP += 1
        return cod

    # proximos tipos de senha
    def proximos_tipos(self, n = 2):
        temp = []; 
        temp_idx = self.idx_ciclo
        nN = len(self.filaN); 
        nP = len(self.filaP); 
        checks = 0

        while len(temp) < n and checks < 12:
            t = self.ciclo[temp_idx % len(self.ciclo)]
            
            if t == "N" and nN > 0:
                temp.append("N"); nN -= 1; temp_idx += 1
            elif t == "P" and nP > 0:
                temp.append("P"); nP -= 1; temp_idx += 1
            else:
                temp_idx += 1
            checks += 1

        while len(temp) < n:
            if len(self.filaP) > 0:
                temp.append("P")
            elif len(self.filaN) > 0:
                temp.append("N")
            else:
                temp.append(None)
        return temp

    # proximas senhas a serem chamadas
    def proximas_senhas(self, n=2):
        tempN = list(self.filaN.to_list()); 
        tempP = list(self.filaP.to_list())
        temp_idx = self.idx_ciclo; 
        res = []; 
        checks = 0

        while len(res) < n and checks < 12:
            t = self.ciclo[temp_idx % len(self.ciclo)]
            if t == "N" and tempN:
                res.append(tempN.pop(0)); temp_idx += 1
            elif t == "P" and tempP:
                res.append(tempP.pop(0)); temp_idx += 1
            else:
                temp_idx += 1
            checks += 1
            
        while len(res) < n:
            if len(tempP) > 0:
                res.append(tempP.pop(0))
            elif len(tempN) > 0:
                res.append(tempN.pop(0))
            else:
                res.append(None)
        return res

    # chamar seguindo 2N:1P
    def chamar(self):
        tent = 0
        while tent < 6:
            t = self.ciclo[self.idx_ciclo % len(self.ciclo)]
            if t == "N" and len(self.filaN) > 0:
                self.idx_ciclo = (self.idx_ciclo + 1) % len(self.ciclo)
                return self.filaN.popleft(), "N"
            if t == "P" and len(self.filaP) > 0:
                self.idx_ciclo = (self.idx_ciclo + 1) % len(self.ciclo)
                return self.filaP.popleft(), "P"
            self.idx_ciclo = (self.idx_ciclo + 1) % len(self.ciclo)
            tent += 1
        if len(self.filaP) > 0:
            return self.filaP.popleft(), "P"
        if len(self.filaN) > 0:
            return self.filaN.popleft(), "N"
        return None, None

    def chamar_proxima_senha(self):
        return self.chamar()

    # atribuir posto livre
    def atribuir_posto_livre(self, senha):
        for p in self.postos:
            if p.ativo and p.atual is None:
                p.atual = senha
                return p.id
        return None

    def finalizar_posto(self, posto_id):
        idx = posto_id - 1
        if idx < 0 or idx >= len(self.postos): return False
        p = self.postos[idx]
        if p.atual is None: return False
        s = p.atual
        self.pilha.empilhar(s)
        self.cont["atend"] += 1
        p.atual = None
        return True
    
    def desistir_aleatorio(self):
        total = len(self.filaN) + len(self.filaP)

        if total == 0:
            return None
        
        if len(self.filaN) == 0:
            c = self.filaP.popleft()
            self.cont["desist"] += 1
            return c
        
        if len(self.filaP) == 0:
            c = self.filaN.popleft()
            self.cont["desist"] += 1
            return c
        
        r = random.random()
        probN = len(self.filaN) / (len(self.filaN) + len(self.filaP))

        if r < probN:
            c = self.filaN.popleft()
        else:
            c = self.filaP.popleft()
            
        self.cont["desist"] += 1
        return c

    # alternar posto ativo/inativo
    def alternar_posto(self, posto_id):
        idx = posto_id - 1

        if idx < 0 or idx >= len(self.postos):
            return False, "Posto inválido."
        
        if self.postos[idx].atual is not None:
            return False, "Posto ocupado — finalize antes de desativar."
        
        ativos = sum(1 for x in self.postos if x.ativo)

        if self.postos[idx].ativo:
            if ativos <= self.MIN_AT:
                return False, f"Não é permitido ter menos que {self.MIN_AT} postos ativos."
            
            self.postos[idx].ativo = False

            return True, "Posto desativado."
        
        self.postos[idx].ativo = True
        return True, "Posto ativado."
    

    # helpers para GUI
    def listar_filaN(self):
        return [x for x in self.filaN.to_list()]

    def listar_filaP(self):
        return [x for x in self.filaP.to_list()]

    def listar_pilha(self):
        return self.pilha.listar_topo_para_baixo()

    def total_fila(self):
        return len(self.filaN) + len(self.filaP)

    def contadores(self):
        return dict(self.cont)
