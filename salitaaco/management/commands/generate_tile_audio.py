from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from salitaaco.backends.text_to_speech.elevenlabs import ElevenLabs, ElevenLabsError
from salitaaco.utils.tile_audio import tile_audio_directory, tile_audio_file_name, tile_words


class Command(BaseCommand):
    help = (
        "Voice the tile words in the shared ElevenLabs voice (ELEVENLABS_VOICE_ID) and save one MP3 "
        "per word in static/audio/text-to-speech/. Words that already have a file are skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--words", nargs="+", metavar="WORD",
            help='Only these tile words, e.g. --words kumain "gusto ko". Handy for trying a voice.',
        )
        parser.add_argument(
            "--overwrite", action="store_true",
            help="Make the files again even if they exist, e.g. after choosing another voice.",
        )

    def handle(self, *args, **options):
        if not settings.ELEVENLABS_API_KEY:
            raise CommandError("Set ELEVENLABS_API_KEY in .env first.")
        if not settings.ELEVENLABS_VOICE_ID:
            raise CommandError("Set ELEVENLABS_VOICE_ID in .env to the ID of the Filipino voice to use.")

        words = tile_words()
        if options["words"]:
            unknown = [word for word in options["words"] if word not in words]
            if unknown:
                raise CommandError(f"Not tile words: {', '.join(unknown)}. Spell them as the tiles do.")
            words = options["words"]

        elevenlabs = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY, model_id=settings.ELEVENLABS_MODEL)
        directory = tile_audio_directory()
        directory.mkdir(parents=True, exist_ok=True)

        made = skipped = 0
        for word in words:
            path = directory / tile_audio_file_name(word)
            if path.exists() and not options["overwrite"]:
                skipped += 1
                continue

            try:
                audio = elevenlabs.text_to_speech(settings.ELEVENLABS_VOICE_ID, word)
            except ElevenLabsError as error:
                # Files made so far are kept; running the command again carries on from here.
                raise CommandError(f"Stopped at '{word}' after {made} new files: {error}")

            path.write_bytes(audio)
            made += 1
            self.stdout.write(f"{word} -> {path.name}")

        self.stdout.write(self.style.SUCCESS(
            f"Done: {made} new, {skipped} already there. Files are in {directory}."
        ))
