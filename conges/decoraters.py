from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages 


def role_required(*allowed_roles): # hed el fonction hiya li tedi the roles name
    def decorator(view_func): # hed el fonction hiya el actual view ou wesh yban for each role
        def wrapper(request, *args, **kwargs): # function hiya li it runs a chaque fois user yvisiti kesh page w tkoun protected by log_required
            # args ou kwargs are parameters just in case for more arguments w kda
            employe= getattr(request.user, 'employe', None)  # hadi get attrubute tae el employe, ida makash don't crash, medli none berk
            # the reason we used getattr psq capable tetcrusha mlwl so haka kayen deja a fail value "none"
            role=employe.get_role() if employe else None # kifkif mdli role we use only if else psq endna deja employe
            if role not in allowed_roles: 
                messages.error(request, "you don't have acces to this page")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator 
