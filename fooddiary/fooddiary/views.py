from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponseNotFound
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer

from .serializers import UserSerializer
from .models import *


class LoginView(APIView):
    permission_classes = (AllowAny, )

    def post(self, request, **kwargs):
        print request.data
        return Response()


class RegistrationView(APIView):
    permission_classes = (AllowAny, )

    def post(self, request, **kwargs):
        serialized = UserSerializer(data=request.data)
        if serialized.is_valid():
            created_user = RegistrationProfile.create_inactive(**request.data)
            return Response(JSONRenderer().render(UserSerializer(created_user).data),
                            status=status.HTTP_201_CREATED)
        else:
            return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)


class ActivationView(APIView):
    permission_classes = (AllowAny, )

    def get(self, request, activation_key):
        if RegistrationProfile.activate_user(activation_key):
            return HttpResponseRedirect(reverse('home'))
        else:
            return HttpResponseNotFound()


def home(request):
    context = {}
    return render(request, "index.html", context)
