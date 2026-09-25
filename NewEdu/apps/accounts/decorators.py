from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    """
    Decorator for views that checks whether a user has a particular role,
    requiring login and raising PermissionDenied if they don't.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
        
    def check_role(user):
        if not user.is_authenticated:
            return False
        if user.role in allowed_roles or user.is_superuser:
            return True
        raise PermissionDenied
        
    return user_passes_test(check_role, login_url='/accounts/login/')
