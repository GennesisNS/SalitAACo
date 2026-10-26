from salitaaco.defaults.reports import USER_COLUMNS

from .report_form import ReportForm, columns_field


class UsersReportForm(ReportForm):
    """The accounts made in some days: how many of each kind, and the guardians' and admins' accounts."""
    columns = columns_field(USER_COLUMNS, "Mga column ng talaan ng account")
