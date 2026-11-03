import csv
import io
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.api.dependencies import get_current_user, get_dbf_manager
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/reports", tags=["Relatórios"])


def _build_report_rows(
    mgr: DBFManager,
    report_type: str,
    situacao: Optional[str] = None,
    responsavel: Optional[str] = None,
) -> List[Dict[str, Any]]:
    rtype = report_type.lower()
    table_map = {
        "sales": "PEDIDOS",
        "revenue": "PEDIDOS",
        "orders": "PEDIDOS",
        "clients": "CLIENTES",
        "products": "PRODUTOS",
        "quotations": "ORCAMENT",
        "opportunities": "OPORTUN",
        "conversion": "OPORTUN",
        "activities": "ATIVIDAD",
        "performance": "OPORTUN",
    }
    tname = table_map.get(rtype, "PEDIDOS")
    rows = mgr.find_all(tname, sort_by="DT_CRIA", descending=True)
    out: List[Dict[str, Any]] = []
    for r in rows:
        if situacao and r.get("SITUACAO") != situacao.upper():
            continue
        if responsavel and r.get("ID_RESP") != responsavel:
            continue
        out.append(r)
    return out


@router.get("/{report_type}")
def get_report(
    report_type: str,
    situacao: Optional[str] = None,
    responsavel: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "RELATORIOS", "view")
    rows = _build_report_rows(mgr, report_type, situacao=situacao, responsavel=responsavel)
    summary = DashboardService(mgr).get_summary()
    return {
        "report_type": report_type,
        "count": len(rows),
        "rows": rows,
        "summary_kpis": summary["kpis"],
    }


@router.get("/{report_type}/csv")
def export_report_csv(
    report_type: str,
    situacao: Optional[str] = None,
    responsavel: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> StreamingResponse:
    check_permission(mgr, user, "RELATORIOS", "export")
    rows = _build_report_rows(mgr, report_type, situacao=situacao, responsavel=responsavel)
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    if rows:
        headers = list(rows[0].keys())
        writer.writerow(headers)
        for r in rows:
            writer.writerow([r.get(h, "") for h in headers])
    else:
        writer.writerow(["STATUS"])
        writer.writerow(["SEM_REGISTROS"])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=relatorio_{report_type}.csv"},
    )

