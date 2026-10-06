from functools import wraps


def active_nav(*nav_ids):
    """
    Declare which sidebar item a view highlights.

    Several ids may be given for a page shared by more than one role; the first
    one the user can see is the one highlighted.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            request.active_nav_ids = nav_ids
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
