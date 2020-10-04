from django.core.management.commands.migrate import Command as MigrateCommand
from django.db.migrations.exceptions import MigrationSchemaMissing
from tenant_schemas.management.commands import SyncCommon
from tenant_schemas.migration_executors import get_executor
from tenant_schemas.utils import (
    get_public_schema_name,
    get_tenant_model,
    schema_exists,
)
from django.db import DEFAULT_DB_ALIAS


class Command(SyncCommon):
    help = (
        "Updates database schema. Manages both apps with migrations and those without."
    )

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to synchronize. Defaults to the "default" database.',
        )
        parser.add_argument(
            '--run-syncdb', action='store_true', dest='run_syncdb',
            help='Creates tables for apps without migrations.',
        )
        parser.add_argument(
            '--interactive', action='store_true', dest='interactive',
            help='Run in interactive mode.',
        )
        parser.add_argument(
            '--check', action='store_true', dest='check_unapplied',
            help='Exits with a non-zero status if unapplied migrations exist.',
        )

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)
        self.PUBLIC_SCHEMA_NAME = get_public_schema_name()

        executor = get_executor(codename=self.executor)(self.args, self.options)

        if self.sync_public and not self.schema_name:
            self.schema_name = self.PUBLIC_SCHEMA_NAME

        if self.sync_public:
            executor.run_migrations(tenants=[self.schema_name])
        if self.sync_tenant:
            if self.schema_name and self.schema_name != self.PUBLIC_SCHEMA_NAME:
                if not schema_exists(self.schema_name):
                    raise MigrationSchemaMissing(
                        'Schema "{}" does not exist'.format(self.schema_name)
                    )
                else:
                    tenants = [self.schema_name]
            else:
                tenants = (
                    get_tenant_model()
                    .objects.exclude(schema_name=get_public_schema_name())
                    .values_list("schema_name", flat=True)
                )
            executor.run_migrations(tenants=tenants)
