import sys
import importlib

sys.path.insert(0, r"D:\Usuários\jorda\Downloads\Quarta-20251104T232832Z-1-001\Quarta")
m = importlib.import_module("main")
print("OK: module imported")
print("emitN=>", m.emitir_senha("N"))
print("emitP=>", m.emitir_senha("P"))
print("peek=>", m.peek_next_types())
print("chamar=>", m.chamar_proxima())
print("desist=>", m.desistencia_aleatoria())
print("finalizar (posto1) =>", m.finalizar_atendimento_no_posto(1))
