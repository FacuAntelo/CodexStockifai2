import { Component, OnDestroy, OnInit } from '@angular/core';
import * as L from 'leaflet';

import { LocalizadorResponse, TallerConStockResponse } from '../../../core/models/localizador';
import { RepuestosService } from '../../../core/services/repuestos.service';

type TallerConStock = {
  id: number;
  nombre: string;
  direccion: string;
  lat: number | null;
  lng: number | null;
  cantidad: number;
  telefono?: string;
  telefonoE164?: string | null;
  email?: string;
  distanciaKm?: number | null;
};

@Component({
  selector: 'app-localizador',
  templateUrl: './localizador.component.html',
  styleUrls: ['./localizador.component.scss'],
})
export class LocalizadorComponent implements OnInit, OnDestroy {
  query = '';
  cargando = false;
  resultados: TallerConStock[] = [];
  tallerId = 1;

  private origen?: LocalizadorResponse['taller_origen'];

  private map?: L.Map;
  private markers: L.Marker[] = [];

  constructor(private repuestosService: RepuestosService) {}

  ngOnInit(): void {
    setTimeout(() => this.initMap(), 0);
  }

  buscar(): void {
    if (!this.query.trim()) return;
    this.cargando = true;
    this.repuestosService
      .buscarRepuestoEnRed(this.query.trim(), this.tallerId)
      .subscribe({
        next: (resp) => {
          this.origen = resp?.taller_origen;
          this.resultados = (resp?.talleres ?? []).map((t) => this.mapTaller(t));
          this.cargando = false;
          this.renderMarkers();
        },
        error: (err) => {
          console.error('Error al buscar localizador', err);
          this.resultados = [];
          this.cargando = false;
          this.renderMarkers();
        },
      });
  }

  limpiar(): void {
    this.query = '';
    this.resultados = [];
    this.origen = undefined;
    this.markers.forEach(m => m.remove());
    this.markers = [];
    this.map?.setView([-34.6037, -58.3816], 12);
  }

  whatsappUrl(t: TallerConStock): string {
    const numero = t.telefonoE164 ?? '';
    const texto = `Hola, consulto por disponibilidad del repuesto ${this.query.trim()}`;
    return `https://wa.me/${numero}?text=${encodeURIComponent(texto)}`;
  }

  private mapTaller(item: TallerConStockResponse): TallerConStock {
    return {
      id: item.id,
      nombre: item.nombre,
      direccion: item.direccion,
      lat: item.lat ?? null,
      lng: item.lng ?? null,
      cantidad: item.stock_total,
      telefono: item.telefono ?? undefined,
      telefonoE164: item.telefono_e164 ?? undefined,
      email: item.email ?? undefined,
      distanciaKm: item.distancia_km ?? undefined,
    };
  }

  private initMap(): void {
    this.map = L.map('mapa', {
      center: [-34.6037, -58.3816],
      zoom: 12,
    });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
    }).addTo(this.map);
  }

  private renderMarkers(): void {
    if (!this.map) return;

    this.markers.forEach(m => m.remove());
    this.markers = [];

    const bounds = L.latLngBounds([]);
    if (this.origen?.lat != null && this.origen?.lng != null) {
      const origenMarker = L.marker([this.origen.lat, this.origen.lng], {
        icon: L.icon({
          iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
          shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        }),
      }).bindPopup(`<b>${this.origen.nombre}</b><br/>Taller origen`);
      origenMarker.addTo(this.map);
      this.markers.push(origenMarker);
      bounds.extend([this.origen.lat, this.origen.lng]);
    }

    if (!this.resultados.length) {
      if (bounds.isValid()) {
        this.map.fitBounds(bounds.pad(0.2));
      }
      return;
    }

    this.resultados.forEach(t => {
      if (t.lat == null || t.lng == null) return;
      const distancia = t.distanciaKm != null ? `<br/>Distancia: ${t.distanciaKm} km` : '';
      const marker = L.marker([t.lat, t.lng]).bindPopup(
        `<b>${t.nombre}</b><br/>${t.direccion}<br/>Unidades: ${t.cantidad}${distancia}`
      );
      marker.addTo(this.map!);
      this.markers.push(marker);
      bounds.extend([t.lat, t.lng]);
    });
    this.map.fitBounds(bounds.pad(0.2));
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }
}
