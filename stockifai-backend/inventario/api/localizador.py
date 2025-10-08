from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import atan2, cos, radians, sin, sqrt
from typing import Dict, Iterable, List, Optional, Sequence, Set

from django.db.models import F, Q, Sum
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalogo.models import Repuesto, RepuestoTaller
from user.models import Grupo, GrupoTaller, Taller
from user.services.phone import to_e164_digits


@dataclass(frozen=True)
class GrupoNode:
    id: int
    parent_id: Optional[int]


def _haversine_distance_km(origin: Sequence[Decimal], target: Sequence[Decimal]) -> Optional[float]:
    if None in origin or None in target:
        return None

    try:
        lat1, lon1 = map(float, origin)
        lat2, lon2 = map(float, target)
    except (TypeError, ValueError):
        return None

    radius = 6371.0

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return round(radius * c, 2)


def _build_group_index() -> Dict[int, GrupoNode]:
    return {
        g.id_grupo: GrupoNode(id=g.id_grupo, parent_id=g.grupo_padre_id)
        for g in Grupo.objects.all().only("id_grupo", "grupo_padre_id")
    }


def _collect_related_groups(initial: Iterable[int], index: Dict[int, GrupoNode]) -> Set[int]:
    result: Set[int] = set(initial)
    queue: List[int] = list(initial)

    # ascender a los ancestros
    while queue:
        gid = queue.pop(0)
        node = index.get(gid)
        if node and node.parent_id and node.parent_id not in result:
            result.add(node.parent_id)
            queue.append(node.parent_id)

    # descender a subgrupos
    added = True
    while added:
        added = False
        for node in index.values():
            if node.parent_id in result and node.id not in result:
                result.add(node.id)
                added = True

    return result


class LocalizadorRepuestoView(APIView):
    """Devuelve talleres con stock disponible para un número de repuesto."""

    def get(self, request):
        numero_pieza = (request.query_params.get("numero_pieza") or "").strip()
        taller_id = request.query_params.get("taller_id")

        if not numero_pieza:
            return Response({"detail": "numero_pieza es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        if not taller_id:
            return Response({"detail": "taller_id es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            taller_id_int = int(taller_id)
        except (TypeError, ValueError):
            return Response({"detail": "taller_id inválido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            taller_origen = Taller.objects.get(pk=taller_id_int)
        except Taller.DoesNotExist:
            return Response({"detail": "Taller de origen no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        try:
            repuesto = Repuesto.objects.get(numero_pieza=numero_pieza)
        except Repuesto.DoesNotExist:
            return Response(
                {
                    "repuesto": None,
                    "taller_origen": {"id": taller_origen.id, "nombre": taller_origen.nombre},
                    "talleres": [],
                },
                status=status.HTTP_200_OK,
            )

        grupos_index = _build_group_index()
        grupos_taller_ids = list(
            GrupoTaller.objects.filter(id_taller=taller_origen).values_list("id_grupo_id", flat=True)
        )
        if grupos_taller_ids:
            grupos_relacionados = _collect_related_groups(grupos_taller_ids, grupos_index)
            talleres_permitidos = set(
                GrupoTaller.objects.filter(id_grupo_id__in=grupos_relacionados).values_list("id_taller_id", flat=True)
            )
        else:
            talleres_permitidos = set()

        talleres_permitidos.add(taller_origen.id)

        qs = (
            RepuestoTaller.objects.filter(
                repuesto=repuesto,
                taller_id__in=talleres_permitidos,
            )
            .select_related("taller")
            .annotate(
                stock_total=Sum(
                    "stocks__cantidad",
                    filter=Q(stocks__deposito__taller_id=F("taller_id")),
                )
            )
            .filter(stock_total__gt=0)
        )

        origen_coords = (taller_origen.latitud, taller_origen.longitud)
        talleres_payload: List[Dict[str, object]] = []

        for rt in qs:
            taller = rt.taller
            lat = float(taller.latitud) if taller.latitud is not None else None
            lon = float(taller.longitud) if taller.longitud is not None else None
            distancia = _haversine_distance_km(origen_coords, (taller.latitud, taller.longitud))
            talleres_payload.append(
                {
                    "id": taller.id,
                    "nombre": taller.nombre,
                    "direccion": taller.direccion,
                    "lat": lat,
                    "lng": lon,
                    "email": taller.email,
                    "telefono": taller.telefono,
                    "telefono_e164": to_e164_digits(taller.telefono) if taller.telefono else None,
                    "stock_total": rt.stock_total or 0,
                    "distancia_km": distancia,
                }
            )

        talleres_payload.sort(key=lambda t: (t["distancia_km"] is None, t["distancia_km"] or 0.0, t["nombre"]))

        data = {
            "repuesto": {
                "numero_pieza": repuesto.numero_pieza,
                "descripcion": repuesto.descripcion,
            },
            "taller_origen": {
                "id": taller_origen.id,
                "nombre": taller_origen.nombre,
                "lat": float(taller_origen.latitud) if taller_origen.latitud is not None else None,
                "lng": float(taller_origen.longitud) if taller_origen.longitud is not None else None,
            },
            "talleres": talleres_payload,
        }
        return Response(data, status=status.HTTP_200_OK)
