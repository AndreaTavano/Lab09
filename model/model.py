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

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        escursioni_valide = []
        for escursione in self.escursioni_map.values():
            if escursione.id_parco == id_parco:
                escursioni_valide.append(escursione)

        self._ricorsione(start_index=0, pacchetto_parziale=[], durata_corrente=0, costo_corrente=0.0, valore_corrente=0, punti_usati=set(), escursioni_valide=escursioni_valide, max_giorni=max_giorni, max_budget=max_budget)

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index, pacchetto_parziale, durata_corrente,costo_corrente, valore_corrente, punti_usati,escursioni_valide, max_giorni, max_budget):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._costo = costo_corrente
            self._pacchetto_ottimo = list(pacchetto_parziale)

        for i in range(start_index, len(escursioni_valide)):
            candidata = escursioni_valide[i]

            if max_budget is not None and (costo_corrente + candidata.costo) > max_budget:
                continue

            if max_giorni is not None and (durata_corrente + candidata.durata_giorni) > max_giorni:
                continue

            if not candidata.punti_interesse.isdisjoint(punti_usati):
                continue

            pacchetto_parziale.append(candidata)
            voto_aggiuntivo = sum(p.voto_visitatori for p in candidata.punti_interesse)
            nuovi_punti_usati = punti_usati.union(candidata.punti_interesse)

            self._ricorsione(
                start_index=i + 1,
                pacchetto_parziale=pacchetto_parziale,
                durata_corrente=durata_corrente + candidata.durata_giorni,
                costo_corrente=costo_corrente + candidata.costo,
                valore_corrente=valore_corrente + voto_aggiuntivo,
                punti_usati=nuovi_punti_usati,
                escursioni_valide=escursioni_valide,
                max_giorni=max_giorni,
                max_budget=max_budget
            )

            pacchetto_parziale.pop()