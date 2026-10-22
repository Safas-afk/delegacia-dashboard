"""Motor de prazo do inquerito policial.
Base legal (pesquisada):
  - Lei de Drogas 11.343/2006, art. 51: 30 dias preso / 90 dias solto;
    o juiz pode DUPLICAR (60 / 180), ouvido o MP, a pedido do delegado.
  - CPP art. 10: 10 dias preso / 30 dias solto (crimes comuns, ex: arma, orcrim).
O prazo nao e digitado: sai de (lei, situacao, data_instauracao, prorrogado).
"""
from datetime import date, datetime, timedelta

# (lei_prazo, situacao) -> dias base
PRAZO_BASE = {
    ("drogas", "preso"): 30,
    ("drogas", "solto"): 90,
    ("cpp", "preso"): 10,
    ("cpp", "solto"): 30,
}


def _parse(d):
    if isinstance(d, (date, datetime)):
        return d if isinstance(d, date) and not isinstance(d, datetime) else d.date()
    return datetime.strptime(d, "%Y-%m-%d").date()


def calcula_prazo(lei_prazo, situacao, data_instauracao, prorrogado=False, hoje=None):
    """Retorna dict com data_limite, dias_restantes, vencido e cor do semaforo."""
    hoje = _parse(hoje) if hoje else date.today()
    base = PRAZO_BASE.get((lei_prazo, situacao))
    if base is None:
        raise ValueError(f"combinacao sem prazo definido: {lei_prazo}/{situacao}")
    dias = base * 2 if prorrogado else base          # prorrogacao duplica (art. 51 p.u.)
    inicio = _parse(data_instauracao)
    limite = inicio + timedelta(days=dias)
    restantes = (limite - hoje).days
    vencido = restantes < 0

    if vencido or restantes <= 3:
        cor = "vermelho"
    elif restantes <= 15:
        cor = "amarelo"
    else:
        cor = "verde"

    return {
        "dias_base": base,
        "dias_total": dias,
        "data_limite": limite.isoformat(),
        "dias_restantes": restantes,
        "vencido": vencido,
        "cor": cor,
    }
