from scheduler.exceptions import KubeHTTPException
from scheduler.resources import Resource


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
