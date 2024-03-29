from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404

from api.models import Key, App, AppSettings, Domain, Certificate, Service
from api.exceptions import DeisException, AlreadyExists


class Command(BaseCommand):
    """Management command for publishing Deis platform state from the database
    to k8s.
    """

    def handle(self, *args, **options):
        """Publishes Deis platform state from the database to kubernetes."""
        print("Publishing DB state to kubernetes...")

        self.save_apps()

        # certificates have to be attached to domains to create k8s secrets
        for cert in Certificate.objects.all():
            for domain in cert.domains:
                domain = get_object_or_404(Domain, domain=domain)
                cert.attach_in_kubernetes(domain)

        # deploy applications
        print("Deploying available applications")
        for application in App.objects.all():
            rel = application.release_set.filter(failed=False).latest()
            if rel.build is None:
                print('WARNING: {} has no build associated with '
                      'its latest release. Skipping deployment...'.format(application))
                continue

            try:
                application.deploy(rel)
            except AlreadyExists as error:
                print('WARNING: {} has a deployment in progress. '
                      'Skipping deployment... due to {}'.format(application, str(error)))
                continue
            except DeisException as error:
                print('ERROR: There was a problem deploying {} '
                      'due to {}'.format(application, str(error)))

            # deploy autoscaling HPAs for application
            appsettings = AppSettings.objects.filter(app=application).order_by('-created')[0]
            if appsettings.autoscale:
                try:
                    for proc_type in application.structure:
                        application.autoscale(proc_type, appsettings.autoscale[proc_type])
                except Exception as error:
                    print('ERROR: There was a problem deploying HPAs for this {} proc_type '
                          'of {} app due to error: {}'.format(proc_type, application, error))
                    continue

        print("Done Publishing DB state to kubernetes.")

    def save_apps(self):
        """Saves important Django data models to the database."""
        for app in App.objects.all():
            try:
                app.save()
                app.config_set.latest().save()
                app.tls_set.latest().sync()
            except DeisException as error:
                print('ERROR: Problem saving to model {} for {}'
                      'due to {}'.format(str(App.__name__), str(app), str(error)))
        for model in (Key, Domain, Certificate, Service):
            for obj in model.objects.all():
                try:
                    obj.save()
                except DeisException as error:
                    print('ERROR: Problem saving to model {} for {}'
                          'due to {}'.format(str(model.__name__), str(obj), str(error)))
