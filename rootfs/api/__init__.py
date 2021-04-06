"""
The **api** Django app presents a RESTful web API for interacting with the **deis** system.
"""

import os
from urllib.parse import urlparse

__version__ = '2.3.0'

__sso_provider__ = urlparse(os.getenv('OIDC_AUTH_ENDPOINT') or 'https://keycloak.mothership.ey.io/').netloc
