from salitaaco.utils.guardian_boards import board_guardian
from salitaaco.utils.plans import current_plan

PLUS_CUSTOMIZATION = "Para sa SalitAACo Plus ang pag-record ng sariling boses sa isang tile."


def can_customize_tiles(owner, owner_child):
    """
    Whether a board's tiles can be given their own recording (Customization):
    on a paid plan only. A child's board goes by their guardian's plan, a
    guardian's own by theirs. An admin's board has no plan, and neither has a
    child from before guardians, whose board works as it did. On Free the
    recordings already made are kept, but the board does not play them until
    the plan allows them again. (A tile's picture is not changed on the board.)
    """
    if owner_child is not None and owner_child.guardian_id is None:
        return True
    guardian = board_guardian(owner, owner_child)
    if guardian is None:
        return True
    return not current_plan(guardian).is_free
