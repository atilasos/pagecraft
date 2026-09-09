"""Identidade remota do professor, validada por assinatura e aplicação Access."""
from urllib.parse import urlsplit

import jwt
from starlette.concurrency import run_in_threadpool


class CloudflareAccess:
    def __init__(self, config):
        self.origin = config.teacher_origin.rstrip('/')
        self.audience = config.access_aud
        self.email = config.access_email.casefold()
        self.issuer = 'https://' + config.access_team_domain
        settings = (self.origin, self.audience, self.email, config.access_team_domain)
        self.enabled = any(settings)
        if not self.enabled:
            return
        origin = urlsplit(self.origin)
        if (not all(settings) or origin.scheme != 'https' or not origin.hostname
            or origin.path or origin.query or origin.fragment or origin.username
            or '/' in config.access_team_domain
            or not config.access_team_domain.endswith('.cloudflareaccess.com')):
            raise ValueError('Configuração Cloudflare Access incompleta ou inválida.')
        self.hostname = origin.hostname
        self.keys = jwt.PyJWKClient(self.issuer + '/cdn-cgi/access/certs', timeout=5, lifespan=300)

    def _verify(self, token):
        try:
            key = self.keys.get_signing_key_from_jwt(token)
            claims = jwt.decode(token, key.key, algorithms=['RS256'],
                issuer=self.issuer, audience=self.audience,
                options={'require': ['exp', 'iat', 'iss', 'aud', 'sub', 'email']})
            return (isinstance(claims['email'], str)
                    and claims['email'].casefold() == self.email
                    and bool(claims['sub']))
        except (jwt.PyJWTError, OSError, ValueError):
            return False

    async def authenticates(self, request):
        token = request.headers.get('cf-access-jwt-assertion', '')
        if not self.enabled or request.url.hostname != self.hostname or not token or len(token) > 16384:
            return False
        # JWKS retrieval never blocks FastAPI's event loop. Cached keys still
        # require signature, expiry, issuer, audience and email on every request.
        return await run_in_threadpool(self._verify, token)
