# The reports an admin makes on Mga Ulat (routes/generated_reports/): what
# each is about, the file it is made as, and the columns of its detail tables
# the admin chooses from. Every column is chosen to begin with.
#
# A report lists usernames of guardians and admins, never anything about a
# child: children are only counted.

USERS = "users"
PAYMENTS = "payments"
FEEDBACK = "feedback"

REPORT_TYPES = [
    (USERS, "Mga User"),
    (PAYMENTS, "Mga Bayad"),
    (FEEDBACK, "Feedback"),
]

# A report's ID reads RPT-<code>-<day made>-<number>, e.g. RPT-USR-20261026-0007:
# the code of its kind, the day it was made, and its running number.
REPORT_ID_PREFIX = "RPT"
REPORT_CODES = {
    USERS: "USR",
    PAYMENTS: "PAY",
    FEEDBACK: "FBK",
}

CSV = "csv"
PRINTABLE = "printable"

FILE_TYPES = [
    (CSV, "CSV (para sa Excel o Google Sheets)"),
    (PRINTABLE, "Pahinang ipi-print o ise-save bilang PDF"),
]

USER_COLUMNS = [
    ("username", "Username"),
    ("role", "Uri"),
    ("date_joined", "Petsa ng sign-up"),
    ("last_login", "Huling login"),
    ("status", "Status"),
    ("plan", "Plano"),
    ("children", "Bilang ng bata"),
]

PAYMENT_COLUMNS = [
    ("payment_id", "Payment ID"),
    ("date", "Petsa"),
    ("guardian", "Tagapag-alaga"),
    ("plan", "Plano"),
    ("amount", "Halaga"),
    ("status", "Status"),
    ("reviewed_at", "Petsa ng pagsuri"),
    ("reviewed_by", "Sinuri ni"),
    ("period", "Sakop"),
    ("note", "Dahilan ng pagtanggi"),
]

RATING_COLUMNS = [
    ("date", "Petsa"),
    ("username", "Username"),
    ("stars", "Bituin"),
    ("comment", "Komento"),
]

MESSAGE_COLUMNS = [
    ("date", "Petsa"),
    ("username", "Tagapag-alaga"),
    ("message", "Mensahe"),
    ("status", "Status"),
    ("resolved_at", "Petsa ng pag-ayos"),
]
