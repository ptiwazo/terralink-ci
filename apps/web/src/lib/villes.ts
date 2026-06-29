// Principales villes de Côte d'Ivoire avec coordonnées approximatives (centre).
// Sert à pré-centrer la carte et pré-remplir la position quand le producteur
// choisit sa ville — il peut ensuite affiner le point sur la carte.
export interface Ville {
  nom: string;
  lat: number;
  lng: number;
}

export const VILLES_CI: Ville[] = [
  { nom: "Abidjan", lat: 5.348, lng: -4.027 },
  { nom: "Yamoussoukro", lat: 6.827, lng: -5.289 },
  { nom: "Bouaké", lat: 7.69, lng: -5.03 },
  { nom: "Daloa", lat: 6.877, lng: -6.45 },
  { nom: "San-Pédro", lat: 4.748, lng: -6.636 },
  { nom: "Korhogo", lat: 9.458, lng: -5.629 },
  { nom: "Man", lat: 7.412, lng: -7.554 },
  { nom: "Gagnoa", lat: 6.131, lng: -5.951 },
  { nom: "Divo", lat: 5.837, lng: -5.357 },
  { nom: "Abengourou", lat: 6.729, lng: -3.496 },
  { nom: "Agboville", lat: 5.928, lng: -4.213 },
  { nom: "Bondoukou", lat: 8.04, lng: -2.8 },
  { nom: "Séguéla", lat: 7.961, lng: -6.673 },
  { nom: "Odienné", lat: 9.51, lng: -7.564 },
  { nom: "Soubré", lat: 5.784, lng: -6.602 },
  { nom: "Bouna", lat: 9.267, lng: -3.0 },
  { nom: "Grand-Bassam", lat: 5.211, lng: -3.738 },
  { nom: "Toumodi", lat: 6.557, lng: -5.018 },
];

export const CENTRE_CI = { lat: 7.54, lng: -5.55 }; // centre du pays
