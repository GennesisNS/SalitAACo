from salitaaco.defaults.reports import MESSAGE_COLUMNS, RATING_COLUMNS

from .report_form import ReportForm, columns_field


class FeedbackReportForm(ReportForm):
    """The ratings given and the support messages sent in some days, each with a table of its own."""
    rating_columns = columns_field(RATING_COLUMNS, "Mga column ng talaan ng rating")
    message_columns = columns_field(MESSAGE_COLUMNS, "Mga column ng talaan ng mensahe")
