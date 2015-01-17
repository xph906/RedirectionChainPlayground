EMAIL_STRING = "droid000111@gmail.com"
PASSWORD_STRING = "Droid10^"
NAME_STRING = "Droid"
PHONE_STRING = "8474675343"
USERNAME_STRING = "droid000111"
ADDRESS_STRING = "2401 Sheridan Rd"
CITY_STRING = "Evanston"
STATE_STRING = "IL"
ZIPCODE_STRING = "60208"
YEAR_STRING = "2012"
DAY_STRING = "01"
MONTH_STRING = "Jan"
PYEAR_STRING = "1986"
AGE_STRING = "25"

ACCOUNTS = ["gmail", "google", "twitter", "facebook"]


OK_WORDS = ["ok", "done", "agree", "accept", "next", "finish", "submit"]

CANCEL_WORDS = ["cancel", "revert", "discard", "quit", "deny", "reject", "exit"]

BACK_WORDS = ["back"]

LICENSE_WORDS = ["license", "eula", "terms and conditions",
    "terms & conditions"]

ABOUT_WORDS = ["about", "help"]

EMAIL_WORDS = ["email"]
ADDRESS_WORDS = ["address", "street"]
CITY_WORDS = ["city", "location"]
STATE_WORDS = ["state"]
ZIPCODE_WORDS = ["zipcode", "postal code", "zip code", "zip"]
YEAR_WORDS = ["year"]
DAY_WORDS = ["day", "date"]
MONTH_WORDS = ["month"]
AGE_WORDS = ["age"]

PHONE_WORDS = ["phone", "cell"]

PASSWORD_WORDS = ["password"]

USERNAME_WORDS = ["username", "login", "userid"]
PROFILE_WORDS = ["profile", "sign up", "sign in", "login"]

NAME_WORDS = ["name", "lastname", "firstname"]

IGNORE_WORDS = ["zoom", "preferences", "settings", "options", "sign out",
    "signout", "logout", "log out"]

BIRTH_WORDS = ["birth", "born"]

FORBIDDEN_APPS = ["com.android.mms", "com.android.browser",
    "com.android.contacts"]

MAX_LEVELS = 10

# used to count visiting buttons and options in lists
VISITING_THRESHOLD = 6
VISITING_THRESHOLD2 = 5
VISITING_THRESHOLD3 = 6

# the thing below also changed across SDK
LAUNCHER_WIN = 'com.android.launcher/com.android.launcher2.Launcher'
LAUNCHER_PKG = 'com.android.launcher'

RETRIES = 3
PROGRESSBAR_RETRIES = 3

PROGRESSBAR_SLEEP = 2
TIME_NODE_SLEEP = 1.5
INITIAL_SLEEP = 4
REFRESH_SLEEP = 0.15
OPERATE_SLEEP = 0.3


MONKEY_SERVER_PORT = 1080
MONKEY_STDIN_PORT = 1081
VIEW_SERVER_PORT = 4939

SERVICE_CODE_START_VIEW_SERVER = 1
SERVICE_CODE_STOP_VIEW_SERVER = 2
SERVICE_CODE_IS_VIEW_SERVER_RUNNING = 3
