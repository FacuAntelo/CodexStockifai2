export interface TallerConStockResponse {
    id: number;
    nombre: string;
    direccion: string;
    lat: number | null;
    lng: number | null;
    email?: string;
    telefono?: string;
    telefono_e164?: string | null;
    stock_total: number;
    distancia_km: number | null;
}

export interface LocalizadorResponse {
    repuesto: {
        numero_pieza: string;
        descripcion: string | null;
    } | null;
    taller_origen: {
        id: number;
        nombre: string;
        lat: number | null;
        lng: number | null;
    };
    talleres: TallerConStockResponse[];
}
