export const config = { matcher: '/((?!_vercel/).*)' };

const REALM = 'Confidential wiki';

function deny(note) {
  return new Response('401 Unauthorized - this site is private.', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="' + REALM + '", charset="UTF-8"',
      'X-Robots-Tag': 'noindex, nofollow, noarchive, nosnippet',
      'Cache-Control': 'no-store',
      'Content-Type': 'text/plain; charset=utf-8',
      'X-Auth-Note': note || 'auth-required',
    },
  });
}

const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

// base64 -> utf-8 string, without relying on atob/Buffer existing
function b64decode(input) {
  const s = String(input).replace(/[^A-Za-z0-9+/]/g, '');
  const bytes = [];
  for (let i = 0; i < s.length; i += 4) {
    const n =
      (B64.indexOf(s[i]) << 18) |
      (B64.indexOf(s[i + 1]) << 12) |
      ((i + 2 < s.length ? B64.indexOf(s[i + 2]) : 0) << 6) |
      (i + 3 < s.length ? B64.indexOf(s[i + 3]) : 0);
    bytes.push((n >> 16) & 255);
    if (i + 2 < s.length) bytes.push((n >> 8) & 255);
    if (i + 3 < s.length) bytes.push(n & 255);
  }
  let out = '';
  for (let i = 0; i < bytes.length; i++) out += String.fromCharCode(bytes[i]);
  try {
    return decodeURIComponent(escape(out));
  } catch (e) {
    return out;
  }
}

function safeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function readEnv(name) {
  try {
    const p = globalThis.process;
    if (p && p.env && typeof p.env[name] === 'string') return p.env[name];
  } catch (e) {}
  return undefined;
}

export default function middleware(request) {
  // Any unexpected failure must DENY, never pass the request through.
  try {
    const expectedPass = readEnv('SITE_PASSWORD');
    const expectedUser = readEnv('SITE_USER') || 'team';
    if (!expectedPass) return deny('server-misconfigured');

    let header = '';
    try {
      header = request.headers.get('authorization') || '';
    } catch (e) {
      return deny('no-headers');
    }

    const sp = header.indexOf(' ');
    if (sp < 0) return deny();
    const scheme = header.slice(0, sp);
    const encoded = header.slice(sp + 1).trim();
    if (scheme.toLowerCase() !== 'basic' || !encoded) return deny();

    const decoded = b64decode(encoded);
    const sep = decoded.indexOf(':');
    if (sep < 0) return deny();

    const user = decoded.slice(0, sep);
    const pass = decoded.slice(sep + 1);

    if (safeEqual(user, expectedUser) && safeEqual(pass, expectedPass)) {
      return undefined; // authenticated: let the static file be served
    }
    return deny();
  } catch (e) {
    return deny('error');
  }
}
