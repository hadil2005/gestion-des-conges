from .models import Notification

def notifications_context(request):
    if request.user.is_authenticated:
        employe = getattr(request.user, 'employe', None)
        if employe:
            return {
                'notifications_non_lues': Notification.objects.filter(employe=employe, lu=False).count(),
                'notifications_recentes_header': Notification.objects.filter(employe=employe).order_by('-dateCreation', '-id')[:5],
            }
    return {'notifications_non_lues': 0, 'notifications_recentes_header': []}


def employe_hierarchie(request):
    employe = getattr(request.user, 'employe', None) if request.user.is_authenticated else None
    return {
        'hierarchie': employe.get_hierarchie() if employe else None
    }