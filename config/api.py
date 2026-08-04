from ninja import NinjaAPI
from apps.accounts.api import router as accounts_router
from apps.profiles.api import router as profile_router
from apps.preferences.api import router as partner_preferences_router
from apps.matching.api import router as matching_router
from apps.chat.api import router as chat_router



api = NinjaAPI()

api.add_router("",accounts_router)
api.add_router("", profile_router)
api.add_router("/partner-preferences/",partner_preferences_router)
api.add_router("/matching/", matching_router)
api.add_router("/chat/", chat_router)