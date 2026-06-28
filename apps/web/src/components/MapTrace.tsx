import L from "leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import "leaflet/dist/leaflet.css";
import { useEffect } from "react";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";

// Corrige les icônes de marqueur cassées par les bundlers (chemins d'images).
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

// Marqueur de destination (point de livraison).
const destinationIcon = L.divIcon({
  className: "",
  html: '<div style="font-size:22px;line-height:22px">🏁</div>',
  iconSize: [22, 22],
  iconAnchor: [11, 22],
});

interface Trace {
  lat: number;
  lng: number;
  ts: string;
}

interface Props {
  traces: Trace[];
  destination?: { lat: number; lng: number } | null;
}

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 0) return;
    if (points.length === 1) map.setView(points[0], 13);
    else map.fitBounds(points, { padding: [30, 30] });
  }, [points, map]);
  return null;
}

export default function MapTrace({ traces, destination }: Props) {
  if (traces.length === 0 && !destination) return null;
  const points = traces.map((t) => [t.lat, t.lng] as [number, number]);
  const dest = destination ? ([destination.lat, destination.lng] as [number, number]) : null;
  const tous = dest ? [...points, dest] : points;
  const center = tous[tous.length - 1] ?? [0, 0];

  return (
    <MapContainer
      center={center}
      zoom={12}
      scrollWheelZoom={false}
      style={{ height: 260, width: "100%" }}
      className="rounded-lg"
    >
      <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {points.length > 1 && <Polyline positions={points} color="#15803d" />}
      {/* Lien entre la dernière position et la destination */}
      {points.length > 0 && dest && (
        <Polyline positions={[points[points.length - 1], dest]} color="#9ca3af" dashArray="6" />
      )}
      {points.map((p, i) => (
        <Marker key={i} position={p}>
          <Popup>
            Point {i + 1}
            <br />
            {new Date(traces[i].ts).toLocaleString("fr-FR")}
          </Popup>
        </Marker>
      ))}
      {dest && (
        <Marker position={dest} icon={destinationIcon}>
          <Popup>Destination (point de livraison)</Popup>
        </Marker>
      )}
      <FitBounds points={tous} />
    </MapContainer>
  );
}
