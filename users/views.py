from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.views.generic import UpdateView
from django.urls import reverse, reverse_lazy


def LogoutView(request):
    logout(request)
    return render(request, 'logout.html')

class ProfileView(UpdateView):
    model = User
    form_class = UserUpdateForm
    second_form_class = ProfileUpdateForm
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        user = User.objects.get(id=self.object.id)
        context['form'] = self.form_class(instance=user)
        context['form2'] = self.second_form_class(instance=user.profile)
        return context

    def get(self, request, *args, **kwargs):
        super(ProfileView, self).get(request, *args, **kwargs)
        form = self.form_class
        form2 = self.second_form_class
        return self.render_to_response(self.get_context_data(
            object=self.object, form=form, form2=form2))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = User.objects.get(id=self.object.id)
        form = self.form_class(request.POST, instance=user)
        form2 = self.second_form_class(request.POST, instance=user.profile)

        if form.is_valid() and form2.is_valid():
            form = form.save(commit=False)
            form.save()
            form2 = form2.save(commit=False)
            form2.user = form 
            form2.save()
            messages.success(self.request, 'Profile updated successfully!')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
              self.get_context_data(form=form, form2=form2))

    def get_success_url(self):
        user = User.objects.get(id=self.object.id)
        if user == self.request.user:
            return reverse('account')
        else:
            return reverse('user-list')