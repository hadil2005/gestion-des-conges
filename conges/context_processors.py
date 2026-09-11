from .models import Notification, DemandeConge


from .models import Notification, DemandeConge


def notifications_context(request):
    if not request.user.is_authenticated:
        return {
            'notifications_non_lues': 0,
            'notifications_recentes_header': [],
            'a_valider_count': 0,
            'mes_demandes_count': 0,
        }

    employe = getattr(request.user, 'employe', None)
    if not employe:
        return {
            'notifications_non_lues': 0,
            'notifications_recentes_header': [],
            'a_valider_count': 0,
            'mes_demandes_count': 0,
        }

    role = employe.get_role()

    validations_count = 0
    if role in ('ES', 'CG', 'CD', 'DIR'):
        demandes = DemandeConge.objects.filter(statue='EN_ATT_VA', niveau_validation=role)
        validations_count = sum(1 for d in demandes if employe.meme_equipe(d.name_employee))

    remplacements_count = DemandeConge.objects.filter(
        name_remplacent=employe, statue='EN_ATT_RMP'
    ).count()

    mes_demandes_count = Notification.objects.filter(employe=employe, type_notif='UPD', lu=False).count()

    return {
        'notifications_non_lues': Notification.objects.filter(employe=employe, lu=False).count(),
        'notifications_recentes_header': Notification.objects.filter(employe=employe).order_by('-dateCreation', '-id')[:5],
        'a_valider_count': validations_count + remplacements_count,
        'mes_demandes_count': mes_demandes_count,
    }

def employe_hierarchie(request):
    employe = getattr(request.user, 'employe', None) if request.user.is_authenticated else None
    return {
        'hierarchie': employe.get_hierarchie() if employe else None
    }