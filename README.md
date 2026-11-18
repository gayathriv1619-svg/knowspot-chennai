# KnowSpot Chennai

A hyperlocal Chennai guide: events, new openings, cafés and shops with real photos, peaceful night walks, a Google-News-style feed, a reel-to-place finder and an AI concierge.

- `app/` – the static web app (`app/index.html` plus `img/` and `snd/`). Open `app/index.html` through any static server, or deploy the folder to Netlify / GitHub Pages.
- `pipeline/` – the scripts and data snapshots used to build the app (events, OpenStreetMap places, routes, news feeds, walks).
- `prototype-v3/` – the earlier "verified brief" prototype (single self-contained file).

## Real café photos, ratings and reviews
These load live from the Google Places API (New). Add your own key in the app (☰ › "Real shop photos"). Never commit a key to this repo.

## Data and credits
Events: Meetup, allevents.in, District. Places, roads and coast: © OpenStreetMap contributors (ODbL). News: The Hindu, The New Indian Express, DT Next (links go to the publisher). Walk and landmark photos: Wikimedia Commons (credited in the app). Traffic speeds: TomTom Traffic Index 2025. Some shop photos were found on the web and link to their source; review rights before making the site public.
