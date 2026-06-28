import L from "leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import "leaflet/dist/leaflet.css";
import { MapContainer, Marker, Polyline, Popup, TileLayer } from "react-leaflet";

// Corrige les icônes de marqueur cassées par les bundlers (chemins d'images).
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

interface Trace {
  lat: number;
  lng: number;
  ts: string;
}

export default function MapTrace({ traces }: { traces: Trace[] }) {
  if (traces.length === 0) return null;
  const points = traces.map((t) => [t.lat, t.lng] as [number, number]);
  const center = points[points.length - 1];

  return (
    <MapContainer
      center={center}
      zoom={12}
      scrollWheelZoom={false}
      style={{ height: 240, width: "100%" }}
      className="rounded-lg"
    >
      <TileLayer
        attribution='&copy; OpenStreetMap'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {points.length > 1 && <Polyline positions={points} color="#15803d" />}
      {points.map((p, i) => (
        <Marker key={i} position={p}>
          <Popup>
            Point {i + 1}
            <br />
            {new Date(traces[i].ts).toLocaleString("fr-FR")}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
