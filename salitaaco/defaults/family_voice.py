# Family voices: what a family member reads aloud to have their voice cloned,
# and the version of the consent terms (templates/components/family_voice_terms.html).
# Change TERMS_VERSION whenever the wording of the terms changes, so each voice
# records which version its guardian agreed to.

TERMS_VERSION = "2026-10-11"

# About a minute of everyday Filipino, with many of the sounds of the tile words.
READING_PARAGRAPH = (
    "Magandang araw! Ako ay nasa bahay kasama ang aking pamilya. Tuwing umaga, kumakain kami ng almusal "
    "sa kusina: kanin, itlog, isda, at mainit na tsokolate. Pagkatapos, naglalaro ang mga bata sa labas "
    "habang nagbabasa si Lolo sa sala. Kapag gutom ka, sabihin mo lang, \"Gusto kong kumain.\" Kapag uhaw "
    "ka, sabihin mo, \"Gusto kong uminom.\" Kapag may masakit, ituro mo at sabihin, \"Masakit dito.\" "
    "Huwag kang mahihiya, anak. Nandito lang kami para tumulong. Mahal na mahal ka namin. Salamat po sa "
    "lahat, at magkita tayo mamaya."
)

# How many tile words one request generates; the page keeps asking until all are done.
WORDS_PER_REQUEST = 5

# The tile word played when someone presses ▶ to hear what a voice sounds like.
# It must be spelled exactly as a tile in vocabulary.py, or there is nothing to play.
PREVIEW_WORD = "salamat"
