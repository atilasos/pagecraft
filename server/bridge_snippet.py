"""Bridge-lite: excerto injetado deterministicamente nas atividades publicadas.

Garante que TODAS as atividades do catálogo respondem ao «chamar a atenção»
do professor, mesmo as anteriores ao template com PageCraftBridge. É JS/CSS
inline, sem rede — preserva o invariante self-contained. Se a atividade já
tem o bridge completo (template novo), o excerto não faz nada.
"""

from __future__ import annotations

MARKER = "pagecraft-bridge-lite"

SNIPPET = """
<style data-pagecraft-bridge-lite>
.pagecraft-attention {
  animation: pagecraft-attention-pulse 1.2s ease-out 4;
  outline: 4px solid oklch(0.78 0.13 85);
  outline-offset: 4px;
}
@keyframes pagecraft-attention-pulse {
  0%   { box-shadow: 0 0 0 0 oklch(0.78 0.13 85 / 0.55); }
  70%  { box-shadow: 0 0 0 18px oklch(0.78 0.13 85 / 0); }
  100% { box-shadow: 0 0 0 0 oklch(0.78 0.13 85 / 0); }
}
@media (prefers-reduced-motion: reduce) { .pagecraft-attention { animation: none; } }
</style>
<script data-pagecraft-bridge-lite>
/* pagecraft-bridge-lite: recetor de «chamar a atenção» (injetado na publicação) */
(function () {
  window.addEventListener('message', function (ev) {
    var d = ev.data;
    if (!d || d.pagecraft !== 1 || d.type !== 'highlight') return;
    var el = null;
    if (d.unitId) {
      el = document.getElementById(d.unitId) ||
           document.querySelector('[data-unit="' + d.unitId + '"]');
      if (!el) {
        /* heurística para páginas antigas: uN aponta para a N-ésima secção */
        var n = parseInt(String(d.unitId).replace(/^u/, ''), 10);
        var sections = document.querySelectorAll('main section');
        if (!sections.length) sections = document.querySelectorAll('section, .knowledge-unit, .card');
        if (n >= 1 && n <= sections.length) el = sections[n - 1];
      }
    }
    if (!el) el = document.querySelector('main') || document.body;
    try { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (e) {}
    el.classList.remove('pagecraft-attention');
    void el.offsetWidth;
    el.classList.add('pagecraft-attention');
    setTimeout(function () { el.classList.remove('pagecraft-attention'); }, 6000);
  });
})();
</script>
"""


def ensure_bridge_lite(html: str) -> str:
    """Injeta o bridge-lite antes de </body> se ainda não existir nenhum
    recetor de highlight (nem o completo do template, nem o lite)."""
    if MARKER in html or "d.type === 'highlight'" in html:
        return html
    lower = html.lower()
    idx = lower.rfind("</body>")
    if idx == -1:
        return html + SNIPPET
    return html[:idx] + SNIPPET + html[idx:]
