from salitaaco.models.word_usage import WordUsage

DEFAULT_FREQUENT_LIMIT = 40
MAX_FREQUENT_LIMIT = 200


def frequent_words(user, limit=DEFAULT_FREQUENT_LIMIT):
    """The user's most-used words, highest count first, most recently used first on a tie."""
    limit = max(1, min(limit, MAX_FREQUENT_LIMIT))
    usages = WordUsage.objects.filter(user=user).order_by('-use_count', '-last_used')[:limit]
    return [{"word": usage.word, "use_count": usage.use_count} for usage in usages]
