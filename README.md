# GodeX – sito

Sito statico di presentazione di GodeX, con le pagine che servono per l'App Store: informativa sulla privacy,
termini di servizio, supporto e contatti. In italiano (alla radice), inglese (`/en/`), francese (`/fr/`) e spagnolo
(`/es/`), come l'app. Pubblicato con GitHub Pages.

Niente framework né dipendenze: HTML e CSS, più `build.py` (solo libreria standard di Python 3) che mette ogni
pagina nel layout comune e sostituisce i segnaposto. Nessun cookie, nessuna analisi, nessuna risorsa da altri siti.

## Anteprima

```bash
python3 build.py --serve     # genera _site/ e apre http://localhost:8000
```

`build.py` si ferma se un link interno è rotto o se un segnaposto non esiste, ed elenca i segnaposto ancora da
compilare.

## Struttura

| Percorso | Contenuto |
|---|---|
| `content/<lingua>/index.html` | Home: funzioni, privacy, widget, invito a fare da tester |
| `content/<lingua>/privacy.html` | Informativa sulla privacy (bozza) |
| `content/<lingua>/terms.html` | Termini di servizio (bozza) |
| `content/<lingua>/support.html` | Supporto, domande frequenti, contatti |
| `content/strings.json` | Testi comuni per lingua: menu, piè di pagina, titoli e descrizioni, nomi dei segnaposto |
| `templates/layout.html` | Layout comune (intestazione, menu, lingue, piè di pagina) |
| `assets/css/site.css` | Stile scuro (oro #E2BC6E, rosa #E2738F), come `DesignSystem/Theme.swift` dell'app |
| `assets/img/` | Logo (`godex-lockup.svg` nell'intestazione, `logo.svg` il simbolo), favicon e icone, schermate dell'app (con dati di esempio, nessun dato reale) |
| `assets/site.webmanifest` | Manifest con le icone 192 e 512 |
| `site.json` | Titolare, email, link di TestFlight, dominio; `draft` |
| `.github/workflows/pages.yml` | Genera e pubblica su Pages a ogni push su `main`; sulle PR controlla solo la generazione |

## Segnaposto e bozza

I dati non ancora decisi stanno in `site.json` sotto `values`. Un valore `null` diventa nel sito un segnaposto
evidenziato `[…]`; compilato una volta vale per tutte e quattro le lingue. Nei frammenti si usano così:

- `{{controller}}`: il valore come testo;
- `{{mailto:support_email}}`: un link email;
- `{{link:testflight_url}}`: un link;
- `{{root}}`: il percorso relativo alla radice del sito (per le immagini).

Altri punti aperti sono scritti direttamente nei testi legali come `<mark class="todo">[…]</mark>` (valutazioni
del consulente, DPIA, marchio). Con `"draft": true` privacy e termini mostrano in cima la scritta "Bozza".
Con `"draft": false` la generazione fallisce se resta anche un solo segnaposto di `site.json`; i `mark` scritti a
mano vanno tolti dai testi.

Quando si sceglie il dominio: `domain` in `site.json` (crea il file `CNAME`) e `base_url` (per i link tra le
lingue nei motori di ricerca), poi il dominio in Settings → Pages.

## Pubblicazione

Una volta sola: Settings → Pages → Build and deployment → Source: **GitHub Actions**. Da lì ogni merge su `main`
pubblica il sito. Il workflow gira su Linux e dura pochi secondi.

## Aggiornare i contenuti

- Una funzione nuova dell'app va nella home di tutte e quattro le lingue, descritta come in `docs/` di godex-ios:
  niente funzioni che l'app non ha.
- Un cambio nei dati trattati dall'app (nuovi campi, servizi, permessi) va nell'informativa di tutte le lingue,
  aggiornando `last_updated` in `site.json`.
- I nomi di menu e pulsanti citati devono essere quelli dell'app nella stessa lingua (`Localizable.xcstrings`).
- Le schermate vengono dal simulatore con dati di esempio: mai dati reali.

## Regole

Come godex-ios: branch da `main` e pull request con merge squash; commit in inglese
`tipo(ambito): gitmoji descrizione` (ambiti `site`, `legal`, `ci`).
