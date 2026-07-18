from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views import View
from .forms import RegistrationForm, UserUpdateForm, ProfileUpdateForm
from store.models import Order


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('store:home')
        form = RegistrationForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('store:home')
        return render(request, 'accounts/register.html', {'form': form})


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('store:home')
        form = AuthenticationForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'store:home')
            return redirect(next_url)
        return render(request, 'accounts/login.html', {'form': form})


class LogoutView(View):
    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('store:home')


class ProfileView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        return render(request, 'accounts/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'orders': orders,
        })

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('accounts:profile')
        return render(request, 'accounts/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form,
        })
