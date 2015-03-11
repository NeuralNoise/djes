
DATABASES = {
    "default": {
        "NAME": "default",
        "ENGINE": "django.db.backends.sqlite3"
    }
}

INSTALLED_APPS = (
    "djes",
    "example.app",
)

SECRET_KEY = "vj_+489jz2081l^3gnndu4=#ml_8^@jl6)niifgm@ct!i1#e9r"

MIDDLEWARE_CLASSES = (
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware"
)

ES_INDEX = "djes-example"
ES_INDEX_SETTINGS = {
	"djes-example": {
		"number_of_replicas" : 2
	}
}