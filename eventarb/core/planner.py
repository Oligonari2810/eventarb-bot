from decimal import Decimal
from typing import List

from eventarb.core.models import Event, PlannedAction, Side


def plan_actions_for_event(
    ev: Event, default_notional_usd: float
) -> List[PlannedAction]:
    actions: List[PlannedAction] = []
    kind = (ev.kind or "").upper().strip()

    if kind in ("CPI", "FOMC"):
        action_side: Side = "BUY"
        tp_pct = 3.5
        sl_pct = 1.8
        timing = "AT_T0"
    else:
        action_side: Side = "FLAT"
        tp_pct = 0.0
        sl_pct = 0.0
        timing = "AT_T0"

    for sym in ev.symbols:
        actions.append(
            PlannedAction(
                event_id=ev.id,
                symbol=sym,
                side=action_side,
                notional_usd=Decimal(str(default_notional_usd)),
                tp_pct=tp_pct,
                sl_pct=sl_pct,
                timing=timing,
            )
        )
    return actions
