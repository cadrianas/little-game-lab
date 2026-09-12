"""Build Milo's independent entrypoint; all runtime assets live in this folder."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
html=(ROOT/'index.template.html').read_text()
html=html.replace('__FIREFLY_DATA__',(ROOT/'gardens.json').read_text().strip()).replace('__GARDEN_CLASS__','wide').replace('__STORE__','milo:garden:results:v1')
a=html.index('  <nav class="garden-modes"');b=html.index('</nav>',a)+len('</nav>')
html=html[:a]+'''  <nav class="garden-library" aria-label="Choose an evening walk"><label for="gardenSelect">Your evening walks<select id="gardenSelect"></select></label><span id="collectionProgress"></span></nav>
  <div class="music-controls"><button id="musicToggle" aria-pressed="false">♫ Music off</button><label for="musicVolume">Volume<input id="musicVolume" type="range" min="0" max="100" value="30"></label><span id="musicStatus" role="status" aria-live="polite"></span></div>'''+html[b:]
html=html.replace('Firefly — A moonlit logic puzzle','Milo & the Firefly Garden').replace('<h1>Firefly</h1>','<h1>Milo &amp; the Firefly Garden</h1>').replace('<p>A moonlit logic puzzle</p>','<p>A little light. A quiet evening together.</p>')
html=html.replace('A Little Game Lab prototype · Progress stays on this device','An evening with Milo · Your progress stays on this device')
html=html.replace('</head>','<link rel="stylesheet" href="milo.css"><link rel="stylesheet" href="standalone.css">\n</head>')
html=html.replace('</body>','<script src="milo.js"></script><script src="standalone.js"></script><script src="music.js"></script><script src="celebration.js"></script>\n</body>')
(ROOT/'index.html').write_text(html)
print('Built standalone Milo garden.')
