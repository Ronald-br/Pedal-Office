
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login


def inicio(request):
    return render(request, 'core/inicio.html')


def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('username')
        senha = request.POST.get('password')

        user = authenticate(request, username=usuario, password=senha)

        if user is not None and user.is_staff:
            auth_login(request, user)
            return redirect('admin:index')

        return render(request, 'core/login.html', {
            'erro': 'Usuário ou senha inválidos, ou acesso não autorizado.'
        })

    return render(request, 'core/login.html')
