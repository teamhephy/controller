from scheduler.exceptions import KubeHTTPException
from scheduler.resources import Resource
from datetime import datetime, timedelta
import json

class Consolerole(Resource):
    short_name = 'consolerole'

    def _service_account_manifest(self, namespace):
        manifest = {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": "deis-console-{}".format(namespace),
                "namespace": "{}".format(namespace)
            },
            "secrets:": [{
                "name": "deis-console-{}".format(namespace)
            }],
        }

        return manifest

    def _role_binding_manifest(self, namespace):
        manifest = {
            "kind": "RoleBinding",
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "metadata": {
                "name": "deis-console-{}".format(namespace),
                "labels": {
                    'heritage': 'deis'
                }
            },
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "ClusterRole",
                "name": "deis:deis-console"
            },
            "subjects": [{
                "kind": "ServiceAccount",
                "name": "deis-console-{}".format(namespace),
                "namespace": "{}".format(namespace),
            }]

        }

        return manifest

    def _create_service_account(self, namespace):
        url = self.api("/namespaces/{}/serviceaccounts", namespace)
        manifest = self._service_account_manifest(namespace)
        response = self.http_post(url, json=manifest)
        if response.status_code == 409:
            return response
        if not response.status_code == 201:
            raise KubeHTTPException(
                response, "create ServiceAccount {}".format(namespace)
            )

        return response

    def _delete_secret(self, namespace, secret_name):
        url = self.api("/namespaces/{}/secrets/{}", namespace, secret_name)
        response = self.http_delete(url)
        if not response.status_code == 200:
            raise KubeHTTPException(
                response, "Delete secret: {} in namespace {}".format(secret_name, namespace)
            )
            
    def _get_namespace_secrets(self, namespace):
        url = self.api("/namespaces/{}/secrets", namespace)
        response = self.http_get(url)
        if not response.status_code == 200:
            raise KubeHTTPException(
                response, "Get secrets in namespace {}".format(namespace)
            )
        return response.content
        
    def _get_service_account_secret(self, secrets_json):
        secrets = json.loads(secrets_json)
        secret = [
            x for x in secrets['items']
            if x['metadata']['name'].startswith("deis-console-")
            ]
        if secret:
            return secret[0]
        return None

    def refresh_service_account_token(self, namespace):
        secrets_json = self._get_namespace_secrets(namespace)
        secret = self._get_service_account_secret(secrets_json)
        self._delete_secret(namespace, secret['metadata']['name'])
            
    def _service_account_token_exists(self, namespace):
        secrets_json = self._get_namespace_secrets(namespace)
        secret = self._get_service_account_secret(secrets_json)
        return secret != None

    def create(self, namespace):
        self._create_service_account(namespace)
        url = (
            "/apis/rbac.authorization.k8s.io/v1"
            "/namespaces/{}/rolebindings"
            ).format(namespace)
        manifest = self._role_binding_manifest(namespace)
        response = self.http_post(url, json=manifest)
        if response.status_code == 409:
            return response
        if not response.status_code == 201:
            raise KubeHTTPException(
                response, "create RoleBinding for {}".format(namespace)
            )

        return response
