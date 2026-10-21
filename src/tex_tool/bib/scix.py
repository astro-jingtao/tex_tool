"""Request layer for the SciX (and ADS) export API.

SciX speaks the same API as ADS (https://adsabs.github.io/scixhelp/api-scix/):
GET {base}/v1/export/bibtex/{bibcode} with an ``Authorization: Bearer <token>``
header returns the raw BibTeX record for that bibcode. Tokens are generated at
https://scixplorer.org/user/settings/token (SciX) or
https://ui.adsabs.harvard.edu/help/api/ (ADS). If the SciX base URL is wrong
or unreachable, retry with the ADS base (see ADS_API_BASE).
"""
import urllib.error
import urllib.request

SCIX_API_BASE = "https://api.scix.xyz"
ADS_API_BASE = "https://api.adsabs.harvard.edu"
DEFAULT_TIMEOUT = 30.0


def export_bibtex(bibcode: str, token: str, base_url: str = SCIX_API_BASE) -> str:
    """Fetch the BibTeX record for *bibcode*; returns the raw BibTeX text.

    Raises RuntimeError on HTTP errors (bad token, unknown bibcode, rate
    limit) and on an unreachable server, with the server's message included.
    """
    url = f"{base_url.rstrip('/')}/v1/export/bibtex/{bibcode}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"export/bibtex request for '{bibcode}' failed (HTTP {exc.code}): {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"cannot reach {base_url} ({exc.reason}); "
            f"retry with --api-base {ADS_API_BASE}"
        ) from exc
