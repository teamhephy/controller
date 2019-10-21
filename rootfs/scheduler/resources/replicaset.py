from scheduler.exceptions import KubeHTTPException
from scheduler.resources import Resource

from packaging.version import parse


class ReplicaSet(Resource):
    api_prefix = 'apis'
    short_name = 'rs'

    @property
    def api_version(self):
        # API locations have changed since 1.9 and deprecated in 1.16
        # https://kubernetes.io/blog/2019/07/18/api-deprecations-in-1-16/
        if self.version() >= parse("1.9.0"):
            return 'apps/v1'

        return 'extensions/v1beta1'

    def get(self, namespace, name=None, **kwargs):
        """
        Fetch a single ReplicaSet or a list
        """
        url = '/namespaces/{}/replicasets'
        args = [namespace]
        if name is not None:
            args.append(name)
            url += '/{}'
            message = 'get ReplicaSet "{}" in Namespace "{}"'
        else:
            message = 'get ReplicaSets in Namespace "{}"'

        url = self.api(url, *args)
        response = self.http_get(url, params=self.query_params(**kwargs))
        if self.unhealthy(response.status_code):
            args.reverse()  # error msg is in reverse order
            raise KubeHTTPException(response, message, *args)

        return response
