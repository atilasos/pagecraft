"""Read the session activity, including a registered draft, without publishing it."""
import re

from .errors import SessionNotFoundError


async def session_activity_path(app, slug: str):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,100}', slug):
        raise SessionNotFoundError('Atividade não encontrada.')
    learning = app.state.learning
    registered = next((a for a in (await learning.activities()).values() if a['slug'] == slug), None)
    path = learning.content_path(registered) if registered else app.state.config.activities_dir / slug / 'index.html'
    if not path.is_file():
        raise SessionNotFoundError('Atividade não encontrada.')
    return path


GROUP_LEVEL_ADAPTER = '''<script data-pagecraft-group-level>
(() => {
  window.addEventListener('message', event => {
    if (event.source !== window.parent || event.data?.pagecraft !== 1 || event.data.type !== 'work_group_preferences') return;
    const level = event.data.payload?.level;
    if (!['support','intermediate','challenge'].includes(level)) return;
    const select = document.querySelector('select#level');
    if (select && [...select.options].some(option => option.value === level)) {
      if (select.value !== level) { select.value = level; select.dispatchEvent(new Event('change', {bubbles:true})); }
      return;
    }
    const aliases = {support:'support', apoio:'support', intermediate:'intermediate', standard:'intermediate', middle:'intermediate', intermedio:'intermediate', medio:'intermediate', challenge:'challenge', desafio:'challenge'};
    document.querySelectorAll('button[data-level], .diff-tabs button[data-show]').forEach(button => {
      const target = button.dataset.level || button.dataset.show?.split('-').at(-1);
      const selected = button.getAttribute('aria-selected') === 'true' || button.classList.contains('active');
      if (aliases[target] === level && !selected) button.click();
    });
  });
})();
</script>'''


def with_group_level_adapter(html: str) -> str:
    end = html.lower().rfind('</body>')
    return html[:end] + GROUP_LEVEL_ADAPTER + html[end:] if end >= 0 else html + GROUP_LEVEL_ADAPTER
