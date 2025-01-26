from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.contrib.auth import logout

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('/cesium/')  # All users go to cesium, then routed to the correct page based on group
        return super().get(request, *args, **kwargs)

def logout_view(request):
    logout(request)
    return redirect('/')
