from django.contrib.auth import get_user_model, logout, authenticate, login
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from validate_email import validate_email
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from accounts.token import account_activation_token

User = get_user_model()


def register(request):
    if request.method == 'POST':
        context = {'has_error': False, 'data': request.POST}
        first_name = request.POST.get('first_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validation
        if len(password1) < 8:
            messages.add_message(request, messages.ERROR, 'Password should be at least 8 characters')
            context['has_error'] = True

        if password1 != password2:
            messages.add_message(request, messages.ERROR, 'Password mismatch')
            context['has_error'] = True

        if not validate_email(email):
            messages.add_message(request, messages.ERROR, 'Enter a valid email address')
            context['has_error'] = True

        if not first_name:
            messages.add_message(request, messages.ERROR, 'First name is required')
            context['has_error'] = True

        if not username:
            messages.add_message(request, messages.ERROR, 'Username is required')
            context['has_error'] = True

        if User.objects.filter(username=username).exists():
            messages.add_message(request, messages.ERROR, 'Username is taken, choose another one')
            context['has_error'] = True

        if User.objects.filter(email=email).exists():
            messages.add_message(request, messages.ERROR, 'Email is taken, choose another one')
            context['has_error'] = True

        if context['has_error']:
            return render(request, 'account/register.html', context)

        else:
            new_user = User.objects.create_user(username=username, email=email)
            new_user.set_password(password1)
            new_user.first_name = first_name
            new_user.is_active = False  # User must confirm email before being active
            new_user.save()

            # Setting-up email
            current_site = get_current_site(request)
            subject = 'Activate your Account'
            message = render_to_string('account/account_activation_email.html', {
                'user': new_user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
                'token': account_activation_token.make_token(new_user),
            })
            email = EmailMessage(subject, message, to=[new_user.email])
            email.content_subtype = "html"  # Main content is now text/html
            email.send()

            messages.success(request, 'Account creation was successful, confirm your email using the link sent to '
                                      'activate.')
            return redirect('core:home')

    return render(request, 'account/register.html')


def account_activate(request, uidb64, token):
    uid = force_str(urlsafe_base64_decode(uidb64))
    try:
        new_user = User.objects.get(pk=uid)
    except User.DoesNotExist:
        new_user = None

    if new_user is not None and account_activation_token.check_token(new_user, token):
        new_user.is_active = True
        new_user.save()
        login(request, new_user)
        messages.success(request, 'Your account has been activated!')
        return redirect('core:home')
    else:
        return render(request, 'account/activation_invalid.html')


def login_view(request):  # Renamed the function to avoid conflict
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You have been successfully logged in')
            return redirect('core:home')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('accounts:login')

    return render(request, 'account/login.html')


def logout_user(request):
    logout(request)
    return redirect('core:home')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'account/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    token_generator = default_token_generator

    def get_user(self, uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        return user

    def form_valid(self, form):
        user = self.get_user(self.kwargs['uidb64'])
        if user is not None:
            password1 = form.cleaned_data.get('new_password1')
            password2 = form.cleaned_data.get('new_password2')

            if len(password1) < 8:
                messages.error(self.request, 'Password should be at least 8 characters.')
                return self.form_invalid(form)

            user.set_password(password1)
            user.save()
            messages.success(self.request, 'Your password has been set. You may go ahead and log in.')
            return super().form_valid(form)
        else:
            messages.error(self.request, 'The reset link is invalid or has expired.')
            return redirect('accounts:password_reset')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['validlink'] = self.get_user(self.kwargs['uidb64']) is not None
        return context
