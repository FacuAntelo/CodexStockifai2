from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand

from catalogo.models import Categoria, Marca, Repuesto, RepuestoTaller
from inventario.models import Deposito, StockPorDeposito
from user.models import Grupo, GrupoTaller, Taller


class Command(BaseCommand):
    help = "Carga datos iniciales para probar el localizador de repuestos"

    def handle(self, *args, **options):
        marca, _ = Marca.objects.get_or_create(nombre="Genérica")
        categoria, _ = Categoria.objects.get_or_create(nombre="Motor")

        repuestos_data = [
            {
                "numero_pieza": "A-12345",
                "descripcion": "Bomba de agua",
            },
            {
                "numero_pieza": "B-67890",
                "descripcion": "Filtro de aceite",
            },
        ]

        repuestos = {}
        for data in repuestos_data:
            repuesto, _ = Repuesto.objects.update_or_create(
                numero_pieza=data["numero_pieza"],
                defaults={
                    "descripcion": data["descripcion"],
                    "marca": marca,
                    "categoria": categoria,
                },
            )
            repuestos[data["numero_pieza"]] = repuesto

        grupo_red, _ = Grupo.objects.get_or_create(
            nombre="Red Central",
            defaults={"descripcion": "Red principal de talleres"},
        )
        grupo_bsas, _ = Grupo.objects.get_or_create(
            nombre="Área Metropolitana",
            defaults={"descripcion": "Talleres de AMBA", "grupo_padre": grupo_red},
        )
        if grupo_bsas.grupo_padre_id != grupo_red.id:
            grupo_bsas.grupo_padre = grupo_red
            grupo_bsas.save(update_fields=["grupo_padre"])
        grupo_interior, _ = Grupo.objects.get_or_create(
            nombre="Interior",
            defaults={"descripcion": "Talleres del interior", "grupo_padre": grupo_red},
        )
        if grupo_interior.grupo_padre_id != grupo_red.id:
            grupo_interior.grupo_padre = grupo_red
            grupo_interior.save(update_fields=["grupo_padre"])

        talleres_data = [
            {
                "nombre": "Taller Central",
                "direccion": "Av. Rivadavia 1234, CABA, Argentina",
                "latitud": Decimal("-34.608300"),
                "longitud": Decimal("-58.409700"),
                "telefono": "11 5555-1234",
                "email": "central@talleres.com",
                "grupo": grupo_bsas,
            },
            {
                "nombre": "Mecánica del Sur",
                "direccion": "Calle 50 742, La Plata, Buenos Aires, Argentina",
                "latitud": Decimal("-34.921500"),
                "longitud": Decimal("-57.954500"),
                "telefono": "221 444-7788",
                "email": "contacto@mecanicadelsur.com",
                "grupo": grupo_bsas,
            },
            {
                "nombre": "Taller Norte",
                "direccion": "Av. Sarmiento 3500, Rosario, Santa Fe, Argentina",
                "latitud": Decimal("-32.957500"),
                "longitud": Decimal("-60.639400"),
                "telefono": "341 555-6677",
                "email": "ventas@tallernorte.com",
                "grupo": grupo_interior,
            },
            {
                "nombre": "Garage Oeste",
                "direccion": "Av. San Martín 255, Morón, Buenos Aires, Argentina",
                "latitud": Decimal("-34.653200"),
                "longitud": Decimal("-58.621800"),
                "telefono": "11 4667-8899",
                "email": "hola@garageoeste.com",
                "grupo": grupo_bsas,
            },
        ]

        talleres = {}
        for data in talleres_data:
            taller, _ = Taller.objects.update_or_create(
                nombre=data["nombre"],
                defaults={
                    "direccion": data["direccion"],
                    "telefono": data["telefono"],
                    "email": data["email"],
                    "latitud": data["latitud"],
                    "longitud": data["longitud"],
                },
            )
            GrupoTaller.objects.get_or_create(id_grupo=data["grupo"], id_taller=taller)
            deposit, _ = Deposito.objects.get_or_create(taller=taller, nombre="Depósito Principal")
            talleres[data["nombre"]] = {"taller": taller, "deposito": deposit}

        stock_config = [
            ("Taller Central", "A-12345", 4),
            ("Mecánica del Sur", "A-12345", 2),
            ("Taller Norte", "A-12345", 5),
            ("Garage Oeste", "A-12345", 1),
            ("Taller Central", "B-67890", 3),
        ]

        for taller_nombre, numero_pieza, cantidad in stock_config:
            taller_info = talleres[taller_nombre]
            repuesto = repuestos[numero_pieza]
            rt, _ = RepuestoTaller.objects.get_or_create(
                taller=taller_info["taller"], repuesto=repuesto
            )
            spd, _ = StockPorDeposito.objects.get_or_create(
                repuesto_taller=rt,
                deposito=taller_info["deposito"],
                defaults={"cantidad": 0},
            )
            spd.cantidad = cantidad
            spd.save(update_fields=["cantidad"])

        self.stdout.write(self.style.SUCCESS("Datos de ejemplo para el localizador cargados."))
