from rest_framework import serializers
from user.models import Taller
from user.services.phone import normalize_local_phone


class TallerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taller
        fields = (
            "id",
            "nombre",
            "direccion",
            "telefono",
            "email",
            "latitud",
            "longitud",
            "fecha_creacion",
        )

    def validate_direccion(self, value: str) -> str:
        return (value or "").strip()

    def validate_telefono(self, value: str) -> str:
        return normalize_local_phone(value or "")
