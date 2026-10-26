from salitaaco.defaults.reports import PAYMENT_COLUMNS

from .report_form import ReportForm, columns_field


class PaymentsReportForm(ReportForm):
    """The payments sent in some days: by status and by plan, the money approved, and each payment."""
    columns = columns_field(PAYMENT_COLUMNS, "Mga column ng talaan ng bayad")
