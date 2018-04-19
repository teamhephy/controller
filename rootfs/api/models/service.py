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

    def save(self, *args, **kwargs):
        # app = str(self.app)
        # domain = str(self.domain)

        # # get config for the service
        # config = self._load_service_config(app, 'router')

        # # See if domains are available
        # if 'domains' not in config:
        #     config['domains'] = ''

        # # convert from string to list to work with and filter out empty strings
        # domains = [_f for _f in config['domains'].split(',') if _f]
        # if domain not in domains:
        #     domains.append(domain)
        # config['domains'] = ','.join(domains)

        # self._save_service_config(app, 'router', config)

        # Save to DB
        return super(Service, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # app = str(self.app)
        # domain = str(self.domain)

        # # Deatch cert, updates k8s
        # if self.certificate:
        #     self.certificate.detach(domain=domain)

        # # get config for the service
        # config = self._load_service_config(app, 'router')

        # # See if domains are available
        # if 'domains' not in config:
        #     config['domains'] = ''

        # # convert from string to list to work with and filter out empty strings
        # domains = [_f for _f in config['domains'].split(',') if _f]
        # if domain in domains:
        #     domains.remove(domain)
        # config['domains'] = ','.join(domains)

        # self._save_service_config(app, 'router', config)

        # Delete from DB
        return super(Service, self).delete(*args, **kwargs)
