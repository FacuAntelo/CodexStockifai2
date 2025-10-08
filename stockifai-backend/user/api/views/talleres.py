from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from inventario.models import Movimiento
from user.api.serializers.taller_serializer import TallerSerializer
from user.models import Taller
from user.services.geocoding import geocode_address
from user.services.phone import normalize_local_phone


class TallerViewSet(viewsets.ModelViewSet):
    queryset = Taller.objects.all()
    serializer_class = TallerSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        instance = serializer.save()
        self._enrich_taller(instance, serializer.validated_data)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._enrich_taller(instance, serializer.validated_data)

    def _enrich_taller(self, taller: Taller, data: dict) -> None:
        update_fields: set[str] = set()

        if "direccion" in data:
            direccion = (data.get("direccion") or "").strip()
            if taller.direccion != direccion:
                taller.direccion = direccion
                update_fields.add("direccion")

            if direccion:
                coords = geocode_address(direccion)
                if coords:
                    lat, lon = coords
                    lat_dec = Decimal(str(lat))
                    lon_dec = Decimal(str(lon))
                    if taller.latitud != lat_dec:
                        taller.latitud = lat_dec
                        update_fields.add("latitud")
                    if taller.longitud != lon_dec:
                        taller.longitud = lon_dec
                        update_fields.add("longitud")

        if "telefono" in data:
            telefono = normalize_local_phone(data.get("telefono") or "")
            if taller.telefono != telefono:
                taller.telefono = telefono
                update_fields.add("telefono")

        if update_fields:
            taller.save(update_fields=list(update_fields))


class TallerView(APIView):
    """
    GET /talleres/<taller_id>/info
    Respuesta:
    {
      "taller": { ...datos básicos... },
      "stock_inicial_cargado": true|false
    }
    """

    def get(self, request, taller_id: int):
        try:
            taller = Taller.objects.get(pk=taller_id)
        except Taller.DoesNotExist:
            return Response(
                {"detail": "Taller no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        stock_inicial_cargado = Movimiento.objects.filter(
            stock_por_deposito__repuesto_taller__taller_id=taller.id
        ).exists()

        data = {
            "taller": TallerSerializer(taller).data,
            "stock_inicial_cargado": stock_inicial_cargado,
        }
        return Response(data, status=status.HTTP_200_OK)
