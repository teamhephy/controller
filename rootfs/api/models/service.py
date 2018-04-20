from django.db import models
from django.conf import settings

from api.models import AuditedModel

class Service(AuditedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    app = models.ForeignKey('App', on_delete=models.CASCADE)
    procfile_type = models.TextField(blank=False, null=False, unique=False)
    path_pattern = models.TextField(blank=False, null=False, unique=False)

    class Meta:
        get_latest_by = 'created'
        unique_together = (('app', 'procfile_type'))
        ordering = ['-created']

    def __str__(self):
        return "{}-{}".format(self.app.id, str(self.procfile_type))

    def as_dict(self):
        return {
            "procfile_type": self.procfile_type,
            "path_pattern": self.path_pattern
        }

    def create(self, *args, **kwargs):  # noqa
        # create required minimum service in k8s for the application
        namespace = self.app.id
        svc_name = "{}-{}".format(self.id, self.procfile_type)
        self.log('creating Service: {}'.format(svc_name), level=logging.DEBUG)
        try:
            try:
                self._scheduler.svc.get(namespace, svc_name)
            except KubeException:
                self._scheduler.svc.create(namespace, svc_name)
        except KubeException as e:
            raise ServiceUnavailable('Kubernetes service could not be created') from e
        # config service
        annotations = self._gather_settings()
        routable = annotations.pop('routable')
        self._update_service(namespace, self.procfile_type, routable, annotations)

    def save(self, *args, **kwargs):
        service = super(Service, self).save(*args, **kwargs)
        self.create()
        return service

    def delete(self, *args, **kwargs):
        namespace = self.app.id
        svc_name = "{}-{}".format(self.id, self.procfile_type)
        self.log('deleting Service: {}'.format(svc_name), level=logging.DEBUG)
        try:
            self._scheduler.svc.delete(namespace, svc_name)
        except KubeException:
            # swallow exception
            # raise ServiceUnavailable('Kubernetes service could not be deleted') from e
            self.log('Kubernetes service cannot be deleted: {}'.format(svc_name), level=logging.ERROR)

        # Delete from DB
        return super(Service, self).delete(*args, **kwargs)

    def _gather_settings(self):
        app_settings = self.app.appsettings_set.latest()
        return {
            'domains': "{}-{}".format(self.app.id, self.procfile_type),
            'maintenance': app_settings.maintenance,
            'routable': app_settings.routable,
            'proxyDomain': self.app.id,
            'proxyLocations': self.path_pattern
        }

    def _update_service(self, namespace, app_type, routable, annotations):  # noqa
        """Update application service with all the various required information"""
        svc_name = "{}-{}".format(namespace, app_type)
        service = self._fetch_service_config(namespace, svc_name)
        old_service = service.copy()  # in case anything fails for rollback

        try:
            # Update service information
            for key, value in annotations.items():
                if value is not None:
                    service['metadata']['annotations']['router.deis.io/%s' % key] = str(value)
                else:
                    service['metadata']['annotations'].pop('router.deis.io/%s' % key, None)
            if routable:
                service['metadata']['labels']['router.deis.io/routable'] = 'true'
            else:
                # delete the annotation
                service['metadata']['labels'].pop('router.deis.io/routable', None)

            # Set app type selector
            service['spec']['selector']['type'] = app_type

            self._scheduler.svc.update(namespace, svc_name, data=service)
        except Exception as e:
            # Fix service to old port and app type
            self._scheduler.svc.update(namespace, svc_name, data=old_service)
            raise ServiceUnavailable(str(e)) from e
