from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO
import copy

class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        relazioni = EscursioneDAO.get_escursioni_punti_interesse()

        if relazioni is None:
            return

        for row in relazioni:
            id_esc = row["id_escursione"]
            id_punto = row["id_punto_interesse"]

            if id_esc in self.escursioni_map and id_punto in self.punti_interesse_map:
                escursione = self.escursioni_map[id_esc]
                punto = self.punti_interesse_map[id_punto]
                escursione.punti_interesse.add(punto)
                punto.escursioni.add(escursione)

    def genera_pacchetto(self, id_parco, max_giorni , max_budget):
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        escursioni_valide = []
        for escursione in self.escursioni_map.values():
            if escursione.id_parco == id_parco:
                escursioni_valide.append(escursione)

        self._ricorsione(
            pacchetto_parziale=[],
            durata_corrente=0,
            costo_corrente=0.0,
            valore_corrente=0,
            punti_usati=set(),
            escursioni_rimanenti=escursioni_valide,
            max_giorni=max_giorni,
            max_budget=max_budget
        )

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, pacchetto_parziale, durata_corrente, costo_corrente, valore_corrente, punti_usati, escursioni_rimanenti, max_giorni, max_budget):
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._costo = costo_corrente
            self._pacchetto_ottimo = list(pacchetto_parziale)

        for i in range(len(escursioni_rimanenti)):
            candidata = escursioni_rimanenti[i]

            if max_budget is not None and (costo_corrente + candidata.costo) > max_budget:
                continue

            if max_giorni is not None and (durata_corrente + candidata.durata_giorni) > max_giorni:
                continue

            if len(candidata.punti_interesse & punti_usati) > 0:
                continue

            pacchetto_parziale.append(candidata)
            voto_aggiuntivo = sum(p.voto_visitatori for p in candidata.punti_interesse)
            nuovi_punti_usati = punti_usati | candidata.punti_interesse
            nuove_rimanenti = escursioni_rimanenti[i + 1:]

            self._ricorsione(
                pacchetto_parziale=pacchetto_parziale,
                durata_corrente=durata_corrente + candidata.durata_giorni,
                costo_corrente=costo_corrente + candidata.costo,
                valore_corrente=valore_corrente + voto_aggiuntivo,
                punti_usati=nuovi_punti_usati,
                escursioni_rimanenti=nuove_rimanenti,
                max_giorni=max_giorni,
                max_budget=max_budget
            )

            pacchetto_parziale.pop()