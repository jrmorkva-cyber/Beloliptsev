/* global opentype */
/* Runtime font cleaner: fetch each TTF, re-serialise through opentype.js
 * (which strips problematic tables Chrome's sanitiser rejects), then
 * register it as a FontFace under the brand family name. Call once on
 * page load BEFORE the design system is rendered. */
(function () {
  const families = [
    { file: 'fonts/Anticva-Regular.otf',            family: 'Anticva',     weight: 400, style: 'normal' },
    { file: 'fonts/Panama-Regular.ttf',             family: 'Panama',      weight: 400, style: 'normal' },
    { file: 'fonts/Panama-Italic.ttf',              family: 'Panama',      weight: 400, style: 'italic' },
    { file: 'fonts/Panama-Bold.ttf',                family: 'Panama',      weight: 700, style: 'normal' },
    { file: 'fonts/Panama-Iranic.ttf',              family: 'Panama',      weight: 400, style: 'oblique' },
    { file: 'fonts/PanamaMonospace-Regular.ttf',    family: 'Panama Mono', weight: 400, style: 'normal' },
    { file: 'fonts/PanamaMonospace-Italic.ttf',     family: 'Panama Mono', weight: 400, style: 'italic' },
    { file: 'fonts/PanamaMonospace-Bold.ttf',       family: 'Panama Mono', weight: 700, style: 'normal' },
    { file: 'fonts/PanamaMonospace-Iranic.ttf',     family: 'Panama Mono', weight: 400, style: 'oblique' },
  ];

  async function loadOne({ file, family, weight, style }, basePath) {
    const url = basePath + file;
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error('http ' + r.status);
      const buf = await r.arrayBuffer();
      let cleaned;
      try {
        const parsed = opentype.parse(buf);
        cleaned = parsed.toArrayBuffer();
      } catch (e) {
        cleaned = buf;
      }
      const ff = new FontFace(family, cleaned, { weight: String(weight), style });
      await ff.load();
      document.fonts.add(ff);
    } catch (e) {
      console.warn('font failed', family, weight, style, e.message);
    }
  }

  window.__loadBrandFonts = async function (basePath = '') {
    if (!window.opentype) {
      console.warn('opentype.js not loaded — falling back to native @font-face');
      return;
    }
    await Promise.all(families.map(f => loadOne(f, basePath)));
  };
})();
