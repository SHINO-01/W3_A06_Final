# properties/context_processors.py

import datetime

def current_year(request):
    return {'current_year': datetime.datetime.now().year}
