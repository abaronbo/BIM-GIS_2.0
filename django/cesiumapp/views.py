from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def cesium_viewer(request):
    # Check user's groups
    user_groups = list(request.user.groups.values_list('name', flat=True))
    print(f"User: {request.user.username}")
    print(f"Authenticated: {request.user.is_authenticated}")
    print(f"Groups: {user_groups}")

    if 'Contractor' in user_groups:
        template_name = 'cesium.html'
        query_type = 'contractor_query'
    elif 'Municipality' in user_groups:
        template_name = 'municipality_cesium.html'
        query_type = 'municipality_query'
    else:
        print(f"Unauthorized access for user: {request.user.username}")
        return redirect('/')  # Redirect to login instead of 403

    context = {
        'query_type': query_type,
        'user_group': user_groups[0] if user_groups else "Unknown",
    }
    return render(request, template_name, context)
