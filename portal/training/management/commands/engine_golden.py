from django.core.management.base import BaseCommand

from training import golden


class Command(BaseCommand):
    help = "Check the engines against their golden snapshots, or --update the snapshots after an intended change."

    def add_arguments(self, parser):
        parser.add_argument("--update", action="store_true", help="Rewrite training/golden/*.json from the current engines.")

    def handle(self, *args, update=False, **options):
        golden.GOLDEN_DIR.mkdir(exist_ok=True)
        for name, build in golden.BUILDERS.items():
            current = golden.dump(build())
            target = golden.path(name)
            if update:
                target.write_text(current, encoding="utf-8", newline="\n")
                self.stdout.write(f"wrote {target.name} ({len(current):,} bytes)")
            else:
                same = target.exists() and target.read_text(encoding="utf-8") == current
                self.stdout.write(f"{name}: {'matches snapshot' if same else 'DIFFERS from snapshot (or missing)'}")
